# pairing_child : IM920sLグループ番号登録(子機：ノード番号 ≠ 0001h)
# IMBLE2は非対応(不要)
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

def_SET_NODE = b'1234'								# 設定するノード番号 / 0000,0001,FFF0~FFFFは設定不可

keyreq = digitalio.DigitalInOut(board.D4)			# IM920sL再起動トリガ / コネクタ #6(D4)を使用
keyreq.direction = digitalio.Direction.INPUT
keyreq.pull = digitalio.Pull.UP

ib = ipcbox.IPCBox()
time.sleep(0.1)										# IM920sL起動待ち
while ib.get_imbusy():								# BUSY解除までループ
	pass

while not ib.put_line(b'ENWR\r\n'):					# Flash書き込み許可
	pass
while not ib.put_line(b'STNN'+def_SET_NODE+b'\r\n'):# ノード番号設定
	pass
while not ib.put_line(b'STGN\r\n'):					# グループ番号登録開始
	pass

while True:											# 電源Offまで登録待機状態 / 親機の50cm以内に近づけて下さい
	ib.ledg_on()
	time.sleep(0.1)
	ib.ledg_off()
	time.sleep(0.1)
	ib.ledg_on()
	time.sleep(0.1)
	ib.ledg_off()
	time.sleep(0.7)

	s = ib.get_line()								# IM920sLからの受信処理
	if s != None:
		if s == b'GRNOREGD\r\n':						# 登録完了したらLEDを連続点灯に / 完了後はIM920sLを再起動して下さい
			ib.ledg_on()
			while True:
				if keyreq.value == 0:						# ボタンが押された場合はIM920sLを再起動
					ib.imrst_on()								# RESET
					time.sleep(0.01)							# 10ms wait
					ib.imrst_off()								# RESET解除
					ib.ledg_off()
					while True:
						pass