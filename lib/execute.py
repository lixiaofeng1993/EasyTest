#!/usr/bin/python
# coding:utf-8
import sys

__author__ = 'wsy'

from base.models import Project, Sign, Environment, Interface, Case, Plan, Report
from django.contrib.auth.models import User  # django自带user
import requests, re, os, datetime, json, logging, time
from django.conf import settings
from django.db.models import Sum
from lib.signtype import user_sign_api, encryptAES, auth_user
from lib.public import validators_result, get_extract, get_param, replace_var, \
    extract_variables, call_interface, format_url, format_body, http_random, str_number
from lib.random_params import random_params
from lib.except_check import env_not_exit, case_is_delete, interface_is_delete, parametric_set_error, AES_length_error, \
    response_value_error, request_api_error, index_error, checkpoint_no_error, eval_set_error, sql_query_error
from httprunner.api import HttpRunner
from lib.httprunner_execute import HttpRunerMain

# from lib.processingJson import write_data

# from lib.connectMySql import SqL

log = logging.getLogger('log')


class Test_execute():
    def __init__(self, env_id, case_id_list, run_mode='0', plan='', case_id=0, locust=False):
        self.case_id = case_id
        self.env_id = env_id
        self.locust = locust
        self.case_id_list = case_id_list
        self.begin_time = time.clock()
        self.s = requests.session()
        self.extract_list = []
        self.glo_var = {}
        self.run_mode = run_mode
        self.plan = plan
        self.step_json = []
        self.user_auth = ""  # 用户认证
        self.headers = {}  # 未设置默认header的情况
        # self.sql = SqL(job=True)

    @property
    def test_case(self):
        """接口测试用例"""
        class_name = self.__class__.__name__
        func_name = sys._getframe().f_code.co_name
        # method_doc = self.test_case.__doc__
        method_doc = "接口测试用例"
        case_run = {'class_name': class_name, 'func_name': func_name, 'method_doc': method_doc}

        if self.get_env(self.env_id):  # 获取测试环境数据
            self.prj_id, self.env_url, self.private_key = self.get_env(self.env_id)
        else:
            case_run = env_not_exit(case_run)  # 异常情况
            return case_run
        self.sign_type = self.get_sign(self.prj_id)  # 获取签名数据

        case_step_list = []
        if self.run_mode == '1':
            for case_id in self.case_id_list:
                try:
                    case = Case.objects.get(case_id=case_id)
                    case_run.update(
                        {"case_name": case.case_name, "case_id": case.case_id, "project_id": case.project_id,
                         "weight": case.weight})
                    if self.plan:
                        case_run.update({"plan_name": self.plan.plan_name})
                except Case.DoesNotExist as e:
                    case_run = case_is_delete(case_run, e, case_id)
                    return case_run
                self.step_list = eval(case.content)
                for step in self.step_list:
                    step_info = self.step(step)
                    step_info.update(case_run)
                    if isinstance(step_info, dict):
                        case_step_list.append(step_info)
                    else:
                        case_run = interface_is_delete(case_run, case.case_name, step["if_name"], step_info)
                        return case_run
            testsuites_json_path = HttpRunerMain(case_step_list, locust=self.locust).splicing_api()
            if not self.locust:
                from lib.helper import pattern

                today = str(datetime.datetime.now())[:10]
                log_file = os.path.join(settings.BASE_DIR, "logs" + pattern + "all-" + today + ".log")
                runner = HttpRunner(failfast=False, log_file=log_file)
                report_path = runner.run(testsuites_json_path)
                summary = runner._summary
                case_run['summary'] = summary
                case_run['report_path'] = report_path
                case_run['case_name'] = case.case_name
            else:
                return testsuites_json_path
        elif self.run_mode == '0':
            try:
                case = Case.objects.get(case_id=self.case_id)
            except Case.DoesNotExist as e:
                case_run = case_is_delete(case_run, e, self.case_id)
                return case_run

            self.step_list = eval(case.content)
            for step in self.step_list:
                step_info = self.step(step)
                if isinstance(step_info, dict):
                    case_step_list.append(step_info)
                    if step_info["result"] == "fail":
                        case_run["result"] = "fail"
                    if step_info["result"] == "error":
                        case_run["result"] = "error"
                else:
                    case_run = interface_is_delete(case_run, case.case_name, step["if_name"], step_info)
                    return case_run

            case_run['case_name'], case_run["step_list"] = case.case_name, case_step_list
            log.info('interface response data: {}'.format(case_run))
        return case_run

    def step(self, step_content):
        """
        处理各种情况的参数，并请求接口
        :param step_content:
        :return:
        """
        if_id = step_content["if_id"]
        try:
            interface = Interface.objects.get(if_id=if_id)
        except Interface.DoesNotExist as e:
            return e  # 接口不存在
        if self.run_mode == '0':
            var_list = extract_variables(step_content)
            if var_list:  # 检查是否存在变量
                for var_name in var_list:
                    var_value = get_param(var_name, step_content)
                    if var_value is None:
                        var_value = get_param(var_name, self.step_json)
                    if var_value is None:
                        for extract_dict in self.extract_list:  # 把变量替换为提取的参数
                            if var_name in extract_dict.keys():
                                var_value = extract_dict[var_name]
                    step_content = json.loads(replace_var(step_content, var_name, var_value))

        if_dict = {"url": interface.url, "header": step_content["header"], "body": step_content["body"], "if_id": if_id,
                   "if_name": step_content["if_name"], "method": interface.method, "data_type": interface.data_type}
        # 跳过不执行
        if interface.skip:
            if_dict["skip"] = interface.skip
        elif step_content["skip"]:
            if_dict["skip"] = step_content["skip"]
        else:
            if_dict["skip"] = ""

        if_dict['body'] = format_body(if_dict['body'])  # body参数中存在list或者dict，或者dict本身就是list
        if if_dict['body'] == 'error':
            if_dict = eval_set_error(if_dict)
            return if_dict

        if self.run_mode == '0':
            if_dict['body'] = http_random(if_dict['body'])  # 默认参数化和httpruner参数化保持基本一致
            if_dict['header'] = random_params(if_dict['header'])  # random参数化
            if_dict['body'] = random_params(if_dict['body'])
            if if_dict['header'] == 'error' or if_dict['body'] == 'error':  # 参数化异常
                if_dict = parametric_set_error(if_dict)
                return if_dict

        # if self.run_mode == '0':  # 补全header
        set_headers = Environment.objects.get(env_id=self.env_id).set_headers
        if set_headers and not interface.is_header:  # 把设置的header赋值到if_dict中
            headers = eval(set_headers)['header']
            # for k, v in headers.items():
            #     if '$' not in v:
            #         self.make = True
            # if self.make:
            if self.headers:
                self.headers.update(if_dict["header"])
                if_dict['header'] = self.headers
            else:
                headers.update(if_dict['header'])
                if_dict['header'] = headers
        # if interface.data_type == 'sql':
        #     for k, v in if_dict['body'].items():
        #         if 'select' in v:
        #             if_dict['body'][k] = self.sql.execute_sql(v)
        #             if not if_dict['body'][k]:
        #                 if_dict = sql_query_error(if_dict, v)
        #                 return if_dict

        if interface.is_sign:  # 接口存在签名时，处理参数
            if self.sign_type == "md5加密":  # md5加密
                if_dict["body"] = user_sign_api(if_dict["body"], self.private_key)
            elif self.sign_type == "无":  # 不签名
                pass
            elif self.sign_type == "用户认证":  # 用户认证
                self.user_auth = auth_user()
            elif self.sign_type == "AES算法":  # AES算法加密
                if len(self.private_key) in [16, 24, 32]:
                    if_dict["body"] = encryptAES(json.dumps(if_dict['body']).encode('utf-8'),
                                                 self.private_key.encode('utf-8')).decode('utf-8')
                else:
                    if_dict = AES_length_error(if_dict)  # AES密钥设置异常
                    return if_dict
        else:
            if 'true' in step_content['body']:
                if_dict["body"] = True
            elif 'false' in step_content['body']:
                if_dict['body'] = False

        if interface.data_type == 'file':  # 图片上传类型接口
            if_dict["body"] = {
                "file": ("login-bg.jpg", open("/var/static/static/img/login-bg.jpg", "rb"), "image/jpeg", {})}

        if self.run_mode == '0':
            if interface.set_mock == '1':  # 使用mock接口
                if_dict['url'] = 'http://www.easytest.xyz/mocks' + interface.url
                if_dict['base_url'] = 'http://www.easytest.xyz/mocks'
            else:
                if_dict["url"] = self.env_url + interface.url
        elif self.run_mode == '1':
            if interface.set_mock == '1':
                if_dict['base_url'] = 'http://www.easytest.xyz/mocks'
            else:
                if_dict['base_url'] = self.env_url
            if_dict['path'] = interface.url

        if_dict["url"], if_dict["body"] = format_url(if_dict["url"], if_dict["body"])

        if self.run_mode == '1':
            if_dict['extract'] = step_content['extract']
            if_dict['validators'] = step_content['validators']
            return if_dict
        else:
            # if not interface.set_mock:  # 请求接口或者模拟接口返回值
            if if_dict["skip"]:
                if_dict["skipped"] = "skipped"
                if_dict["result"] = "skipped"
                if_dict["msg"] = "skipped"
                if_dict["res_content"] = if_dict["skip"]
                if_dict['checkpoint'] = if_dict["skip"]
                return if_dict
            try:
                if interface.is_sign:
                    if self.sign_type == "AES算法":
                        res = call_interface(self.s, if_dict["method"], if_dict["url"], if_dict["header"],
                                             {'data': if_dict["body"]}, if_dict["data_type"])
                    else:
                        res = call_interface(self.s, if_dict["method"], if_dict["url"], if_dict["header"],
                                             if_dict["body"], if_dict["data_type"], self.user_auth)
                else:
                    res = call_interface(self.s, if_dict["method"], if_dict["url"], if_dict["header"],
                                         if_dict["body"], if_dict["data_type"])
                if_dict["res_status_code"] = res.status_code
                try:
                    if_dict["res_content"] = eval(
                        res.text.replace('false', 'False').replace('null', 'None').replace('true',
                                                                                           'True'))  # 查看报告时转码错误的问题
                    if isinstance(if_dict["res_content"], dict):
                        if_dict["res_content"].update({"res_status_code": res.status_code})
                    elif isinstance(if_dict["res_content"], list):
                        res_content = {}
                        res_content.update({"res_status_code": res.status_code, "data": if_dict["res_content"]})
                        if_dict["res_content"] = res_content
                    elif isinstance(if_dict["res_content"], (str, int)):
                        if_dict["res_content"] = {"res_status_code": res.status_code, "data": res.text}
                    if isinstance(if_dict['res_content'], dict):
                        if '系统异常' in if_dict['res_content'].values():
                            if_dict = response_value_error(if_dict, make=True)
                            return if_dict
                except SyntaxError as e:
                    if_dict["res_content"] = {"res_status_code": res.status_code, "data": res.text}  # 返回值无法eval的情况
            except requests.RequestException as e:
                if_dict = request_api_error(if_dict, e)  # 接口请求异常
                return if_dict

            if not isinstance(if_dict["res_content"], str):
                if interface.is_header:  # 补充默认headers中的变量
                    set_headers = Environment.objects.get(env_id=self.env_id).set_headers
                    if set_headers:
                        self.headers = eval(set_headers)['header']
                        from lib.public import httprunner_extract
                        if self.headers:
                            for k, v in self.headers.items():
                                v = extract_variables(v)
                                if v:
                                    self.headers[k] = httprunner_extract(if_dict["res_content"], v)

                if step_content["extract"]:  # 提取接口中的变量
                    extract_dict = get_extract(step_content["extract"], if_dict["res_content"],
                                               interface.url)
                    if 'error' in extract_dict.keys():
                        if_dict = index_error(if_dict, extract_dict)
                        return if_dict
                    else:
                        self.extract_list.append(extract_dict)

            if step_content["validators"]:  # 判断接口返回值
                validators = str_number(step_content["validators"])
                if_dict["result"], if_dict["msg"], if_dict['checkpoint'] = validators_result(validators, if_dict)
                if 'error' in if_dict['result']:
                    if_dict['result'] = 'error'
                elif 'fail' in if_dict['result']:
                    if_dict['result'] = 'fail'
                else:
                    if_dict['result'] = 'pass'
            else:
                if_dict = checkpoint_no_error(if_dict)

            if interface.data_type == 'file':
                if_dict["body"] = {'file': '上传图片'}
            end_time = time.clock()
            interface_totalTime = str(end_time - self.begin_time)[:6] + ' s'  # 接口执行时间
            if_dict['interface_totalTime'] = interface_totalTime
            return if_dict

    def get_env(self, env_id):
        """
        获取测试环境
        :param env_id:
        :return:
        """
        try:
            env = Environment.objects.get(env_id=env_id)
            prj_id = env.project.prj_id
            return prj_id, env.url, env.private_key
        except ValueError:
            return False

    def get_sign(self, prj_id):
        """
        获取签名方式
        :param prj_id:
        :return:
        """
        prj = Project.objects.get(prj_id=prj_id)
        sign_type = prj.sign.sign_type
        return sign_type


def get_user(user_id):
    '''
    判断用户是否存在
    :param user_id:
    :return:
    '''
    if not user_id:
        return False
    else:
        try:
            user = User.objects.get(id=user_id)
            return user.username
        except User.DoesNotExist:
            return False


def is_superuser(user_id, type='', off=''):
    """
    权限  超级用户和普通用户
    :param user_id:
    :param type:
    :return:
    """
    superuser = User.objects.get(id=user_id).is_superuser
    if superuser and off == '0':
        prj_list = Project.objects.filter(user_id=user_id)
    elif superuser or off == '1':
        prj_list = Project.objects.all()
    else:
        prj_list = Project.objects.filter(user_id=user_id)
    if type == 'list':
        project_list = []
        for prj in prj_list:
            project_list.append(prj.prj_id)
        return project_list
    else:
        return prj_list


def get_total_values(user_id):
    """
    首页统计图显示数据
    :param user_id:
    :return:
    """
    total = {
        'pass': [],
        'fail': [],
        'error': [],
        'skip': [],
        'percent': []
    }
    today = datetime.date.today()
    plan_list = []
    prj_list = is_superuser(user_id, type='list', off='1')
    plan = Plan.objects.filter(project_id__in=prj_list)
    for plan_ in plan:
        plan_list.append(plan_.plan_id)
    for i in range(-11, 1):
        begin = today + datetime.timedelta(days=i)
        end = begin + datetime.timedelta(days=1)
        total_pass = Report.objects.all().filter(update_time__range=(begin, end)).aggregate(
            pass_num=Sum('pass_num'))['pass_num']
        total_fail = Report.objects.all().filter(update_time__range=(begin, end)).aggregate(
            fail_num=Sum('fail_num'))['fail_num']
        total_error = Report.objects.all().filter(update_time__range=(begin, end)).aggregate(
            error_num=Sum('error_num'))['error_num']
        total_skip = Report.objects.all().filter(update_time__range=(begin, end)).aggregate(
            skip_num=Sum('skip_num'))['skip_num']
        if not total_pass:
            total_pass = 0
        if not total_fail:
            total_fail = 0
        if not total_error:
            total_error = 0
        if not total_skip:
            total_skip = 0

        total_percent = round(total_pass / (total_pass + total_fail + total_error + total_skip) * 100, 2) if (
                                                                                                                 total_pass + total_fail + total_error + total_skip) != 0 else 0.00
        total['pass'].append(total_pass)
        total['fail'].append(total_fail)
        total['error'].append(total_error)
        total['skip'].append(total_skip)
        total['percent'].append(total_percent)

    return total
