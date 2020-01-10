#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/9 13:53
# @Author  : lixiaofeng
# @Site    : 
# @File    : random_params.py
# @Software: PyCharm
from faker import Faker
from datetime import datetime
import re, random

faker = Faker('zh_CN')


def fake_params(params, value, key='', i=0):
    """
    支持对body中存在的嵌套参数进行参数化
    :param params: 参数字典
    :param value: 包含参数化关键字的值
    :param key: 字典的key，区分dict、list
    :param i: list参数包含关键字的位置
    :return:
    """
    if isinstance(value, str):
        if '__random_int' in value:
            regexp = r"\((.+)\)"
            num = re.findall(regexp, value)
            str_value = value.split('__random_int')[0]
            if num:
                try:
                    k = int(num[0].split(',')[0])
                    v = int(num[0].split(',')[1])
                    if key:
                        params[key] = str_value + str(random.randint(k, v))
                    else:
                        params.remove(value)
                        params.insert(i, str_value + str(random.randint(k, v)))
                except ValueError:
                    return 'error'
            else:
                params[key] = random.randint(1, 10000)
        elif '__name' in value:
            str_value = value.split('__name')[0]
            str_value1 = value.split('__name')[1]
            str_name = faker.name()
            if key:
                params[key] = str_value + str_name + str_value1
            else:
                params.remove(value)
                params.insert(i, str_value + str_name + str_value1)
        elif '__address' in value:
            str_value = value.split('__address')[0]
            str_value1 = value.split('__address')[1]
            str_address = faker.address()
            if key:
                params[key] = str_value + str_address + str_value1
            else:
                params.remove(value)
                params.insert(i, str_value + str_address + str_value1)
        elif '__phone' in value:
            str_value = value.split('__phone')[0]
            str_value1 = value.split('__phone')[1]
            str_phone = faker.phone_number()
            if key:
                params[key] = str_value + str_phone + str_value1
            else:
                params.remove(value)
                params.insert(i, str_value + str_phone + str_value1)
        elif '__text' in value:
            regexp = r"\((.+)\)"
            num = re.findall(regexp, value)
            str_value = value.split('__text')[0]
            str_value1 = value.split('__text')[1]
            if num:
                try:
                    number = int(num[0])
                    if key:
                        params[key] = str_value + faker.text(max_nb_chars=number).replace('\n', '').replace('\r', '')
                    else:
                        params.remove(value)
                        params.insert(i,
                                      str_value + faker.text(max_nb_chars=number).replace('\n', '').replace('\r', ''))
                except ValueError:
                    return 'error'
            else:
                if key:
                    params[key] = str_value + faker.text().replace('\n', '').replace('\r', '') + str_value1
                else:
                    params.remove(value)
                    params.insert(i, str_value + faker.text().replace('\n', '').replace('\r', '') + str_value1)
        elif '__random_time' in value:
            regexp = r"\((.+)\)"
            tag = re.findall(regexp, value)
            str_value = value.split('__random_time')[0]
            str_value1 = value.split('__random_time')[1]
            str_random_time = faker.date_time()
            if tag:
                if tag[0].lower() == 'd':
                    if key:
                        params[key] = str_value + str(str_random_time)[:10]
                    else:
                        params.remove(value)
                        params.insert(i, str_value + str(str_random_time)[:10])
                else:
                    if key:
                        params[key] = str_value + str(str_random_time)
                    else:
                        params.remove(value)
                        params.insert(i, str_value + str(str_random_time))
            else:
                if key:
                    params[key] = str_value + str(str_random_time) + str_value1
                else:
                    params.remove(value)
                    params.insert(i, str_value + str(str_random_time) + str_value1)
        elif '__now' in value:
            regexp = r"\((.+)\)"
            tag = re.findall(regexp, value)
            str_value = value.split('__now')[0]
            str_value1 = value.split('__now')[1]
            str_random_time = datetime.now()
            if tag:
                if tag[0].lower() == 'd':
                    if key:
                        params[key] = str_value + str(str_random_time)[:10]
                    else:
                        params.remove(value)
                        params.insert(i, str_value + str(str_random_time)[:10])
                else:
                    if key:
                        params[key] = str_value + str(str_random_time)[:-7]
                    else:
                        params.remove(value)
                        params.insert(i, str_value + str(str_random_time)[:-7])
            else:
                if key:
                    params[key] = str_value + str(str_random_time)[:-7] + str_value1
                else:
                    params.remove(value)
                    params.insert(i, str_value + str(str_random_time)[:-7] + str_value1)
        elif '__email' in value:
            str_value = value.split('__email')[0]
            str_value1 = value.split('__email')[1]
            str_email = faker.email()
            if key:
                params[key] = str_value + str_email + str_value1
            else:
                params.remove(value)
                params.insert(i, str_value + str_email + str_value1)
    return params


def random_params(params):
    """
    参数化
    :param params:
    :return:
    """
    if isinstance(params, dict):  # params是字典，包含字典或者列表
        for key, value in params.items():
            if isinstance(value, (dict, list)):
                random_params(value)
            elif isinstance(value, str):
                fake_params(params, value, key)
                # for k, v in value.items():
                #     fake_params(value, v, k)
                # elif isinstance(value, list):
                # value.sort()
                # for i in range(len(value)):
                #     fake_params(value, value[i], i=i)
                # else:
                #     fake_params(params, value, key)
    elif isinstance(params, list):  # params是列表，包含字典
        for i in range(len(params)):
            if isinstance(params[i], (dict, list)):
                random_params(params[i])
            elif isinstance(params[i], str):
                fake_params(params, params[i])
                # if isinstance(params[i], dict):
                #     for k, v in params[i].items():
                #         fake_params(params[i], v, k)
    return params
