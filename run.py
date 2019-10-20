#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: run.py
# 说   明: 
# 创建时间: 2019/10/20 20:43
'''
import os, json
from httprunner.api import HttpRunner
from lib.processingJson import write_data


data = {
    "config": {
        "base_url": "",
        "name": "性能测试计划",
        "output": [],
        "variables": {}
    },
    "testcases": [
        {
            "teststeps": [
                {
                    "extract": [],
                    "name": "添加发布会接口",
                    "output": [],
                    "request": {
                        "data": {
                            "address": "广西壮族自治区秀英县大兴柳州路a座 764595",
                            "eid": "2947",
                            "limit": "3583",
                            "name": "李凯发布会",
                            "start_time": "2019-10-30 17:03:07",
                            "status": "1"
                        },
                        "headers": {},
                        "method": "post",
                        "params": {},
                        "url": "http://www.easytest.xyz/api/add_event/"
                    },
                    "validate": [
                        {
                            "eq": [
                                "content.message",
                                "add event success"
                            ]
                        }
                    ],
                    "variables": {}
                },
                {
                    "extract": [
                        {
                            "event_id": "content.data.0.id"
                        }
                    ],
                    "name": "查询发布会",
                    "output": [],
                    "request": {
                        "headers": {},
                        "method": "get",
                        "params": {
                            "name": "发布会"
                        },
                        "url": "http://www.easytest.xyz/api/get_event_list"
                    },
                    "validate": [
                        {
                            "eq": [
                                "content.message",
                                "success"
                            ]
                        }
                    ],
                    "variables": {}
                },
                {
                    "extract": [],
                    "name": "添加嘉宾接口",
                    "output": [],
                    "request": {
                        "data": {
                            "eid": "$event_id",
                            "email": "dujing@gmail.com",
                            "phone": "18004323190",
                            "realname": "孙桂芝"
                        },
                        "headers": {},
                        "method": "post",
                        "params": {},
                        "url": "http://www.easytest.xyz/api/add_guest/"
                    },
                    "validate": [
                        {
                            "eq": [
                                "content.message",
                                "add guest success"
                            ]
                        }
                    ],
                    "variables": {}
                }
            ]
        }
    ]
}
# testcase_cli_path = 'D:\HttpRunner_framework\\testsuites\demo_testsuite.json'
# runner = HttpRunner(failfast=True)
# runner.run(data)
# # runner.run('D:\HttpRunnerManager-1\suite\\2019-10-09 13-58-39-702')
# print(runner.summary)

data = {'id': 4220, 'name': '吴玉兰发布会', 'address': '青海省武汉县房山陈路j座 539697', 'status': True, 'limit': 7742, 'start_time': '2019-10-30T17:03:07'}

for i in ['id']:
    print(data[i])