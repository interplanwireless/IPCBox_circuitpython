# pairing_parent : IM920sLグループ番号登録(子機：ノード番号 ≠ 0001h)
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

# IM920sLグループ番号登録(親機:ノード番号 = 0001h)
# IMBLE2は非対応(不要)
ib = ipcbox.IPCBox()
time.sleep(0.1)										# IM920sL起動待ち
while ib.get_imbusy():								# BUSY解除までループ
	pass

while not ib.put_line(b'ENWR\r\n'):					# Flash書き込み許可
	pass
while not ib.put_line(b'STNN0001\r\n'):				# ノード番号 = 0001h
	pass
while not ib.put_line(b'STGN\r\n'):					# グループ番号登録開始
	pass

while True:											# 電源Offまで登録パケットを自動で送信
	ib.ledg_on()
	time.sleep(0.1)
	ib.ledg_off()
	time.sleep(0.4)