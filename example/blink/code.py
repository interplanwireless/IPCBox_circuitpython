# blink : LEDを1秒周期で点滅
#
# Ver . 0.01    2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
import time

ib = ipcbox.IPCBox()

while True:
	ib.ledg_on()
	ib.ledr_off()
	time.sleep(0.5)
	ib.ledg_off()
	ib.ledr_on()
	time.sleep(0.5)