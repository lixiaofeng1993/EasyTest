#!/usr/bin/env python
# coding:utf-8
import json, re, os
import time
import logging
from datetime import datetime
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # 分页
from .error_code import ErrorCode

log = logging.getLogger('log')  # 初始化log


def pagination_data(paginator, page, is_paginated):
    """
    牛掰的分页
    :param paginator:
    :param page:
    :param is_paginated:
    :return:
    """
    if not is_paginated:
        # 如果没有分页，则无需显示分页导航条，不用任何分页导航条的数据，因此返回一个空的字典
        return {}

    # 当前页左边连续的页码号，初始值为空
    left = []

    # 当前页右边连续的页码号，初始值为空
    right = []

    # 标示第 1 页页码后是否需要显示省略号
    left_has_more = False

    # 标示最后一页页码前是否需要显示省略号
    right_has_more = False

    # 标示是否需要显示第 1 页的页码号。
    # 因为如果当前页左边的连续页码号中已经含有第 1 页的页码号，此时就无需再显示第 1 页的页码号，
    # 其它情况下第一页的页码是始终需要显示的。
    # 初始值为 False
    first = False

    # 标示是否需要显示最后一页的页码号。
    # 需要此指示变量的理由和上面相同。
    last = False

    # 获得用户当前请求的页码号
    page_number = page.number

    # 获得分页后的总页数
    total_pages = paginator.num_pages

    # 获得整个分页页码列表，比如分了四页，那么就是 [1, 2, 3, 4]
    page_range = paginator.page_range

    if page_number == 1:
        # 如果用户请求的是第一页的数据，那么当前页左边的不需要数据，因此 left=[]（已默认为空）。
        # 此时只要获取当前页右边的连续页码号，
        # 比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 right = [2, 3]。
        # 注意这里只获取了当前页码后连续两个页码，你可以更改这个数字以获取更多页码。
        right = page_range[page_number:page_number + 2]

        # 如果最右边的页码号比最后一页的页码号减去 1 还要小，
        # 说明最右边的页码号和最后一页的页码号之间还有其它页码，因此需要显示省略号，通过 right_has_more 来指示。
        if right[-1] < total_pages - 1:
            right_has_more = True

        # 如果最右边的页码号比最后一页的页码号小，说明当前页右边的连续页码号中不包含最后一页的页码
        # 所以需要显示最后一页的页码号，通过 last 来指示
        if right[-1] < total_pages:
            last = True

    elif page_number == total_pages:
        # 如果用户请求的是最后一页的数据，那么当前页右边就不需要数据，因此 right=[]（已默认为空），
        # 此时只要获取当前页左边的连续页码号。
        # 比如分页页码列表是 [1, 2, 3, 4]，那么获取的就是 left = [2, 3]
        # 这里只获取了当前页码后连续两个页码，你可以更改这个数字以获取更多页码。
        left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]

        # 如果最左边的页码号比第 2 页页码号还大，
        # 说明最左边的页码号和第 1 页的页码号之间还有其它页码，因此需要显示省略号，通过 left_has_more 来指示。
        if left[0] > 2:
            left_has_more = True

        # 如果最左边的页码号比第 1 页的页码号大，说明当前页左边的连续页码号中不包含第一页的页码，
        # 所以需要显示第一页的页码号，通过 first 来指示
        if left[0] > 1:
            first = True
    else:
        # 用户请求的既不是最后一页，也不是第 1 页，则需要获取当前页左右两边的连续页码号，
        # 这里只获取了当前页码前后连续两个页码，你可以更改这个数字以获取更多页码。
        left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number - 1]
        right = page_range[page_number:page_number + 2]

        # 是否需要显示最后一页和最后一页前的省略号
        if right[-1] < total_pages - 1:
            right_has_more = True
        if right[-1] < total_pages:
            last = True

        # 是否需要显示第 1 页和第 1 页后的省略号
        if left[0] > 2:
            left_has_more = True
        if left[0] > 1:
            first = True

    data = {
        'left': left,
        'right': right,
        'left_has_more': left_has_more,
        'right_has_more': right_has_more,
        'first': first,
        'last': last,
    }

    return data


def paginator(data, page):
    """
    普通分页
    :param data:
    :param page:
    :return:
    """
    paginator = Paginator(data, 10)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)  # page不是整数，取第一页
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)  # page不在范围，取最后一页
    return contacts


def format_url(url, body):
    """
    处理路径中带{}的情况
    :param url:
    :param body:
    :return:
    """
    url_params = re.findall('{(\w+)}', url)  # 格式化utl<带有 {} 的情况
    if url_params:
        url = url.replace(url_params[0], '')
        for k, v in body.items():
            if k == url_params[0]:
                url = url.format(v)
        body.pop(url_params[0])
        return url, body
    else:
        return url, body


def get_check_filed(check_filed, response):
    """
    返回值降序排序后，获取断言字段值
    :param check_filed: 查找的排序字段
    :param response: 降序排序后的返回值
    :return:
    """
    param_val = None
    if "." in check_filed:
        patt = check_filed.split('.')
        for par in patt:
            if isinstance(response, list):
                for check in response:
                    if check[0] == par:
                        patt.remove(par)
                        param_val = httprunner_extract(check[1], patt)
    elif isinstance(response, list):
        for check in response:
            if isinstance(check, tuple):
                if check[0] == check_filed:
                    param_val = check[1]
    return param_val


def validators_result(validators_list, res):
    """
    验证结果
    :param validators_list:
    :param res:
    :return:
    """
    msg = ""
    result = ""
    checkpoint = ''
    # response = res["res_content"]
    response = sorted(res["res_content"].items(), reverse=True)  # 字典降序排序
    for var_field in validators_list:
        check_filed = var_field["check"]
        expect_filed = str(var_field["expect"]).lower()
        comparator = var_field['comparator']
        checkpoint += '字段：' + check_filed + '--> 值：' + expect_filed + '    '
        # check_filed_value = str(get_param(check_filed, response)).lower()
        check_filed_value = str(get_check_filed(check_filed, response)).lower()
        if 'error' in res.keys():
            result += "error" + '    '
            msg += res['error']
        elif 'fail' in res.keys():
            result += "fail" + '    '
            msg += res['fail']
        elif comparator == 'eq':
            if check_filed_value == expect_filed:
                result += "pass" + '    '
                msg += "success！" + '    '
            else:
                result += "fail" + '    '
                msg += "断言方式 -> 等于    字段: " + check_filed + " 实际值为：" + str(
                    check_filed_value) + " 与期望值：" + expect_filed + " 不符" + '    '
        elif comparator == 'neq':
            if expect_filed != check_filed_value:
                result += "pass" + '    '
                msg += "success！" + '    '
            else:
                result += "fail" + '    '
                msg += "断言方式 -> 不等于    字段: " + check_filed + " 实际值为：" + str(
                    check_filed_value) + " 与期望值：" + expect_filed + " 相等" + '    '
        elif comparator == 'included':
            if expect_filed in check_filed_value:
                result += "pass" + '    '
                msg += "success！" + '    '
            else:
                result += "fail" + '    '
                msg += "断言方式 -> 包含    字段: " + check_filed + " 实际值为：" + str(
                    check_filed_value) + "  不包含  " + " 期望值：" + expect_filed + '    '
        elif comparator == 'not_included':
            if expect_filed not in check_filed_value:
                result += "pass" + '    '
                msg += "success！" + '    '
            else:
                result += "fail" + '    '
                msg += "断言方式 -> 不包含    字段: " + check_filed + " 实际值为：" + str(
                    check_filed_value) + "  包含  " + " 与期望值：" + expect_filed + '    '
        else:
            result += "fail" + '    '
            msg += "字段: " + check_filed + " 实际值为：" + str(
                check_filed_value) + " 与期望值：" + expect_filed + " 不符" + '    '
    return result, msg, checkpoint


def get_extract(extract_dict, res, url=''):
    """
    在response中提取参数, 并放到列表中
    :param extract_dict: 要提取参数的字典
    :param res: 要提取参数的返回值
    :param url: 要拼接的接口路径
    :return: 处理好的要提取的参数和值，装在字典中返回
    """
    with_extract_dict = {}
    make = False
    for key, value in extract_dict.items():
        if "str(" in value:
            patt = re.compile("str\((.+)\)")
            value = patt.findall(value)[0]
            make = True
        patt = value.split('.')
        _extract = httprunner_extract(res, patt)
        if _extract == 'error':
            return {'error': ErrorCode.extract_value_path_error}
        else:
            if not make:
                if _extract.isdigit():
                    with_extract_dict[key] = int(_extract)
                else:
                    try:
                        with_extract_dict[key] = float(_extract)
                    except ValueError:
                        with_extract_dict[key] = _extract
            else:
                with_extract_dict[key] = _extract

                # if ',' in key:  # 一个接口支持同时提取多个参数
                #     key_list = key.split(',')
                #     if len(key_list) > 1:
                #         for k in key_list:
                #             key_value = the_same_one(k, res)
                #             if isinstance(key_value, dict):
                #                 with_extract_dict = key_value
                #             else:
                #                 url_key = splicing_url(url, k)
                #                 with_extract_dict[url_key] = key_value
                #     else:
                #         key = key.strip(',')
                #         key_value = get_param(key, res)
                #         url_key = splicing_url(url, key)
                #         with_extract_dict[url_key] = key_value
                # else:
                #     key_value = the_same_one(key, res)
                #     if isinstance(key_value, dict):
                #         with_extract_dict = key_value
                #     else:
                #         url_key = splicing_url(url, key)
                #         with_extract_dict[url_key] = key_value
    return with_extract_dict


def httprunner_extract(res, patt):
    for par in patt:
        try:
            try:
                res = res[int(par)]
            except ValueError:
                res = res[par]
        except Exception:
            return 'error'
        patt.remove(par)
        if patt:
            return httprunner_extract(res, patt)
        else:
            return str(res)


def the_same_one(key, res):
    """
    :param key:  提取的参数名称
    :param res: 返回值
    :return:
    """
    if '_' in key:  # 一个接口支持提取相同参数中的某个
        key_list = key.split('_')
        try:
            num = int(key_list[-1])
        except ValueError:
            num = ''
        if isinstance(num, int):
            if len(key_list) == 1:  # 参数不能为数字
                key_value = get_param(key, res)
            else:
                key_value = get_param(key[:-(len(str(num)) + 1)], res, num)  # 符合上述条件，去掉后num位数的加1位 传参
        else:
            key_value = get_param(key, res)
    else:
        key_value = get_param(key, res)
    return key_value


def splicing_url(url, key):
    """
    :param url: api 路径
    :param key:  提取的参数
    :return: 拼接后的key
    """
    if url:
        url = url.strip('/').replace('/', '_')
        url_key = url + '_' + key  # 拼接接口路径和参数
    else:
        url_key = key
    return url_key


def replace_var(content, var_name, var_value):
    """
    替换内容中的变量
    :param content: 要被提取变量的用例数据
    :param var_name: 提取的参数
    :param var_value: 提取的参数值
    :return: 返回替换后的用例数据
    """
    if not isinstance(content, str):
        content = json.dumps(content)
    var_name = "$" + var_name
    if isinstance(var_value, (int, float)):
        content = content.replace('\"' + str(var_name) + '\"', str(var_value))
    else:
        content = content.replace(str(var_name), str(var_value))
    return content


def extract_variables(content):
    """
    从内容中提取所有变量名, 变量格式为$variable,返回变量名list
    :param content: 要被提取变量的用例数据
    :return: 所有要提取的变量
    """
    variable_regexp = r"\$([\w_]+)"
    if not isinstance(content, str):
        content = str(content)
    try:
        return re.findall(variable_regexp, content)
    except TypeError:
        return []


def get_param(param, content, num=0):
    """
    在内容中获取某一参数的值
    :param param: 从接口返回值中要提取的参数
    :param content: 接口返回值
    :param num: 返回值中存在list时，取指定第几个
    :return: 返回非变量的提取参数值
    """
    param_val = None
    if "." in param:
        patt = param.split('.')
        param_val = httprunner_extract(content, patt)
        return param_val
    else:
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except:
                content = ""
        if isinstance(content, dict):
            param_val = get_param_response(param, content, num)
        if isinstance(content, list):
            dict_data = {}
            for i in range(len(content)):
                try:
                    dict_data[str(i)] = eval(content[i])
                except:
                    dict_data[str(i)] = content[i]
            param_val = get_param_response(param, dict_data, num)
        if param_val is None:
            return param_val
        else:
            if "$" + param == param_val:
                param_val = None
            return param_val


def get_param_response(param_name, dict_data, num=0, default=None):
    """
    :param param_name: 从接口返回值中要提取的参数
    :param dict_data: 接口返回值
    :param num: 返回值中存在list时，取指定第几个
    :param default: 函数异常返回
    :return: 提取的参数值
    """
    if isinstance(dict_data, dict):
        for k, v in dict_data.items():
            if k == param_name:
                return v
            else:
                if isinstance(v, dict):
                    ret = get_param_response(param_name, v)
                    if ret is not default:
                        return ret
                if isinstance(v, list):
                    if num:
                        try:
                            if isinstance(v[num], dict):
                                ret = get_param_response(param_name, v[num])
                                if ret is not default:
                                    return ret
                        except IndexError:
                            return {'error': ErrorCode.index_error}
                    else:
                        for i in v:
                            if isinstance(i, dict):
                                ret = get_param_response(param_name, i)
                                if ret is not default:
                                    return ret
                if isinstance(v, str):
                    try:
                        value = eval(v)
                        ret = get_param_response(param_name, value)
                        if ret is not default:
                            return ret
                    except Exception:
                        pass
    elif isinstance(dict_data, list):
        for content in dict_data:
            ret = get_param_response(param_name, content)
            if ret is not default:
                return ret
    return default


def str_number(params):
    """数字需要是str的情况"""
    if isinstance(params, dict):
        for key, value in params.items():
            if "str" in str(value):  # 参数值数字需要时字符串的情况，传参时使用 str(number)
                patt = re.compile("str\((\d+)\)")
                number_list = patt.findall(value)
                if number_list:
                    params[key] = str(number_list[0])
        return params


def format_body(body):
    """
    处理body参数中存在list或者dict后者本身为list的情况
    :param body:
    :return:
    """
    if isinstance(body, dict):
        for key, value in body.items():
            body = str_number(body)
            if not isinstance(value, (int, float)):  # 排除参数是int的情况
                value = re.sub('[\n\t ]', '', value)
                if key == 'list':  # 标识body参数为list的情况
                    try:
                        body = eval(value)
                    except Exception:
                        return 'error'
                else:
                    if '[' in value or '{' in value and "$" not in value:
                        try:
                            body[key] = eval(value)
                        except Exception as e:
                            return 'error'
        return body
    else:
        return 'error'


def http_random(body):
    if isinstance(body, dict):
        for key, value in body.items():
            if not str(value).isdigit():
                if "_random_in" in value:
                    body[key] = "__random_int()"
                elif "_name" in value:
                    body[key] = "__name"
                elif "_address" in value:
                    body[key] = "__address"
                elif "_phone" in value:
                    body[key] = "__phone"
                elif "_text" in value:
                    body[key] = "__text()"
                elif "_random_time" in value:
                    body[key] = "__random_time"
                elif "_now" in value:
                    body[key] = "__now"
                elif "_email" in value:
                    body[key] = "__email"
                elif "list(" in value:
                    patt = re.compile("list\((.+)\)")
                    params = patt.findall(value)[0]
                    params = params.split(',')[0]
                    body[key] = params
        return body


def call_interface(s, method, url, header, data, content_type='json', user_auth=''):
    """
    发送请求
    :param s:
    :param method:
    :param url:
    :param header:
    :param data:
    :param content_type:
    :param user_auth:
    :return:
    """
    # log.info('========interface params==============> {} {} {} {}'.format(url, header, data, content_type))
    if method in ["post", "put"]:
        if content_type in ["json", 'sql']:
            res = s.request(method=method, url=url, json=data, headers=header, verify=False)
            # res = requests.post(url=url, json=data, headers=header, verify=False)
        if content_type == "data":
            res = s.request(method=method, url=url, data=data, headers=header, verify=False)
            # res = s.request(method=method, url=url, data=json.dumps(data), headers=header, verify=False)
            # res = requests.post(url=url, data=data, headers=header, verify=False)
    if method in ["get", "delete"]:
        # res = requests.get(url=url, params=data, headers=header, verify=False)
        if content_type in ["json", 'sql']:
            res = s.request(method=method, url=url, json=data, headers=header, verify=False)
        else:
            if user_auth:
                res = s.request(method=method, url=url, params=data, headers=header, auth=user_auth)
            else:
                res = s.request(method=method, url=url, params=data, headers=header, verify=False)
    if content_type == 'file':
        # res = s.request(method=method, url=url, params=data, headers=header, verify=False)
        res = s.request(method=method, url=url, files=data, headers=header, verify=False)
    # log.info('========接口返回信息==============> {} {}'.format(res.status_code, res.text))
    return res


def get_new_report_html(report_path_html):
    """
    获取最新的测试报告
    :param report_path_html:
    :return:
    """
    lists = os.listdir(report_path_html)
    for file_name in lists:
        if os.path.splitext(file_name)[1] == '.html':
            continue
        else:
            lists.remove(file_name)
    lists.sort(key=lambda a: os.path.getmtime(os.path.join(report_path_html, a)))
    log.info('最新的测试报告是：{} '.format(lists[-1]))
    report_file_html = os.path.join(report_path_html, lists[-1])  # 找到最新的测试报告文件
    return report_file_html


import matplotlib as mpl
from matplotlib import pyplot as plt
# from matplotlib.font_manager import FontProperties
from collections import OrderedDict


# font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf", size=14)


def DrawPie(pass_num=0, fail=0, error=0):
    """
    绘制饼图用pie
    :return:
    """
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    now_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
    mpl.rcParams[u'font.sans-serif'] = ['simhei']
    mpl.rcParams['axes.unicode_minus'] = False
    # 调节图形大小，宽，高
    # plt.figure(figsize=(6, 9))
    # 定义饼状图的标签，标签是列表
    labels = 'pass', 'fail', 'error'
    # 每个标签占多大，会自动去算百分比
    my_labels = [pass_num, fail, error]
    colors = ['green', 'orange', 'red']
    # 将某部分爆炸出来， 使用括号，将第一块分割出来，数值的大小是分割出来的与其他两块的间隙
    explode = (0.05, 0, 0)

    patches, l_text, p_text = plt.pie(my_labels, explode=explode, labels=labels, colors=colors,
                                      labeldistance=1.1, autopct='%3.1f%%', shadow=False,
                                      startangle=90, pctdistance=0.6, textprops={'fontsize': 12, 'color': 'w'})

    # labeldistance，文本的位置离远点有多远，1.1指1.1倍半径的位置
    # autopct，圆里面的文本格式，%3.1f%%表示小数有三位，整数有一位的浮点数
    # shadow，饼是否有阴影
    # startangle，起始角度，0，表示从0开始逆时针转，为第一块。一般选择从90度开始比较好看
    # pctdistance，百分比的text离圆心的距离
    # patches, l_texts, p_texts，为了得到饼图的返回值，p_texts饼图内部文本的，l_texts饼图外label的文本

    # 改变文本的大小
    # 方法是把每一个text遍历。调用set_size方法设置它的属性
    for t in l_text:
        t.set_size = (30)
    for t in p_text:
        t.set_size = (20)
    plt.title('Running results of test cases')
    # 显示图例,去掉重复的标签
    colors, labels = plt.gca().get_legend_handles_labels()
    by_labels = OrderedDict(zip(labels, colors))
    plt.legend(by_labels.values(), by_labels.keys(), loc='upper left')
    # 设置x，y轴刻度一致，这样饼图才能是圆的
    plt.axis('equal')
    # plt.show()
    # 保存饼图
    pic_path = settings.MEDIA_ROOT
    # pic_path = '/var/lib/jenkins/workspace/EasyTest/media'
    imgPath = os.path.join(pic_path, str(now_time) + "pie.png")
    plt.savefig(imgPath)
    plt.tight_layout()
    plt.cla()  # 不覆盖
    return str(now_time) + "pie.png"


def is_number(s):
    """
    判断是否是数字
    :param s:
    :return:
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def gr_code(url):
    """
    生成二维码
    :param url:
    :return:
    """
    import qrcode
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    now_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
    pic_path = settings.MEDIA_ROOT
    imgPath = os.path.join(pic_path, str(now_time) + "qrcode.png")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(imgPath)
    return str(now_time) + "qrcode.png"


import urllib.request
import urllib.parse
import json

appid = ""
appsecret = ""


def getToken(appid, appsecret):
    """
    获取TOKEN
    :param appid:
    :param appsecret:
    :return:
    """
    # 这个是微信获取小程序码的接口
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}'.format(
        appid=appid, appsecret=appsecret)
    # 准备一下头
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    }

    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    readData = response.read()
    readData = readData.decode('utf-8')
    obj = json.loads(readData)
    try:
        access_token = obj['access_token']
        return access_token
    except KeyError:
        return None


def getACodeImage(appid, appsecret, values):
    """
    获取小程序码
    :param appid:
    :param appsecret:
    :param values:
    :return:
    """
    # 这个是微信获取小程序码的接口
    token = getToken(appid, appsecret)
    if not token:
        return None
    url = 'https://api.weixin.qq.com/wxa/getwxacode?access_token={token}'.format(token=token)
    # 准备一下头
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    }
    # 用Post传值，这里值用JSON的形式
    # values = {"path": "pages/index/detail/index?id=365&campId=12&index=1"}
    # 将字典格式化成能用的形式,urlencode不能用
    # data = urllib.parse.urlencode(values).encode('utf-8')
    # 使用json.dumps的方式序列化为字符串，然后bytes进行编码
    data = json.dumps(values)
    data = bytes(data, 'utf8')
    # 创建一个request,放入我们的地址、数据、头
    request = urllib.request.Request(url, data, headers)
    # 将获取的数据存在本地文件
    readData = urllib.request.urlopen(request).read()
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    now_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
    pic_path = settings.MEDIA_ROOT
    imgPath = os.path.join(pic_path, str(now_time) + "small-qrcode.png")
    with open(imgPath, 'wb') as f:
        f.write(readData)
    return str(now_time) + "small-qrcode.png"


def remove_logs(path):
    """
    到期删除日志文件
    :param path:
    :return:
    """
    file_list = os.listdir(path)  # 返回目录下的文件list
    now_time = datetime.now()
    num = 0
    for file in file_list:
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            file_ctime = datetime(*time.localtime(os.path.getctime(file_path))[:6])
            if (now_time - file_ctime).days > 5:
                try:
                    os.remove(file_path)
                    num += 1
                    log.info('------删除文件------->>> {}'.format(file_path))
                except PermissionError as e:
                    log.warning('删除文件失败：{}'.format(e))
        else:
            log.info('文件夹跳过：{}'.format(file_path))
    return num
