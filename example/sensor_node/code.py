# sensor_node : センサノード
# I2C接続温度湿度センサ(SHT31/Grove Temperature&Humidity Sensor)の値を設定間隔でIM920sLによりブロードキャスト送信
# ※Grove SHT35も同一コードで使用可能です
# SDA = コネクタ1番ピン / SCL = 2番ピン / 内蔵プルアップ抵抗使用
#
# 出力フォーマット:温度(整数部),温度(小数部),湿度(整数部),湿度(小数部) / 小数部は測定値の小数部×256を設定(128=0.5)
# 単位:温度[℃] / 湿度[%]
#
# 送信間隔は5秒+DIP-SW設定値x1秒
# 送信間の待機中はCPU/IM920sL共にスリープ状態に移行
# ※ここではLight Sleep(time.sleep())を使用します
#
# -----------------------------------------------------------------------------------
# Adafruit_CircuitPython_Bundleライブラリのlibフォルダにあるadafruit_sht31d.mpy(又は.py)と
# adafruit_bus_deviceフォルダをCIRCUITPYドライブのlibフォルダにコピーして下さい
#
# ※コピー後は下記の状態になります
# CIRCUITPY---lib\---+---ipcbox.py
#                    +---adafruit_sht31d.mpy
#                    L---adafruit_bus_device\---+---__init.py___
#                                               ・
#                                               ・
#                                               ・
# ライブラリの説明はこちら https://circuitpython.readthedocs.io/projects/bundle/en/latest/index.html
# ライブラリの入手はこちら https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases
# ※-mpy-又は-py-を使用します / mpy版はバイナリ形式の為少し効率が良くなります
#
# 本ソフトウェアは無保証です。
# 本ソフトウェアの不具合により損害が発生した場合でも補償は致しません。
# 改変・流用はご自由にどうぞ。
# Copyright (C)2022 Interplan Co., Ltd. all rights reserved.

import ipcbox
import time
import board
from busio import I2C
import adafruit_sht31d

ib = ipcbox.IPCBox()
ib.i2cpu_on()										# 内蔵I2Cプルアップ抵抗On
i2c = I2C(board.SCL,board.SDA,frequency=100000)		# I2C初期化 / CLK周波数:100kHz

time.sleep(0.1)										# IM920sL起動待ち
while ib.get_imbusy():								# BUSY解除までループ
	pass

while ib.get_blebusy():								# BUSY解除までループ
    pass
ib.ble_sleep()										# IMBLE2は使用しないのでスリープ

ib.ledr_on()
try:
	sht = adafruit_sht31d.SHT31D(i2c)				# センサ初期化 / 未接続時は戻らない or OSError発生
except:
	while True:
		pass
ib.ledr_off()

dsw = ib.get_dsw()									# 送信周期
tsleep = 5 + dsw - 0.1								# LED点灯時間分引く

while True:
	t = sht.temperature								# 温度を取得
	ti = int(t)											# 整数部
	if ti > 255:
		ti = 255
	tf = int((t-ti)*256)								# 小数部
	print('temp:%3.2f'%t)

	h = sht.relative_humidity						# 湿度を取得
	hi = int(h)											# 整数部
	if hi > 255:
		hi = 255
	hf = int((h-hi)*256)								# 小数部
	print('humi:%3.2f'%h)

	m = bytes([ti]) + bytes([tf]) + bytes([hi]) + bytes([hf])
	c = ib.encode_pkt(0,m)							# 送信用コマンドを生成 / ブロードキャスト
	ib.put_line(c)									# IM920sLへコマンド投入

	ib.ledg_on()									# 送信したらLEDを点灯
	time.sleep(0.1)
	ib.ledg_off()

	ib.im_sleep()									# IM920sLをスリープ状態へ
	time.sleep(tsleep)								# CPUをスリープ(Light Sleep)
	ib.im_wakeup()									# IM920sLのスリープを解除