#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/8/8 16:32
# @Author  : lixiaofeng
# @Site    : 
# @File    : except_check.py
# @Software: PyCharm

from base.models import Project, Sign, Environment, Interface, Case, Plan, Report
from django.contrib.auth.models import User
import logging, re
from lib.error_code import ErrorCode

log = logging.getLogger('log')  # 初始化log


def register_info_logic(username, password, pswd_again, email):
    """
    注册新用户逻辑
    :param username:
    :param password:
    :param pswd_again:
    :param email:
    :return:
    """
    if email:
        if not re.match('.+@.+.com$', email):
            return ErrorCode.format_error
    if username == '' or password == '' or pswd_again == '':
        return ErrorCode.empty_error
    elif len(username) > 50 or len(password) > 50 or len(email) > 50:
        return ErrorCode.fields_too_long_error
    elif 6 > len(username) or 6 > len(password):
        return ErrorCode.not_enough_error
    elif password != pswd_again:
        return ErrorCode.different_error
    else:
        try:
            User.objects.get(username=username)
            return ErrorCode.already_exists_error
        except User.DoesNotExist:
            return 'ok'


def change_info_logic(new_password):
    """
    修改密码逻辑
    :param new_password:
    :return:
    """
    if not new_password:
        return ErrorCode.empty_error
    elif len(new_password) < 6:
        return ErrorCode.not_enough_error
    elif len(new_password) > 50:
        return ErrorCode.fields_too_long_error
    else:
        return 'ok'


def project_info_logic(prj_name, prj_id=''):
    """
    项目新增、编辑逻辑
    :param prj_name:
    :param prj_id:
    :param make:
    :return:
    """
    if prj_name == '':  # 判断输入框
        return '项目名称不能为空！'
    else:
        if not prj_id:
            name_exit = Project.objects.filter(prj_name=prj_name)
        else:
            name_exit = Project.objects.filter(prj_name=prj_name).exclude(prj_id=prj_id)
        if name_exit:
            return '项目: {}，已存在！'.format(prj_name)
        else:
            return 'ok'


def sign_info_logic(sign_name, sign_id=''):
    """
    签名新增、编辑逻辑
    :param sign_name:
    :return:
    """
    if sign_name == '':
        return '签名名称不能为空！'
    if not sign_id:
        name_exit = Sign.objects.filter(sign_name=sign_name)
    else:
        name_exit = Sign.objects.filter(sign_name=sign_name).exclude(sign_id=sign_id)
    if name_exit:
        return '签名: {}，已存在！'.format(sign_name)
    else:
        return 'ok'


def env_info_logic(env_name, url, env_id=''):
    """
    环境新增、编辑逻辑
    :param env_name:
    :param url:
    :param env_id:
    :return:
    """
    if env_name == '':
        return '环境名称不能为空！'
    if url == '':
        return 'url不能为空！'
    att = re.compile('^[\w]{3,5}:\/\/.+')
    math = att.findall(url)
    if not math:
        return 'url不符合规则【^[\w]{3,5}:\/\/.+】，请重新输入！'
    if not env_id:
        name_exit = Environment.objects.filter(env_name=env_name)
    else:
        name_exit = Environment.objects.filter(env_name=env_name).exclude(env_id=env_id)
    if name_exit:
        return '环境: {}，已存在！'.format(env_name)
    else:
        return 'ok'


def interface_info_logic(if_name, url, method, is_sign, data_type, is_headers, request_header_data,
                         request_body_data, response_header_data, response_body_data, if_id=''):
    """
    接口新增、编辑逻辑
    :param if_name:
    :param url:
    :param method:
    :param is_sign:
    :param data_type:
    :param is_headers:
    :param request_header_data:
    :param request_body_data:
    :param response_header_data:
    :param response_body_data:
    :param if_id:
    :return:
    """
    if if_name == '':
        return '接口名称不能为空！'
    if url == '':
        return '接口路径不能为空！'
    att = re.compile('^[\w\{\}\/]+$', re.A)
    math = att.findall(url)
    if not math:
        return '接口路径不符合规则【^[\w\{\}\/]+$】，请重新输入！'
    if method == '':
        return '请选择接口的请求方式！'
    if is_sign == '':
        return '请设置接口是否需要签名！'
    if data_type == '':
        return '请选择接口的请求数据类型！'
    if is_headers == '':
        return '请设置接口是否需要设置请求头！'
    att = re.compile('^\w+$', re.A)
    if request_header_data:
        request_header_data = eval(request_header_data)
        for data in request_header_data:
            math = att.findall(data['var_name'])
            if not math:
                return '请求头中有参数不符合规则【^\w+$】，请重新输入！'
    if request_body_data:
        request_body_data = eval(request_body_data)
        for data in request_body_data:
            math = att.findall(data['var_name'])
            if not math:
                return 'body中有参数不符合规则【^\w+$】，请重新输入！'
    if response_header_data:
        response_header_data = eval(response_header_data)
        for data in response_header_data:
            math = att.findall(data['var_name'])
            if not math:
                return '返回头中有参数不符合规则【^\w+$】，请重新输入！'
    if response_body_data:
        response_body_data = eval(response_body_data)
        for data in response_body_data:
            math = att.findall(data['var_name'])
            if not math:
                return '返回body参数中有参数不符合规则【^\w+$】，请重新输入！'
    if not if_id:
        name_exit = Interface.objects.filter(if_name=if_name)
    else:
        name_exit = Interface.objects.filter(if_name=if_name).exclude(if_id=if_id)
    if name_exit:
        return '接口: {}，已存在！'.format(if_name)
    else:
        return 'ok'


def format_params(params):
    """
    格式化参数
    :param params:
    :return:
    """
    if params.method == 'get':
        method = 0
    elif params.method == 'post':
        method = 1
    elif params.method == 'delete':
        method = 2
    elif params.method == 'put':
        method = 3
    else:
        method = ''
    if params.is_sign == 0:
        is_sign = 0
    elif params.is_sign == 1:
        is_sign = 1
    else:
        is_sign = ''
    if params.is_header == 0:
        is_headers = 0
    elif params.is_header == 1:
        is_headers = 1
    else:
        is_headers = ''
    return method, is_sign, is_headers


def case_info_logic(case_name, content, case_id=''):
    """
    用例新增、编辑逻辑
    :return:
    """
    if case_name == '':
        return '用例名称不能为空！'
    if content == '[]':
        return '请输入接口参数信息！'
    contents = eval(content)
    att = re.compile('^\w+$', re.A)
    for param in contents:
        for key in param['header']:
            math = att.findall(key)
            if not math:
                return '请求头中有参数不符合规则【^\w+$】，请重新输入！'
        for key in param['body']:
            math = att.findall(key)
            if not math:
                return 'body中有参数不符合规则【^\w+$】，请重新输入！'
    if not case_id:
        name_exit = Case.objects.filter(case_name=case_name)
    else:
        name_exit = Case.objects.filter(case_name=case_name).exclude(case_id=case_id)
    if name_exit:
        return '用例：{}， 已存在！'.format(case_name)
    else:
        return 'ok'


def plan_info_logic(plan_name, content, plan_id=''):
    """
    计划新增、编辑逻辑
    :return:
    """
    if plan_name == '':
        return '计划名称不能为空！'
    if content == []:
        return '请选择用例编号！'
    if not plan_id:
        name_exit = Plan.objects.filter(plan_name=plan_name)
    else:
        name_exit = Plan.objects.filter(plan_name=plan_name).exclude(plan_id=plan_id)
    if name_exit:
        return '计划: {}，已存在！'.format(plan_name)
    else:
        return 'ok'


"""请求接口异常处理"""


def env_not_exit(case_run):
    log.error('用例 {} 未设置运行环境！'.format(case_run['case_id']))
    case_run['msg'] = '用例 {} 未设置运行环境，请前往【测试环境】页面添加.'.format(case_run['case_id'])
    case_run['error'] = ErrorCode.env_not_exit_error
    return case_run


def case_is_delete(case_run):
    log.error('用例 {} 已被删除！'.format(case_run['case_id']))
    case_run['msg'] = '用例 {} 可能已被删除，请返回【用例管理】页面核实.'.format(case_run['case_id'])
    case_run['error'] = ErrorCode.case_not_exit_error
    return case_run


def interface_is_delete(case_run, case_name, if_name):
    log.error('用例 {} 中的接口 {} 已被删除！'.format(case_name, if_name))
    case_run['msg'] = '用例 {} 中的接口 {} 可能已被删除，请前往【接口管理】页面核实.'.format(case_name, if_name)
    case_run['error'] = ErrorCode.interface_not_exit_error
    return case_run


def parametric_set_error(if_dict):
    if_dict["result"] = "error"
    if_dict["checkpoint"] = ''
    if_dict["res_content"] = '参数化设置错误，请检查是否符合平台参数化规则！'
    if_dict['error'] = ErrorCode.random_params_error
    if_dict['msg'] = ErrorCode.random_params_error
    return if_dict


def AES_length_error(if_dict):
    if_dict["result"] = "error"
    if_dict["checkpoint"] = ''
    if_dict["res_content"] = 'AES算法app_key设置长度错误，请前往【测试环境】页面核实 密钥 是否符合规则.'
    if_dict['error'] = ErrorCode.AES_key_length_error
    if_dict['msg'] = ErrorCode.AES_key_length_error
    return if_dict


def response_value_error(if_dict, e):
    if_dict["result"] = "error"
    if_dict["checkpoint"] = ''
    if_dict["res_content"] = '解析接口返回值出错，请核实原因.  详细报错信息： {}'.format(e)
    if_dict['error'] = ErrorCode.analytical_return_value_error
    if_dict['msg'] = ErrorCode.analytical_return_value_error
    return if_dict


def request_api_error(if_dict, e):
    if_dict["result"] = "error"
    if_dict["checkpoint"] = ''
    if_dict["res_content"] = '接口请求出错，请核实原因.  详细报错信息： {}'.format(e)
    if_dict['error'] = ErrorCode.requests_error
    if_dict["msg"] = ErrorCode.requests_error
    return if_dict


def index_error(if_dict):
    if_dict["result"] = "error"
    if_dict["checkpoint"] = ''
    if_dict["error"] = ErrorCode.index_error
    if_dict["msg"] = ErrorCode.index_error
    return if_dict


def checkpoint_no_error(if_dict):
    if_dict["result"] = 'fail'
    if_dict['checkpoint'] = ''
    if_dict["msg"] = ErrorCode.validators_error
    if_dict["error"] = ErrorCode.validators_error
    return if_dict
