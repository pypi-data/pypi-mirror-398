#
# Copyright 2020, Xiaomi.
# All rights reserved.
# Author: huyumei@xiaomi.com
# 
 
import socket

host = 'cnbj4-talos.api.xiaomi.net'
port = 80
source_address = None
timeout = 5

res = socket.create_connection((host, port), timeout)
test = 1
