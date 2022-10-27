# deep_sleep : 
# CPU及びIM920sL/IMBLE2を20秒周期でスリープさせます(10秒スリープ->10秒wake-up)
# Deep Sleepを使用します / スリープ解除後は再起動 = コード先頭から実行します
# ※起動時に環境初期化処理で1秒程度待機時間があります(この間は電流が多くなります)
# ※スリープ後短時間でwake-upする場合はLight Sleepの方が全体の消費電力が小さくなる場合があります
#
# 下記のコードでのスリープ時消費電流はサンプルによる実測で50μAです。(参考値です/環境により変動します)
#
# Ver . 0.01    2022/10/01 test version
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
import time
import alarm

ib = ipcbox.IPCBox()

ib.ledg_on()
t = int(time.monotonic())							# 秒単位の現在時刻
ts = t
while t < (ts+10):									# 10秒間wake-up状態で待機
	t = int(time.monotonic())

ib.ledg_off()
ib.im_sleep()										# IM920sLをスリープ状態へ
ib.ble_sleep()										# IMBLE2をスリープ状態へ
talm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 10)	# 10秒間Deep Sleep
alarm.exit_and_deep_sleep_until_alarms(talm)