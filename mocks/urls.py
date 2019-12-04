#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/10/14 17:30
# @Author  : lixiaofeng
# @Site    : 
# @File    : urls.py
# @Software: PyCharm

from django.conf.urls import url
# from django.conf.urls.static import static
# from django.views.generic.base import RedirectView
from . import views

app_name = "mocks"
urlpatterns = [
    # 项目
    url(r'api/?', view=views.mock_api, name='mock_api'),
    url(r'[\w|\/]+', view=views.dispatch_request, name='dispatch_request'),

]
