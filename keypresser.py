# -*- coding: utf-8 -*-
import ctypes
import asyncio


tasks = {}
runtasks = 0

def keypress_convert(key,waitsecond,KEYDICT):

    global runtasks
    if runtasks <= 2:
        print("現在入力中のボタンは3以下でした。")
        if key in tasks:
            print (key)
            if not tasks[key].done():
                tasks[key].cancel()
                runtasks -= 1
                print("tasks[key].cancel()発動、入力中 = " + str(runtasks))
        print ("key_press_async侵入直前")
        task = asyncio.ensure_future(key_press_async(key, waitsecond))
        print("キーボードの"+ str(key) + "ボタンが、" + str(waitsecond) + "秒押されます。")
        tasks[key] = task
    else:
        print("ボタンが3つ入力中なので入力をキャンセルしました。" + str(runtasks))

async def key_press_async(key, waitsecond):
    global runtasks
    print ("key_press関数に侵入")
    runtasks += 1
    ctypes.windll.user32.keybd_event(key, 0, 0, 0)  # Aを押す
    print ("key押下開始、runtasks = " + str(runtasks))
    await asyncio.sleep(waitsecond)
    print ("await asyncio.sleep(10)終了")
    ctypes.windll.user32.keybd_event(key, 0, 0x2, 0)  # Aを離す
    runtasks -= 1
    print ("key押下終了、runtasks = " + str(runtasks))
        