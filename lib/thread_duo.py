#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/14 13:11
# @Author  : lixiaofeng
# @Site    : 
# @File    : thread_duo.py
# @Software: PyCharm

# coding=utf-8
# coding=utf-8
import threading
import time

def chiHuoGuo(people):
    print("%s 吃火锅的小伙伴-羊肉：%s" % (time.ctime(),people))
    time.sleep(1)
    print("%s 吃火锅的小伙伴-鱼丸：%s" % (time.ctime(),people))


class myThread (threading.Thread):   # 继承父类threading.Thread
    def __init__(self, people, name):
        '''重写threading.Thread初始化内容'''
        threading.Thread.__init__(self)
        self.threadName = name
        self.people = people

    def run(self):   # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        '''重写run方法'''
        print("开始线程: " + self.threadName)

        chiHuoGuo(self.people)     # 执行任务
        print("qq交流群：226296743")
        print("结束线程: " + self.name)


# 创建新线程
thread1 = myThread("xiaoming", "Thread-1")
thread2 = myThread("xiaowang", "Thread-2")


# 开启线程
thread1.start()
thread2.start()

time.sleep(0.5)
print("退出主线程")