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


def random_params(params):
    """
    参数化
    :param params:
    :return:
    """
    if isinstance(params, dict):
        for key, value in params.items():
            if '__random_int' in value:
                regexp = r"\((.+)\)"
                num = re.findall(regexp, value)
                str_value = value.split('__random_int')[0]
                if num:
                    try:
                        k = int(num[0].split(',')[0])
                        v = int(num[0].split(',')[1])
                        params[key] = str_value + str(random.randint(k, v))
                    except ValueError:
                        return 'error'
                else:
                    return 'error'
            elif '__name' in value:
                str_value = value.split('__name')[0]
                str_value1 = value.split('__name')[1]
                str_name = faker.name()
                params[key] = str_value + str_name + str_value1
            elif '__address' in value:
                str_value = value.split('__address')[0]
                str_value1 = value.split('__address')[1]
                str_address = faker.address()
                params[key] = str_value + str_address + str_value1
            elif '__phone' in value:
                str_value = value.split('__phone')[0]
                str_value1 = value.split('__phone')[1]
                str_phone = faker.phone_number()
                params[key] = str_value + str_phone + str_value1
            elif '__text' in value:
                regexp = r"\((.+)\)"
                num = re.findall(regexp, value)
                str_value = value.split('__text')[0]
                if num:
                    try:
                        number = int(num[0])
                        params[key] = str_value + faker.text(max_nb_chars=number)
                    except ValueError:
                        return 'error'
                else:
                    params[key] = str_value + faker.text()
            elif '__random_time' in value:
                str_value = value.split('__random_time')[0]
                str_value1 = value.split('__random_time')[1]
                str_random_time = faker.date_time()
                params[key] = str_value + str(str_random_time) + str_value1
            elif '__now' in value:
                str_value = value.split('__now')[0]
                str_value1 = value.split('__now')[1]
                str_random_time = datetime.now()
                params[key] = str_value + str(str_random_time)[:-7] + str_value1
            elif '__email' in value:
                str_value = value.split('__email')[0]
                str_value1 = value.split('__email')[1]
                str_email = faker.email()
                params[key] = str_value + str_email + str_value1
        return params