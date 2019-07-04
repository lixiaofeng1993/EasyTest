#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/4 10:04
# @Author  : lixiaofeng
# @Site    : 
# @File    : flowerconfig.py
# @Software: PyCharm

# Broker settings
BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# RabbitMQ management api
broker_api = 'http://guest:guest@localhost:15672/api/'

# Enable debug logging
logging = 'DEBUG'

# 持久模式
persistent = False