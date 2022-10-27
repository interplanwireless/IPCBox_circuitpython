# serial : 外部シリアルポート有効化
# IB-DUAL外部接続用のシリアルポートを初期化する
#
# I2C/SPI/UART使用時は初期化順に制限あり
# 下記の順番で設定すること
# 1)IU920を初期化
# 2)UART(A0/A1)を初期化
# 3)SPI(又はUART2)(D2～5)を初期化
# 4)I2C(又はUART3)(D0/1)を初期化
# ※IU920以外は使用しない物は省略可
#
# Ver . 0.01    2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
import board
import digitalio
from busio import UART,SPI,I2C

ib = ipcbox.IPCBox()

com = UART(board.TX,board.RX)

cs = digitalio.DigitalInOut(board.D2)       # CSpin (D2)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True
spi = SPI(board.SCK,board.MOSI,board.MISO)
# com2 = UART(board.D2,board.D3)

ib.i2cpu_on()                               # I2C pull-up
i2c = I2C(board.SCL,board.SDA)
# com3 = UART(board.D0,board.D1)

while True:
	pass