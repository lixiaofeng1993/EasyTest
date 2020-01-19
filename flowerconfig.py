#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/4 10:04
# @Author  : lixiaofeng
# @Site    : 
# @File    : flowerconfig.py
# @Software: PyCharm

# Broker settings
BROKER_URL = 'amqp:redis://127.0.0.1:6379/0'

# RabbitMQ management api
broker_api = 'http://guest:guest@39.105.136.231:15672/api/'

# Enable debug logging
logging = 'INFO'

# 持久模式
persistent = True

# 最大
max_tasks = 100
