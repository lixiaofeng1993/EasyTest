#!/usr/bin/python
# coding:utf-8
import sys

__author__ = 'wsy'

from base.models import Project, Sign, Environment, Interface, Case, Plan, Report
from django.contrib.auth.models import User  # django自带user
import requests
# import hashlib
import re, os, datetime
from django.db.models import Sum
import json
from lib.signtype import user_sign_api, encryptAES
import logging
import time
from lib.public import validators_result, get_extract, get_param, replace_var, \
    extract_variables, call_interface, format_url

# from common.connectMySql import SqL

log = logging.getLogger('log')
i = 0
j = 0


class Test_execute():
    def __init__(self, case_id, env_id, case_id_list):
        self.case_id = case_id
        self.env_id = env_id
        self.case_id_list = case_id_list
        self.begin_time = time.clock()
        self.prj_id, self.env_url, self.private_key = self.get_env(self.env_id)
        self.sign_type = self.get_sign(self.prj_id)
        self.s = requests.session()
        # self.extract_dict = {}
        self.extract_list = []
        self.glo_var = {}
        self.step_json = []
        # self.sql = SqL(job=True)

    def __del__(self):
        global j
        j = 0

    def test_case(self):
        """接口测试用例"""
        try:
            case = Case.objects.get(case_id=self.case_id)
        except Case.DoesNotExist as e:
            log.error('用例 {} 已被删除！'.format(self.case_id))
            return '用例 {} 已被删除！'.format(self.case_id)
        self.step_list = eval(case.content)
        case_run = {"case_id": self.case_id, "case_name": case.case_name}
        case_step_list = []
        for step in self.step_list:
            step_info = self.step(step)
            if isinstance(step_info, dict):
                case_step_list.append(step_info)
                if step_info["result"] == "fail":
                    case_run["result"] = "fail"
                    # break
                if step_info["result"] == "error":
                    case_run["result"] = "error"
                    # break
            else:
                return {'error': '用例 {} 中的接口 {} 已被删除！'.format(case.case_name, step["if_name"])}
        class_name = self.__class__.__name__
        func_name = sys._getframe().f_code.co_name
        method_doc = self.test_case.__doc__
        case_run["step_list"], case_run['class_name'], case_run[
            'func_name'], case_run['method_doc'] = case_step_list, class_name, func_name, method_doc
        log.info('interface response data: {}'.format(case_run))
        return case_run

    def step(self, step_content):
        if_id = step_content["if_id"]
        try:
            interface = Interface.objects.get(if_id=if_id)
        except Interface.DoesNotExist as e:
            return
        var_list = extract_variables(step_content)
        # 检查是否存在变量
        if var_list:
            for var_name in var_list:
                var_value = get_param(var_name, step_content)
                if var_value is None:
                    var_value = get_param(var_name, self.step_json)
                if var_value is None:
                    for extract_dict in self.extract_list:  # 把变量替换为提取的参数
                        if var_name in extract_dict.keys():
                            var_value = extract_dict[var_name]
                step_content = json.loads(replace_var(step_content, var_name, var_value))
        if_dict = {"url": interface.url, "header": step_content["header"], "body": step_content["body"]}
        set_headers = Environment.objects.get(env_id=self.env_id).set_headers
        if set_headers:
            make = False
            headers = eval(set_headers)['header']
            for k, v in headers.items():
                if k and v:
                    if '$' not in v:
                        make = True
            if make:
                if_dict['header'] = headers
        if interface.data_type == 'sql':
            for k, v in if_dict['body'].items():
                if 'select' in v:
                    if_dict['body'][k] = self.sql.execute_sql(v)
        # 签名
        if interface.is_sign:
            if self.sign_type == 1:  # md5加密
                if_dict["body"] = user_sign_api(if_dict["body"], self.private_key)
            elif self.sign_type == 2:  # 不签名
                pass
            elif self.sign_type == 3:  # 用户认证
                pass
            elif self.sign_type == 4:  # AES算法加密
                if_dict["body"] = encryptAES(json.dumps(if_dict['body']).encode('utf-8'),
                                             self.private_key.encode('utf-8')).decode('utf-8')
        else:
            if 'true' in step_content['body']:
                if_dict["body"] = True
            elif 'false' in step_content['body']:
                if_dict['body'] = False
        if '[' in json.dumps(if_dict["body"]):  # body参数是list的情况
            for k, v in if_dict['body'].items():
                if_dict["body"][k] = eval(v)
        if_dict["url"] = self.env_url + interface.url
        if_dict["url"], if_dict["body"] = format_url(if_dict["url"], if_dict["body"])
        if interface.data_type == 'file':
            if_dict["body"] = {
                "file": ("login-bg.jpg", open("/var/static/static/img/login-bg.jpg", "rb"), "image/jpeg", {})}
        if_dict["if_id"] = if_id
        if_dict["if_name"] = step_content["if_name"]
        if_dict["method"] = interface.method
        if_dict["data_type"] = interface.data_type
        try:
            # if self.sign_type == 4:
            if interface.is_sign:
                if self.sign_type == 4:
                    res = call_interface(self.s, if_dict["method"], if_dict["url"], if_dict["header"],
                                         {'data': if_dict["body"]}, if_dict["data_type"])
            else:
                res = call_interface(self.s, if_dict["method"], if_dict["url"], if_dict["header"],
                                     if_dict["body"], if_dict["data_type"])
            if_dict["res_status_code"] = res.status_code
            # if_dict["res_content"] = res.text
            if_dict["res_content"] = eval(
                res.text.replace('false', 'False').replace('null', 'None').replace('true', 'True'))  # 查看报告时转码错误的问题
            for key, value in if_dict['res_content'].items():
                if value == '系统异常':
                    if_dict['res_content'][key] = 'interface_error'
            if interface.is_header:  # 补充默认headers中的变量
                set_headers = Environment.objects.get(env_id=self.env_id).set_headers
                headers = eval(set_headers)['header']
                if headers:
                    for k, v in headers.items():
                        if k == 'token':
                            if if_dict["res_content"]['data'] == 'interface_error':
                                headers[k] = ''
                            else:
                                headers[k] = if_dict["res_content"]['data']
                            now_time = datetime.datetime.now()
                            Environment.objects.filter(env_id=self.env_id).update(set_headers={'header': headers},
                                                                                  update_time=now_time)
        except requests.RequestException as e:
            if_dict["result"] = "Error"
            if_dict["msg"] = str(e)
            return if_dict

        if step_content["extract"]:
            extract_dict = get_extract(step_content["extract"], if_dict["res_content"],
                                       interface.url)  # 从有提取参数的接口中把参数抓出来
            self.extract_list.append(extract_dict)
        if step_content["validators"]:
            if_dict["result"], if_dict["msg"], if_dict['checkpoint'] = validators_result(step_content["validators"],
                                                                                         if_dict["res_content"])
            if 'error' in if_dict['result']:
                if_dict['result'] = 'error'
            elif 'fail' in if_dict['result']:
                if_dict['result'] = 'fail'
            else:
                if_dict['result'] = 'pass'
        else:
            if_dict["result"] = "pass"
            if_dict["msg"] = {}
        if interface.data_type == 'file':
            if_dict["body"] = {'file': '上传图片'}
        end_time = time.clock()
        interface_totalTime = str(end_time - self.begin_time)[:6] + ' s'
        if_dict['interface_totalTime'] = interface_totalTime
        return if_dict

    # 获取测试环境
    def get_env(self, env_id):
        env = Environment.objects.get(env_id=env_id)
        prj_id = env.project.prj_id
        return prj_id, env.url, env.private_key

    # 获取签名方式
    def get_sign(self, prj_id):
        """
        sign_type: 签名方式
        """
        prj = Project.objects.get(prj_id=prj_id)
        sign_type = prj.sign.sign_id
        return sign_type


def get_user(user_id):
    '''判断用户是否存在'''
    if not user_id:
        return False
    else:
        try:
            user = User.objects.get(id=user_id)
            return user.username
        except User.DoesNotExist:
            return False


def get_total_values():
    total = {
        'pass': [],
        'fail': [],
        'percent': []
    }
    today = datetime.date.today()
    for i in range(-11, 1):
        begin = today + datetime.timedelta(days=i)
        end = begin + datetime.timedelta(days=1)

        total_pass = Report.objects.filter(update_time__range=(begin, end)).aggregate(pass_num=Sum('pass_num'))[
            'pass_num']
        total_fail = Report.objects.filter(update_time__range=(begin, end)).aggregate(fail_num=Sum('fail_num'))[
            'fail_num']
        if not total_pass:
            total_pass = 0
        if not total_fail:
            total_fail = 0

        total_percent = round(total_pass / (total_pass + total_fail) * 100, 2) if (
                                                                                      total_pass + total_fail) != 0 else 0.00
        total['pass'].append(total_pass)
        total['fail'].append(total_fail)
        total['percent'].append(total_percent)

    return total
