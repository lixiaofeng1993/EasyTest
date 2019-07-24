#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: sql_parameter.py
# 说   明: 
# 创建时间: 2019/5/18 14:59
'''
import time, logging, sys, json, requests
from datetime import datetime
from lib.signtype import user_sign_api, encryptAES
from lib.connectMySql import SqL
from lib.public import validators_result, get_extract, get_param, replace_var, extract_variables, call_interface, \
    format_url
from lib.error_code import ErrorCode

s = requests.session()
extract_list = []
step_json = []
log = logging.getLogger('log')
sql = SqL()


# 获取签名方式
def get_sign(prj_id):
    """
    sign_type: 签名方式
    """
    sign_type = sql.execute_sql('select bp.sign_id from base_project as bp where bp.prj_id = "{}";'.format(prj_id),
                                num=1)
    return sign_type


# 获取测试环境
def get_env(env_id):
    env = sql.execute_sql(
        'select be.project_id, be.url, be.private_key from base_environment as be where be.env_id="{}";'.format(env_id),
        dict_type=True, num=1)
    return env['project_id'], env['url'], env['private_key']


def test_case(case_id, env_id, case_id_list, sign_type, private_key, env_url, begin_time=0, locust=False):
    """接口测试用例"""
    class_name = '定时任务'
    func_name = sys._getframe().f_code.co_name
    method_doc = ''
    try:
        case = sql.execute_sql(
            'select bs.case_name, bs.content from base_case as bs where bs.case_id = "{}";'.format(case_id),
            dict_type=True)
        step_list = eval(case['content'])
    except TypeError:
        case_run = {}
        log.error('用例 {} 已被删除！'.format(case_id))
        case_run['msg'] = '用例 {} 已被删除！'.format(case_id)
        case_run['error'] = ErrorCode.case_not_exit_error
        case_run['class_name'] = class_name
        return case_run, ''
    case_run = {"case_id": case_id, "case_name": case['case_name']}
    case_step_list = []
    for ste in step_list:
        if not locust:
            step_info = step(ste, sign_type=sign_type, private_key=private_key, env_url=env_url, begin_time=begin_time,
                             locust=locust, env_id=env_id)
            if isinstance(step_info, dict):
                case_step_list.append(step_info)
                if step_info["result"] == "fail":
                    case_run["result"] = "fail"
                    # break
                if step_info["result"] == "error":
                    case_run["result"] = "error"
                    # break
            else:
                log.error('用例 {} 中的接口 {} 已被删除！'.format(case['case_name'], ste["if_name"]))
                case_run['msg'] = '用例 {} 中的接口 {} 已被删除！'.format(case['case_name'], ste["if_name"])
                case_run['error'] = ErrorCode.interface_not_exit_error
                case_run['class_name'] = class_name
                return case_run, ''
        else:
            step_info, url = step(ste, sign_type=sign_type, private_key=private_key, env_url=env_url,
                                  begin_time=begin_time, locust=locust, env_id=env_id)
            if isinstance(step_info, dict):
                case_step_list.append(step_info)
            else:
                log.error('用例 {} 中的接口 {} 已被删除！'.format(case['case_name'], ste["if_name"]))
                case_run['msg'] = '用例 {} 中的接口 {} 已被删除！'.format(case['case_name'], ste["if_name"])
                case_run['error'] = ErrorCode.interface_not_exit_error
                case_run['class_name'] = class_name
                return case_run, ''
    if locust:
        return case_step_list, url
    case_run["step_list"], case_run['class_name'], case_run[
        'func_name'], case_run['method_doc'] = case_step_list, class_name, func_name, method_doc
    log.info('interface response data: {}'.format(case_run))
    return case_run


def step(step_content, sign_type, private_key, env_url, begin_time=0, locust=False, env_id=''):
    global step_json, extract_list, s
    if_id = step_content["if_id"]
    try:
        interface = sql.execute_sql(
            'select bi.url, bi.method, bi.data_type, bi.is_sign, bi.is_header from base_interface as bi where bi.if_id = {};'.format(
                if_id), dict_type=True)
        if_dict = {"url": interface['url'], 'if_id': if_id}
    except TypeError:
        return 'no'
    var_list = extract_variables(step_content)
    # 检查是否存在变量
    if var_list and not locust:
        for var_name in var_list:
            var_value = get_param(var_name, step_content)
            if var_value is None:
                var_value = get_param(var_name, step_json)
            if var_value is None:
                for extract_dict in extract_list:  # 把变量替换为提取的参数
                    if var_name in extract_dict.keys():
                        var_value = extract_dict[var_name]
            step_content = json.loads(replace_var(step_content, var_name, var_value))
    else:
        extract = step_content['extract']
    if_dict['header'], if_dict['body'] = step_content["header"], step_content["body"]
    set_headers = sql.execute_sql(
        'select be.set_headers from base_environment as be where be.env_id="{}";'.format(env_id),
        dict_type=True, num=1)
    headers = set_headers['set_headers']
    make = False
    if set_headers:
        for k, v in eval(headers)['header'].items():
            if k and v:
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
    if not locust:
        if_dict["url"] = env_url + interface['url']
    else:
        if_dict["url"] = interface['url']
    if_dict["if_id"] = if_id
    if_dict["url"], if_dict["body"] = format_url(if_dict["url"], if_dict["body"])
    if_dict["if_name"] = step_content["if_name"]
    if_dict["method"] = interface['method']
    if_dict["data_type"] = interface['data_type']
    if_dict["is_sign"] = interface['is_sign']
    if_dict["sign_type"] = sign_type
    if locust:
        if_dict['extract'] = extract
        return if_dict, env_url
    try:

        if interface['is_sign']:
            if sign_type == 4:
                res = call_interface(s, if_dict["method"], if_dict["url"], if_dict["header"],
                                     {'data': if_dict["body"]}, if_dict["data_type"])
        else:
            res = call_interface(s, if_dict["method"], if_dict["url"], if_dict["header"],
                                 if_dict["body"], if_dict["data_type"])
        if_dict["res_status_code"] = res.status_code
        # if_dict["res_content"] = res.text
        if_dict["res_content"] = eval(
            res.text.replace('false', 'False').replace('null', 'None').replace('true', 'True'))  # 查看报告时转码错误的问题
        if '系统异常' in if_dict['res_content'].values():
            if_dict['error'] = ErrorCode.interface_error
        if interface['is_header']:  # 补充默认headers中的变量
            if headers:
                for k, v in eval(headers)['header'].items():
                    if k == 'token':
                        if 'error' in if_dict.keys():
                            eval(headers)['header'][k] = ''
                        else:
                            eval(headers)['header'][k] = if_dict["res_content"]['data']
                        now_time = datetime.now()
                        sql.execute_sql(
                            'update base_environment as be set be.env_id = {}, update_time = {};'.format(env_id,
                                                                                                         now_time))
    except requests.RequestException as e:
        if_dict["result"] = "Error"
        if_dict["msg"] = str(e)
        return if_dict
    if step_content["extract"]:
        extract_dict = get_extract(step_content["extract"], if_dict["res_content"])
        if 'error' in extract_dict.keys():
            if_dict["result"] = "error"
            if_dict["checkpoint"] = ''
            if_dict["msg"] = ErrorCode.index_error
            if_dict["error"] = ErrorCode.index_error
            return if_dict
        else:
            extract_list.append(extract_dict)
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
    interface_totalTime = str(end_time - begin_time)[:6] + ' s'
    if_dict['interface_totalTime'] = interface_totalTime
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
            if_dict, url = test_case(case_id, env_id, case_id_list, sign_type, private_key, env_url, locust=True)
            if_dict_list.append(if_dict)
        return if_dict_list, url
    else:
        log.error('查询性能测试数据为空！')
        return False


if __name__ == '__main__':
    get_parameters()
