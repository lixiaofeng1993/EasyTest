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

from django.contrib.auth.models import User
from base.models import Event, Guest
from rest_framework import routers, serializers, viewsets
from django.conf.urls import include

from rest_framework.schemas import get_schema_view
from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer


# Serializers define the API representation.
# class UserSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = User
#         fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
# class UserViewSet(viewsets.ModelViewSet):
#     '''
#            retrieve:
#                Return a user instance.
#
#            list:
#                Return all users,ordered by most recent joined.
#
#            create:
#                Create a new user.
#
#            delete:
#                Remove a existing user.
#
#            partial_update:
#                Update one or more fields on a existing user.
#
#            update:
#                Update a user.
#        '''
    # queryset = User.objects.all()
    # serializer_class = UserSerializer


class EventSerializer(serializers.ModelSerializer):
    # guests = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Event
        fields = '__all__'


# ViewSets define the view behavior.
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class GuestSerializer(serializers.ModelSerializer):
    event = EventSerializer(many=False, read_only=True)

    # event = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Guest
        fields = '__all__'
        exclude = []


# ViewSets define the view behavior.
class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)
router.register(r'events', EventViewSet)
router.register(r'guests', GuestViewSet)

schema_view = get_schema_view(title='EasyTest 测试接口', renderer_classes=[OpenAPIRenderer, SwaggerUIRenderer], url='http://www.easytest.xyz')

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

    # api
    url(r'^add_event/$', view=views_api.add_event, name='add_event'),  # 添加发布会接口
    url(r'^get_event_list/$', view=views_api.get_event_list, name='get_event_list'),  # 查询发布会接口
    url(r'^add_guest/$', view=views_api.add_guest, name='add_guest'),  # 添加嘉宾接口
    url(r'^get_guest_list/$', view=views_api.get_guest_list, name='get_guest_list'),  # 查询嘉宾接口
    url(r'^user_sign/$', view=views_api.user_sign, name='user_sign'),  # 嘉宾签到接口

    # 加密api
    url(r'^sec_add_event/', view=views_api_sec.sec_add_event, name='sec_add_event'),  # 添加发布会加密接口
    url(r'^sec_get_event_list/', view=views_api_sec.sec_get_event_list, name='sec_get_event_list'),  # 查询发布会加密接口
    url(r'^sec_get_guest_list/', view=views_api_sec.sec_get_guest_list, name='sec_get_guest_list'),  # 查询嘉宾接口

    url(r'^docs/$', schema_view, name='docs'),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
