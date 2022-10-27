# i2c_scan : I2C スキャン
# SDA = コネクタ1番ピン / SCL = 2番ピン / 内蔵プルアップ抵抗使用
# 1秒毎にI2Cバスをスキャンし応答があったアドレスを表示します
#
# Ver . 0.01    2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
import board
import time
from busio import I2C

ib = ipcbox.IPCBox()

ib.i2cpu_on()										# 内蔵I2Cプルアップ抵抗On
i2c = I2C(board.SCL,board.SDA,frequency=100000)		# I2C初期化 / CLK周波数:100kHz
while not i2c.try_lock():							# スキャンの為にI2Cバスをロック
	pass

while True:
	l = i2c.scan()									# スキャン実行
	cnt = len(l)
	if cnt == 0:									# 何も応答が無い場合
		print('--')
	else:											# 応答があった場合
		for i in range(cnt):
			print('%02X'%l[i])
	time.sleep(1)