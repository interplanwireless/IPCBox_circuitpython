# -*- coding: utf-8 -*-
#
# IB-DUAL用内蔵I/Oドライバ / for CircuitPython 7.1.0
#
# Ver. 0.01 2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import time
import board
import binascii
import digitalio
from busio import UART


def_IB_LIBVER = b"01.00"		# Lib Ver
def_IB_IMTXD = board.IM_TXD		# CPU -> IM920sL
def_IB_IMRXD = board.IM_RXD		# CPU <- IM920sL
def_IB_IMBUSY = board.IM_BUSY
def_IB_IMRST = board.IM_RST

def_IB_BLETXD = board.BLE_TXD	# CPU -> IMBLE2
def_IB_BLERXD = board.BLE_RXD	# CPU <- IMBLE2
def_IB_BLEBUSY = board.BLE_BUSY
def_IB_BLERST = board.BLE_RST
def_IB_BLEIRQ = board.BLE_IRQ

def_IB_LEDG = board.LEDG
def_IB_LEDR = board.LEDR
def_IB_DSW0 = board.DSW0
def_IB_DSW1 = board.DSW1
def_IB_DSW2 = board.DSW2
def_IB_DSW3 = board.DSW3
def_IB_I2CPU = board.I2C_PUEN


class IPCBox:
	"""IB-DUALのI/O制御クラス"""

# 初期化
	def __init__(self):
		"""各I/Oの初期化

		IM920sL 起動 / IMBLE2 起動 / LED緑&赤 Off(消灯) / I2C-Pull Off /
		"""
																# IM920sL I/F
		self.imrxd = digitalio.DigitalInOut(def_IB_IMRXD)			# UART RxD (CPU <- IM920sL) / スリープ制御用に仮初期化
		self.imrxd.direction = digitalio.Direction.INPUT
		self.imrxd.pull = digitalio.Pull.UP

		self.imbusy = digitalio.DigitalInOut(def_IB_IMBUSY)			# BUSY
		self.imbusy.direction = digitalio.Direction.INPUT
		self.imbusy.pull = digitalio.Pull.UP

		self.imrst = digitalio.DigitalInOut(def_IB_IMRST)			# RESET / 最初はリセット状態
		self.imrst.direction = digitalio.Direction.OUTPUT
		self.imrst_on()

		time.sleep(0.1)												# 100ms間リセット保持
		self.imrst_off()											# リセット解除
		self.comrdy = False
		self.start_uart()											# UART初期化

																# IMBLE2 I/F
		self.blerxd = digitalio.DigitalInOut(def_IB_BLERXD)			# UART RxD (CPU <- IMBLE) / スリープ制御用に仮初期化
		self.blerxd.direction = digitalio.Direction.INPUT
		self.blerxd.pull = digitalio.Pull.UP

		self.blebusy = digitalio.DigitalInOut(def_IB_BLEBUSY)		# BUSY
		self.blebusy.direction = digitalio.Direction.INPUT
		self.blebusy.pull = digitalio.Pull.UP

		self.blerst = digitalio.DigitalInOut(def_IB_BLERST)			# RESET / 最初はリセット状態
		self.blerst.direction = digitalio.Direction.OUTPUT
		self.blerst_on()

		time.sleep(0.1)												# 100ms間リセット保持
		self.blerst_off()											# リセット解除
		self.comrdyb = False
		self.start_uartb()											# UART初期化

																# その他内蔵I/O
		self.ledg = digitalio.DigitalInOut(def_IB_LEDG)				# LED(緑) / 最初は消灯
		self.ledg.direction = digitalio.Direction.OUTPUT
		self.ledg_off()

		self.ledr = digitalio.DigitalInOut(def_IB_LEDR)				# LED(赤) / 最初は消灯
		self.ledr.direction = digitalio.Direction.OUTPUT
		self.ledg_off()

		self.dsw0 = digitalio.DigitalInOut(def_IB_DSW0)				# DIP-SW
		self.dsw0.direction = digitalio.Direction.INPUT
		self.dsw0.pull = digitalio.Pull.UP

		self.dsw1 = digitalio.DigitalInOut(def_IB_DSW1)
		self.dsw1.direction = digitalio.Direction.INPUT
		self.dsw1.pull = digitalio.Pull.UP

		self.dsw2 = digitalio.DigitalInOut(def_IB_DSW2)
		self.dsw2.direction = digitalio.Direction.INPUT
		self.dsw2.pull = digitalio.Pull.UP

		self.dsw3 = digitalio.DigitalInOut(def_IB_DSW3)
		self.dsw3.direction = digitalio.Direction.INPUT
		self.dsw3.pull = digitalio.Pull.UP

		self.i2cpu = digitalio.DigitalInOut(def_IB_I2CPU)			#I2C pull-up制御 / 最初はOff / 負論理
		self.i2cpu.direction = digitalio.Direction.OUTPUT
		self.i2cpu_off()

																# 変数類設定
		self.imrxbuf = b''
		self.blerxbuf = b''


# IMパケット処理
	def encode_pkt(self,node:int,msg:bytearray|bytes) -> bytearray:
		"""1パケット組み立て

		IMシリーズ指定のノード宛にデータを送信する為のコマンドを生成する
		
		宛先 = 0の場合はブロードキャスト用コマンド(TXDA) / その他はユニキャスト用コマンド(TXDU)を生成
		
		※IMBLE2の場合は宛先 = 0のみ使用可
		:param int node: 宛先ノード番号 / ブロードキャスト時は0を指定
		:param bytearray or bytes msg: 送信するデータ / 最大32byte
		:return: 生成したコマンド行を返す
		:rtype: bytearray"""

		m = binascii.hexlify(msg)					# ペイロードをHEXに変換
		if node == 0:
			s = b'TXDA' + m + b'\r\n'
		else:
			s = b'TXDU' + b'%04X,'%node + m + b'\r\n'
		return bytearray(s)


	def decode_pkt(self,rxmsg:bytearray) -> tuple:
		"""受信パケット解析

		IMシリーズの受信パケットを要素に分解する

		宛先 = 0の場合はブロードキャスト用コマンド(TXDA) / その他はユニキャスト用コマンド(TXDU)を生成
		:param bytearray rxmsg: UART受信データ(1行分, CRLFを含む)
		:return node: 送信元ノード番号 / 受信パケット以外はNone
		:return rssi: 受信RSSI値 / 受信パケット以外又はNone
		:return payload: 受信データ / 受信パケット以外はNone
		:return mi: 受信msgID / Miが無い場合はNone / 必要に応じて戻り値に追加してください
		:return rt: 受信Route / Rtが無い場合は[] / 必要に応じて戻り値に追加してください
		:rtype: int,int,bytearray,int,list"""

		msglen = len(rxmsg)
		res = (None,None,None)
		#res = (None,None,None,None,None)

		if self.chk_rfdata(rxmsg):
			if rxmsg[2] == 0x2C:		# 2Byte目が,の場合はMiなし
				mi = None
				ni = 3
			else:						# Miあり
				mi = int.from_bytes(binascii.unhexlify(rxmsg[:4]),'big')	
				ni = 8
			nn = int.from_bytes(binascii.unhexlify(rxmsg[ni:ni+4]),'big')
			rxmsg = rxmsg[ni+5:]		# 必要ない部分は消去
			rt = []
			idx = 0
			rssi = 0
			for i in range(len(rxmsg)):	# RSSIとルート取得
				if rxmsg[i] == 0x3A:		# RSSI保存
					rssi = int.from_bytes(binascii.unhexlify(rxmsg[i-2:i]),'big')
					idx = i + 1
					break
				elif rxmsg[i] == 0x2C:		# ルート保存(EORT設定時のみ)
					rt.append(int.from_bytes(binascii.unhexlify(rxmsg[i-4:i]),'big'))
					msglen -= 5

			payload = bytearray((msglen-12)//3)
			j = 0						# payloadをASCIIに変換して保存する
			for i in range(idx,msglen-3,3):
				try:
					payload[j] = int.from_bytes(binascii.unhexlify(rxmsg[i:i+2]),'big')
					j += 1
				except:
					break

			res = (nn,rssi,payload)
			#res = (nn,rssi,payload,mi,rt)	# Mi,Rtも使用する場合
		return res


	def put_char(self,ch:bytes) -> None:
		"""1文字送信

		入力データをIM920sLへ1文字送信する / BUSYチェックしない
		:param bytes ch: 送信する文字
		:retype: None"""
		self.imcom.write(ch)


	def put_line(self,buf:bytes|bytearray) -> bool:
		"""1行送信

		入力データをそのままIM920sLへUART 1行送信する

		主にパケット送信以外のコマンド入力時に使用
		:param bytes or bytearray buf: 送信するデータ
		:return: BUSY = Highの場合 又は タイムアウト等でIM920sLへのコマンド入力に失敗した場合はFalseを返す
		:rtype: bool"""
		if buf[0] == ord('?'):	                # 先頭が？ならBUSYを無視して送信
			self.put_char(b'?')
			if len(buf) <= 1:                       # ?だけなら終了
				return True
			buf = buf[1:]							# 残りを送信する
			time.sleep(0.01)
                
		if self.imbusy.value == 1:				# BUSYの場合はエラー終了
			return False
		else:
			if isinstance(buf, bytes):
				buf = bytearray(buf)
			r = self.imcom.write(buf)
			if r == 0 or r == None:
				return False
			else:
				return True


	def get_line(self) -> (bytearray|None):
		"""1行受信

		IM920sLのUART出力を行末(=CR+LFまで)1行受信する

		※ 通常は(受信パケット解析処理)を使用する
		:return: 受信結果を1個のbytearrayとして返す / データが何も無い場合はNoneを返す
		:rtype: bytearray or None"""
		if self.imcom.in_waiting == 0:			# 受信データが無い場合は何もせず終了
			return None
		else:
			s = self.imcom.readline()
			line = None
			if not s:
				return None
			else:									# ゴミデータ出力防止
				line = self.get_dispchar(s)

			if line:								# データ追加
				self.imrxbuf = self.imrxbuf + line
			else:
				return None

			if self.imrxbuf[-1] == 0x0a:			# '\n' : 行末まで受信できたら・・・
				line = self.imrxbuf						# 受信文字列を返す
				self.imrxbuf = b''						# 次に備えてバッファはクリア
				return bytearray(line)
			else:
				return None


	def kbhit(self) -> bool:
		"""UART受信データ有無チェック

		※ True時も行末まで受信できていない場合がある為注意
		:return: IM920sLからの受信データが1文字以上ある場合はTrueを返す
		:rtype: bool"""
		if self.imcom.in_waiting != 0:
			return True
		else:
			return False



	def im_sleep(self) -> None:
		"""スリープ開始
		
		IM920sLをスリープ状態に移行しUARTを停止
		:return: None"""
		while not self.put_line(b'DSRX\r\n'):		# スリープ開始
			pass
		time.sleep(0.01)							# 送出完了待ち
		self.stop_uart()							# UART停止



	def im_wakeup(self) -> None:
		"""スリープ解除
		
		UARTを再スタートしIM920sLをスリープ解除
		:return: None"""
		self.start_uart()							# UART再スタート
		self.put_char(b'?')							# wake-upトリガ / これは一時wake-upの為続けてENRXが必要
		while self.get_imbusy():						# BUSY解除(=コマンド受付可)待ち
			pass
		while not self.put_line(b'ENRX\r\n'):		# スリープ解除
			pass



	def get_imbusy(self) -> bool:
		"""BUSY状態取得
		:return: BUSY = High(=コマンド投入不可)の場合はTrueを返す
		:rtype: bool"""
		return self.imbusy.value


	def imrst_on(self) -> None:
		"""RESET On 出力
		:return: None"""
		self.imrst.value = False	# 負論理


	def imrst_off(self) -> None:
		"""RESET Off 出力
		:return: None"""
		self.imrst.value = True		# 負論理


	def put_charb(self,ch:bytes) -> None:
		"""1文字送信(IMBLE2)

		入力データをIMBLE2へ1文字送信する / BUSYチェックしない
		:param bytes ch: 送信する文字
		:retype: None"""
		self.blecom.write(ch)


	def put_lineb(self,buf:bytes|bytearray) -> bool:
		"""1行送信(IMBLE2)

		入力データをそのままIM920sLへUART 1行送信する

		主にパケット送信以外のコマンド入力時に使用
		:param bytes or bytearray buf: 送信するデータ
		:return: BUSY = Highの場合 又は タイムアウト等でIM920sLへのコマンド入力に失敗した場合はFalseを返す
		:rtype: bool"""
		if len(buf)>=2 and buf[0]==ord('?'):	# 先頭が？ならBUSYを無視して送信
			self.put_charb(b'?')
			buf = buf[1:]							# 残りを送信する
			time.sleep(0.01)

		if self.blebusy.value == 1:				# BUSYの場合はエラー終了
			return False
		else:
			if isinstance(buf, bytes):
				buf = bytearray(buf)
			r = self.blecom.write(buf)
			if r == 0 or r == None:
				return False
			else:
				return True


	def get_lineb(self) -> (bytearray|None):
		"""1行受信

		IMBLE2のUART出力を行末(=CR+LFまで)1行受信する

		※ 通常は(受信パケット解析処理)を使用する
		:return: 受信結果を1個のbytearrayとして返す / データが何も無い場合はNoneを返す
		:rtype: bytearray or None"""

		if self.blecom.in_waiting == 0:			# 受信データが無い場合は何もせず終了
			return None
		else:
			s = self.blecom.readline()
			line = None
			if not s:
				return None
			else:									# ゴミデータ出力防止
				line = self.get_dispchar(s)

			if line:								# データ追加		
				self.blerxbuf = self.blerxbuf + line
			else:
				return None

			if self.blerxbuf[-1] == 0x0a:			# '\n' : 行末まで受信できたら・・・
				line = self.blerxbuf						# 受信文字列を返す
				self.blerxbuf = b''						# 次に備えてバッファはクリア
				return bytearray(line)
			else:
				return None


	def kbhitb(self) -> bool:
		"""UART受信データ有無チェック(IMBLE2)

		※ True時も行末まで受信できていない場合がある為注意
		:return: IMBLE2からの受信データが1文字以上ある場合はTrueを返す
		:rtype: bool"""
		if self.blecom.in_waiting != 0:
			return True
		return False


	def ble_sleep(self) -> None:
		"""スリープ開始(IMBLE2)
		
		IMBLE2をスリープ状態に移行しUARTを停止"""
		while not self.put_lineb(b'DSRX\r\n'):		# スリープ開始
			pass
		time.sleep(0.01)
		self.stop_uartb()							# UART停止


	def ble_wakeup(self) -> None:
		"""スリープ解除(IMBLE2)
		
		UARTを再スタートしIIMBLE2をスリープ解除"""
		self.start_uartb()							
		self.put_charb(b'?')						# wake-upトリガ / これは一時wake-upの為続けてENRXが必要
		while self.get_blebusy():					# BUSY解除(=コマンド受付可)待ち
			pass
		while not self.put_lineb(b'ENRX\r\n'):		# スリープ解除
			self.get_lineb()
			pass


	def get_blebusy(self) -> bool:
		"""BUSY状態取得(IMBLE2)
		:return: BUSY = High(=コマンド投入不可)の場合はTrueを返す
		:rtype: bool"""
		return self.blebusy.value


	def blerst_on(self) -> None:
		"""RESET On 出力(IMBLE2)"""
		self.blerst.value = False	# 負論理


	def blerst_off(self) -> None:
		"""RESET Off 出力(IMBLE2)"""
		self.blerst.value = True	# 負論理


# その他I/O制御
	def ledg_on(self) -> None:
		"""LED(緑) 点灯"""
		self.ledg.value = True


	def ledg_off(self) -> None:
		"""LED(緑) 消灯"""
		self.ledg.value = False


	def ledr_on(self) -> None:
		"""LED(赤) 点灯"""
		self.ledr.value = True


	def ledr_off(self) -> None:
		"""LED(赤) 消灯"""
		self.ledr.value = False


	def i2cpu_on(self) -> None:
		"""I2C pull-up On"""
		self.i2cpu.value = False	# 負論理


	def i2cpu_off(self) -> None:
		"""I2C pull-up Off"""
		self.i2cpu.value = True		# 負論理


	def get_dsw(self) -> int:
		"""DIP-SW 状態取得
		:return: DIP-SWの状態を4bitの数値(0～F)として返す
		:rtype: int"""
		res = 0
		if self.dsw0.value == 0:
			res = res + 1
		if self.dsw1.value == 0:
			res = res + 2
		if self.dsw2.value == 0:
			res = res + 4
		if self.dsw3.value == 0:
			res = res + 8
		return res


# 補助関数
	def start_uart(self) -> None:
		"""UART初期化(IM920sL)"""
		if not self.comrdy:
			self.imrxd.deinit()
			self.imcom = UART(def_IB_IMTXD, def_IB_IMRXD, baudrate=19200, timeout=0, receiver_buffer_size=256)
			self.comrdy = True


	def stop_uart(self) -> None:
		"""UART停止(IM920sL)"""
		if self.comrdy:
			self.imcom.deinit()
			self.imrxd = digitalio.DigitalInOut(def_IB_IMRXD)		# スリープ中はRxDをIN/Pull-upに設定 / TxDはモジュール側のpull-upで対応
			self.imrxd.direction = digitalio.Direction.INPUT
			self.imrxd.pull = digitalio.Pull.UP
			self.comrdy = False


	def start_uartb(self) -> None:
		"""UART初期化(IMBLE2)"""
		if not self.comrdyb:
			self.blerxd.deinit()
			self.blecom = UART(def_IB_BLETXD, def_IB_BLERXD, baudrate=19200, timeout=0, receiver_buffer_size=256)
			self.comrdyb = True


	def stop_uartb(self) -> None:
		"""UART停止(IMBLE2)"""
		if self.comrdyb:
			self.blecom.deinit()
			self.blerxd = digitalio.DigitalInOut(def_IB_BLERXD)	# スリープ中はRxDをIN/Pull-upに設定 / TxDはモジュール側のpull-upで対応
			self.blerxd.direction = digitalio.Direction.INPUT
			self.blerxd.pull = digitalio.Pull.UP
			self.comrdyb = False


	def ledg_init(self) -> None:
		"""LED(緑)初期化"""
		self.ledg = digitalio.DigitalInOut(def_IB_LEDG)			# LED(緑)
		self.ledg.direction = digitalio.Direction.OUTPUT


	def ledr_init(self) -> None:
		"""LED(赤)初期化"""
		self.ledr = digitalio.DigitalInOut(def_IB_LEDR)			# LED(赤)
		self.ledr.direction = digitalio.Direction.OUTPUT


	def get_dispchar(self, data:bytes) -> bytes:
		"""表示可能文字だけを抽出する
		:param bytes data: UARTで受信したデータ文字列
		:return: 受信したデータの内の表示可能文字列
		:rtype: bytes"""
		res = b''
		if not len(data):	# データ長が0ならデータ無し
			return res
		else:
			for dt in data:		# 表示可能文字だけ保存する
				dt = chr(dt).encode()	
				if dt==b'\r' or dt==b'\n' or (b' '<=dt and dt<=b'~'):
					res += dt

		return res


	def chk_rfdata(self, rxmsg:bytearray) -> bool:
		"""受信データがRFパケットか確認する
		:param bytearray rxmsg: UART受信データ(1行分, CRLFを含む)
		:return: True=RF受信データ / False=その他
		:rtype: bool"""
		if b':' in rxmsg:				# :があり、
			idx = rxmsg.index(b':')
			header = rxmsg[:idx]            
			headlen = len(header)           # :までの長さが
			if headlen >= 10:				# 10以上で
				if (header[2]==0x2C or header[4]==0x2C) and header[idx-3]==0x2C:	# ','が指定の位置にあるなら・・・
					return True                     # RFパケット
		
		return False