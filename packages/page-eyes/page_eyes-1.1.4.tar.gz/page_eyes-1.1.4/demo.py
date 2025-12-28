#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : aidenmo
# @Email : aidenmo@tencent.com
# @Time : 2025/11/19 12:05

from adbutils import AdbDevice, AdbClient
client = AdbClient()
adb = AdbDevice(client, serial="10.91.145.33:53226")
adb.sync.push("demo.py", "/data/local/tmp")
print("push success", adb.info)
print(adb.sync.exists("/data/local/tmp/demo.py"))