#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/7/23 16:09
# @Author  : lixiaofeng
# @Site    : 
# @File    : urls.py
# @Software: PyCharm

# coding=utf-8
from django.conf.urls import url
from . import views_api, views_api_sec, views

app_name = "guest"
urlpatterns = [
    # web
    url(r'^index_guest/$', view=views.index, name='index_guest'),  # 登录页面
    url(r'^login_action_guest/$', view=views.login_action, name='login_action_guest'),  # 登录出错跳转
    url(r'^event_manage/$', view=views.event_manage, name='event_manage'),  # 发布会管理
    url(r'^accounts/login/$', view=views.index),  # 验证用户是否登录，未登录跳转到登录页
    url(r'^search_name/$', view=views.search_name, name='search_name'),  # 发布会搜索
    url(r'^guest_manage/$', view=views.guest_manage, name='guest_manage'),  # 嘉宾管理
    url(r'^search_guest/$', view=views.search_guest, name='search_guest'),  # 嘉宾搜索
    url(r'^sign_index/(?P<eid>\d+)/$', view=views.sign_index, name='sign_index'),  # 签到 eid 作为参数传给视图
    url(r'^sign_index_action/(?P<eid>\d+)/$', view=views.sign_index_action, name='sign_index_action'),  # 处理签到操作
    url(r'^logout_guest/$', view=views.logout, name='logout_guest'),  # 退出
    url(r'^delete_all/$', view=views.delete_all, name='delete_all'),  # 清空数据

    # api
    url(r'^add_event/$', view=views_api.add_event, name='add_event'),  # 添加发布会接口
    url(r'^update_event/$', view=views_api.update_event, name='update_event'),  # 修改发布会接口
    url(r'^get_event_list/$', view=views_api.get_event_list, name='get_event_list'),  # 查询发布会接口
    url(r'^add_guest/$', view=views_api.add_guest, name='add_guest'),  # 添加嘉宾接口
    url(r'^get_guest_list/$', view=views_api.get_guest_list, name='get_guest_list'),  # 查询嘉宾接口
    url(r'^user_sign/$', view=views_api.user_sign, name='user_sign'),  # 嘉宾签到接口
    url(r'^login/$', view=views_api.login, name='login'),  # 嘉宾签到接口

    # 加密api
    url(r'^sec_add_event/', view=views_api_sec.sec_add_event, name='sec_add_event'),  # 添加发布会加密接口
    url(r'^sec_get_event_list/', view=views_api_sec.sec_get_event_list, name='sec_get_event_list'),  # 查询发布会加密接口
    url(r'^sec_get_guest_list/', view=views_api_sec.sec_get_guest_list, name='sec_get_guest_list'),  # 查询嘉宾接口

]
