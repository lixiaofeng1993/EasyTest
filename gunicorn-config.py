# !/usr/bin/env python
# coding=utf-8
from multiprocessing import cpu_count

bind = '127.0.0.1:9000'
daemon = True   # 守护进程

workers = cpu_count() * 2
worker_class = 'gevent'
forwarded_allow_ips = '*'

# 维持TCP链接
keepalive = 6
timeout = 65
graceful_timeout = 10
worker_connections = 65535

# log
capture_output = True
loglevel = 'info'
accesslog = "/tmp/EasyTest_access.log"    #访问日志文件的路径
errorlog = "/tmp/EasyTest_error.log"
