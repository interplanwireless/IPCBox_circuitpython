# transparent : IM920sLコンソール入力をパケット送信 / 受信パケットをコンソール出力
# コネクタ6番ピン(D4)～GND間にトリガ用押しボタンSWを接続
# IMBLE2も同手順で送信可(node=0のみ対応)
# ローカルエコー=Off / 送信改行コード=CRのみ
#
# Ver . 0.01    2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
import time
import board
import digitalio

ib = ipcbox.IPCBox()
keyreq = digitalio.DigitalInOut(board.D4)			# キー入力トリガ / コネクタ #6(D4)を使用
keyreq.direction = digitalio.Direction.INPUT
keyreq.pull = digitalio.Pull.UP

while ib.get_imbusy():								# IM920sL起動待ち / BUSY解除までループ
	pass
													# IM920sLパラメータ設定 (IMBLEは不要)
while not ib.put_line(b'STRT1\r\n'):					# 通信モード:高速
	pass
while not ib.put_line(b'STCH01\r\n'):					# 通信ch:01
	pass
while not ib.put_line(b'STPO2\r\n'):					# 送信電力:10mW
	pass
while not ib.put_line(b'STTR03\r\n'):					# キャリアセンスリトライ:3回
	pass
while not ib.put_line(b'RDNN\r\n'):                     # 確認のためノード番号を出力
    pass


while True:
	if keyreq.value == 0:							# ボタンが押された場合は・・・
		n = int(input('node >'))						# キー入力待ち / 宛先ノード番号
		s = input('data >')								# キー入力待ち / ペイロード
		c = ib.encode_pkt(n,s.encode())				# 送信用コマンドを生成
		ib.put_line(c)									# IM920sLへコマンド投入

		while keyreq.value == 0:						# チャタリングキャンセル処理
			pass
		time.sleep(0.1)			

	s = ib.get_line()								# IM920sLからの受信処理
	if s != None:									# データがあった場合は・・・
		n,r,m = ib.decode_pkt(s)						# パケット解析して表示
		if n != None:									# 受信パケットの場合は要素毎
			print('node:%04X, rssi:%03d, data:%s'%(n,r,m.decode()))
		else:											# 受信パケット以外はCR+LFだけ削除
			print(s[:-2].decode())