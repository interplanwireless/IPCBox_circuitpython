# setting : コンソール <-> IM920sL/IMBLE通信
# ターミナルソフトを使用する場合は、
# 改行コードはCRのみ、ローカルエコー無しとして下さい
#
# Ver . 0.01    2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
from supervisor import runtime

def_SET_MODULE = 1      # 0=IM920SL, 1=IMBLE2
ib = ipcbox.IPCBox()

while True:
    if runtime.serial_bytes_available:              # USBから入力されたら
        s = input()								        # 入力待ち / Enterで入力完了
        if def_SET_MODULE == 0:
            ib.put_line((s+'\r\n').encode())			    # bytesに変換してIM920sLへ送信 / CR+LF付加要
        else:
            ib.put_lineb((s+'\r\n').encode())			    # bytesに変換してIMBLEへ送信 / CR+LF付加要	

    if def_SET_MODULE == 0:                         # IM920sLからの受信処理
        s = ib.get_line()                               # 1行受信
        if s != None:                                   # データがあればstrに変換して表示
            print(s[:-2].decode())
    else:
        s = ib.get_lineb()								# IMBLEからの受信処理
        if s != None:									# データがあればstrに変換して表示
            print(s[:-2].decode())