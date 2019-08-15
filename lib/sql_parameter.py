#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: sql_parameter.py
# 说   明: 
# 创建时间: 2019/5/18 14:59
'''
import time, logging, sys, json, requests
from lib.signtype import user_sign_api, encryptAES
from lib.connectMySql import SqL
from lib.public import format_url
from lib.except_check import case_is_delete, interface_is_delete, parametric_set_error
from lib.random_params import random_params

s = requests.session()
extract_list = []
step_json = []
log = logging.getLogger('log')
sql = SqL()


def get_sign(prj_id):
    """
    获取签名方式
    :param prj_id:
    :return:
    """
    sign_type = sql.execute_sql('select bp.sign_id from base_project as bp where bp.prj_id = "{}";'.format(prj_id),
                                num=1)
    return sign_type


def get_env(env_id):
    """
    获取测试环境
    :param env_id:
    :return:
    """
    env = sql.execute_sql(
        'select be.project_id, be.url, be.private_key from base_environment as be where be.env_id="{}";'.format(env_id),
        dict_type=True, num=1)
    return env['project_id'], env['url'], env['private_key']


def test_case(case_id, env_id, case_id_list, sign_type, private_key, env_url, begin_time=0):
    """
    接口测试用例
    :param case_id:
    :param env_id:
    :param case_id_list:
    :param sign_type:
    :param private_key:
    :param env_url:
    :param begin_time:
    :return:
    """
    class_name = '性能测试'
    func_name = sys._getframe().f_code.co_name
    method_doc = ''
    case_run = {'class_name': class_name, 'func_name': func_name, 'method_doc': method_doc, 'case_id': case_id}
    try:
        case = sql.execute_sql(
            'select bs.case_name, bs.content from base_case as bs where bs.case_id = "{}";'.format(case_id),
            dict_type=True)
        step_list = eval(case['content'])
    except TypeError as e:
        case_run = case_is_delete(case_run, e)
        return case_run
    case_step_list = []
    for ste in step_list:
        step_info = step(ste, sign_type=sign_type, private_key=private_key, env_url=env_url, begin_time=begin_time,
                         env_id=env_id)
        if isinstance(step_info, dict):
            case_step_list.append(step_info)
        else:
            case_run = interface_is_delete(case_run, case['case_name'], ste["if_name"], step_info)
            return case_run
    case_run['step_list'], case_run['case_name'] = case_step_list, case['case_name']
    return case_run


def step(step_content, sign_type, private_key, env_url, begin_time=0, env_id=''):
    global step_json, extract_list, s
    if_id = step_content["if_id"]
    try:
        interface = sql.execute_sql(
            'select bi.url, bi.method, bi.data_type, bi.is_sign, bi.is_header from base_interface as bi where bi.if_id = {};'.format(
                if_id), dict_type=True)
        if_dict = {"url": interface['url'], 'if_id': if_id}
    except TypeError:
        return 'no'

    extract = step_content['extract']
    if_dict['header'], if_dict['body'], if_dict['if_name'] = step_content["header"], step_content["body"], \
                                                             step_content['if_name']

    if_dict['header'] = random_params(if_dict['header'])  # random参数化
    if_dict['body'] = random_params(if_dict['body'])
    if if_dict['header'] == 'error' or if_dict['body'] == 'error':  # 参数化异常
        if_dict = parametric_set_error(if_dict)
        return if_dict

    set_headers = sql.execute_sql(
        'select be.set_headers from base_environment as be where be.env_id="{}";'.format(env_id),
        dict_type=True, num=1)
    headers = set_headers['set_headers']
    make = False
    if headers:
        for k, v in eval(headers)['header'].items():
            if '$' not in v:
                make = True
    if make:
        if_dict['header'] = eval(headers)['header']
    if interface['data_type'] == 'sql':
        for k, v in if_dict['body'].items():
            if 'select' in v:
                if_dict['body'][k] = SqL(job=True).execute_sql(v)
    # 签名
    if interface['is_sign']:
        if sign_type == 1:  # md5加密
            if_dict["body"] = user_sign_api(if_dict["body"], private_key)
        elif sign_type == 2:  # 不签名
            pass
        elif sign_type == 3:  # 用户认证
            pass
        elif sign_type == 4:  # AES算法加密
            if_dict["body"] = encryptAES(json.dumps(if_dict['body']).encode('utf-8'),
                                         private_key.encode('utf-8')).decode('utf-8')
    else:
        if 'true' in step_content['body']:
            if_dict["body"] = True
        elif 'false' in step_content['body']:
            if_dict['body'] = False
    if '[' in json.dumps(if_dict["body"]):  # body参数是list的情况
        for k, v in if_dict['body'].items():
            if_dict["body"][k] = eval(v)
    if_dict["url"] = env_url + interface['url']

    if_dict["url"], if_dict["body"] = format_url(if_dict["url"], if_dict["body"])

    if_dict["if_id"] = if_id
    if_dict["method"] = interface['method']
    if_dict["data_type"] = interface['data_type']
    if_dict["is_sign"] = interface['is_sign']
    if_dict["sign_type"] = sign_type
    if_dict['extract'] = extract
    return if_dict


def get_parameters():
    """
    locust 运行参数处理
    :return: if_dict 接口请求参数
             url     请求地址
    """
    plan = sql.execute_sql(
        'select bp.environment_id, bp.content,bp.plan_name,bp.plan_id from base_plan as bp where bp.is_locust = 1',
        dict_type=True)
    if plan != None:
        env_id = plan['environment_id']
        case_id_list = eval(plan['content'])
        prj_id, env_url, private_key = get_env(env_id)
        sign_type = get_sign(prj_id)
        if_dict_list = []
        for case_id in case_id_list:
            if_dict, url = test_case(case_id, env_id, case_id_list, sign_type, private_key, env_url)
            if_dict_list.append(if_dict)
        return if_dict_list, env_url
    else:
        log.error('查询性能测试数据为空！')
        return False


if __name__ == '__main__':
    get_parameters()
