#!/user/bin/env python

# coding=utf-8



import hashlib

import hmac

import random

import string

import time

from datetime import datetime

from faker import Faker





SECRET_KEY = "DebugTalk"







def gen_random_string(str_len):

    random_char_list = []

    for _ in range(str_len):

        random_char = random.choice(string.ascii_letters + string.digits)

        random_char_list.append(random_char)



    random_string = ''.join(random_char_list)

    return random_string





def get_sign(*args):

    content = ''.join(args).encode('ascii')

    sign_key = SECRET_KEY.encode('ascii')

    sign = hmac.new(sign_key, content, hashlib.sha1).hexdigest()

    return sign





def get_random_name():

    fake = Faker("zh_CN")

    return fake.name()





def get_random_text(num=""):

    fake = Faker("zh_CN")

    if str(num).isdigit():

        return fake.text(num)

    else:

        return fake.text()





def get_random_address():

    fake = Faker("zh_CN")

    return fake.address()





def get_random_int(x=0, y=0):

    if y == 0:

        return random.randint(1, 10000)

    else:

        return random.randint(x, y)



def get_random_num_list():

    num_list = []

    for i in range(4):

        num_list.append(random.randint(1000, 10000))

    return num_list



def get_now_time():
    
    time_format = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    
    return time_format



def get_random_time():

    fake = Faker("zh_CN")

    return fake.date_time()



def get_randon_phone():

    fake = Faker("zh_CN")

    return fake.phone_number()





def get_random_email():

    fake = Faker("zh_CN")

    return fake.email()


def list_p():
    return ["10000", "20000"]
    
    
def list_w():
    return ["1", "2"]


def get_account(num):
    accounts = []
    for index in range(1, num+1):
        accounts.append(
            {"username": "user%s" % index, "password": str(index) * 6},
        )

    return accounts
