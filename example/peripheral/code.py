# peripheral : IB-DUALの搭載機能制御
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
sts = True
while True:
    dsw = ib.get_dsw()  # DIP-SW 状態取得 (SW201)
    print("DSW = 0x%X" %dsw)

    if sts:             # LED制御
        ib.ledg_on()        # 緑LED On(D200)
        ib.ledr_off()       # 赤LED Off(D201)
        print("LEDR On")
        print("LEDG Off")
    else:               # LED制御
        ib.ledg_on()        # 緑LED Off(D200)
        ib.ledr_off()       # 赤LED On(D201)
        print("LEDR Off")
        print("LEDG On")
        
    if sts:             # D0(SDA)/D1(SCL) I2C Pull-up On
        ib.i2cpu_on()
        print("I2C Pull-up On")
    else:
        ib.i2cpu_off()
        print("I2C Pull-up Off")
    
    sts = not sts
    time.sleep(3)