# !/usr/bin/env python
# coding=utf-8
# from django.conf import settings
from django.conf.urls import url
# from django.conf.urls.static import static
# from django.views.generic.base import RedirectView
from . import views

app_name = "base"
urlpatterns = [
    # 项目
    url(r'project/', view=views.ProjectIndex.as_view(), name='project'),
    url(r'project_add/', view=views.project_add, name='project_add'),
    url(r'project_update/', view=views.project_update, name='project_update'),
    url(r'project_delete/', view=views.project_delete, name='project_delete'),
    # 签名
    url(r'sign/', view=views.SignIndex.as_view(), name='sign'),
    url(r'sign_add/', view=views.sign_add, name='sign_add'),
    url(r'sign_update/', view=views.sign_update, name='sign_update'),
    url(r'sign_delete/', view=views.sign_delete, name='sign_delete'),
    # 测试环境
    url(r'env/', view=views.EnvIndex.as_view(), name='env'),
    url(r'env_add/', view=views.env_add, name='env_add'),
    url(r'env_update/', view=views.env_update, name='env_update'),
    url(r'env_delete/', view=views.env_delete, name='env_delete'),
    url(r'set_headers/', view=views.set_headers, name='set_headers'),
    # 接口
    url(r'interface/', view=views.InterfaceIndex.as_view(), name='interface'),
    url(r'interface_add/', view=views.interface_add, name='interface_add'),
    url(r'interface_update/', view=views.interface_update, name='interface_update'),
    url(r'interface_delete/', view=views.interface_delete, name='interface_delete'),
    url(r'interface_search/', view=views.interface_search, name='interface_search'),
    url(r'interface_copy/', view=views.interface_copy, name='interface_copy'),
    url(r'set_mock/', view=views.set_mock, name='set_mock'),
    # 用例
    url(r'case/', view=views.CaseIndex.as_view(), name='case'),
    url(r'case_add/', view=views.case_add, name='case_add'),
    url(r'case_update/', view=views.case_update, name='case_update'),
    url(r'case_delete/', view=views.case_delete, name='case_delete'),
    url(r'case_run/', view=views.case_run, name='case_run'),
    url(r'case_logs/', view=views.case_logs, name='case_logs'),
    url(r'case_copy/', view=views.case_copy, name='case_copy'),
    url(r'case_search/', view=views.case_search, name='case_search'),
    # 测试计划
    url(r'plan/', view=views.PlanIndex.as_view(), name='plan'),
    url(r'plan_add/', view=views.plan_add, name='plan_add'),
    url(r'plan_update/', view=views.plan_update, name='plan_update'),
    url(r'plan_delete/', view=views.plan_delete, name='plan_delete'),
    url(r'plan_run/', view=views.plan_run, name='plan_run'),
    # 报告
    url(r'^report/', view=views.report_index, name='report'),
    url(r'report_search/', view=views.report_search, name='report_search'),
    # 异步请求获取数据
    url(r'findata/', view=views.findata, name='findata'),
    # 批量导入
    url(r'batch_index', view=views.batch_index, name='batch_index'),
    # 定时任务
    url(r'timing_task/', view=views.timing_task, name='timing_task'),
    url(r'task_logs/', view=views.task_logs, name='task_logs'),
    # 报告页面展示
    url(r'report_page/', view=views.ReportPage.as_view(), name='report_page'),
    url(r'report_logs/', view=views.report_logs, name='report_logs'),  # 日志
    url(r'report_delete/', view=views.report_delete, name='report_delete'),
    # locust
    url(r'performance/', view=views.performance_index, name='performance'),
    url(r'start_locust/', view=views.start_locust, name='start_locust'),
    url(r'performance_report/', view=views.performance_report, name='performance_report'),
    url(r'performance_real/', view=views.performance_real, name='performance_real'),
    url(r'performance_history/', view=views.performance_history, name='performance_history'),
    url(r'performance_delete/', view=views.performance_delete, name='performance_delete'),
    # 下载
    url(r'file_download/', view=views.file_download, name='file_download'),
    # 添加用户
    url(r'user/', view=views.UserIndex.as_view(), name='user'),
    # 关于我们
    url(r'about/', view=views.about_index, name='about'),
    url(r'document/', view=views.document, name='document'),
]
