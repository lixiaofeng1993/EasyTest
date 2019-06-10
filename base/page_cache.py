# !/usr/bin/env python
# coding=utf-8
from django.core.cache import cache
from django.conf import settings
from redis import Redis

r = Redis(**settings.REDIS)


def page_cache(timeout):
    def wrap1(view_func):  # page_cache装饰器
        def wrap2(request, *args, **kwargs):
            key = 'Response-{}'.format(request.get_full_path())  # 拼接唯一的key
            response = cache.get(key)  # 从缓存中获取数据
            print('从缓存中获取数据:{}'.format(response))
            if response is None:
                # 获取数据库中的数据,在添加到缓存中
                response = view_func(request, *args, **kwargs)
                cache.set(key, response, timeout)
                print('从数据库中获取:{}'.format(response))
            return response

        return wrap2

    return wrap1
