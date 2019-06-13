#!/usr/bin/env python
# coding:utf-8
import json, re, os
import time
from common.logger import Log
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # 分页


def paginator(data, page):
    paginator = Paginator(data, 10)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)  # page不是整数，取第一页
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)  # page不在范围，取最后一页
    return contacts


# 格式化utl<带有 {} 的情况>
def format_url(url, body):
    # url_params = re.findall('({\w+})', url)
    url_params = re.findall('{(\w+)}', url)
    if url_params:
        url = url.replace(url_params[0], '')
        for k, v in body.items():
            if k == url_params[0]:
                url = url.format(v)
        body.pop(url_params[0])
        return url, body
    else:
        return url, body


# 验证结果
def validators_result(validators_list, res):
    msg = ""
    result = ""
    checkpoint = ''
    for var_field in validators_list:
        check_filed = var_field["check"]
        expect_filed = var_field["expect"]
        checkpoint += '字段：' + check_filed + '--> 值：' + expect_filed + '    '
        check_filed_value = str(get_param(check_filed, res)).lower()
        if check_filed_value == expect_filed:
            result += "pass" + '    '
            msg += "success！" + '    '
        else:
            result += "fail" + '    '
            msg += "字段: " + check_filed + " 实际值为：" + str(check_filed_value) + " 与期望值：" + expect_filed + " 不符" + '    '
            # break
    return result, msg, checkpoint


# 在response中提取参数, 并放到列表中
def get_extract(extract_dict, res):
    for key, value in extract_dict.items():
        key_value = get_param(key, res)
        extract_dict[key] = key_value
    return extract_dict


# 替换内容中的变量, 返回字符串型
def replace_var(content, var_name, var_value):
    if not isinstance(content, str):
        content = json.dumps(content)
    var_name = "$" + var_name
    content = content.replace(str(var_name), str(var_value))
    return content


# 从内容中提取所有变量名, 变量格式为$variable,返回变量名list
def extract_variables(content):
    variable_regexp = r"\$([\w_]+)"
    if not isinstance(content, str):
        content = str(content)
    try:
        return re.findall(variable_regexp, content)
    except TypeError:
        return []


# 在内容中获取某一参数的值
def get_param(param, content):
    param_val = None
    if isinstance(content, str):
        # content = json.loads(content)
        try:
            content = json.loads(content)
        except:
            content = ""
    if isinstance(content, dict):
        param_val = get_param_reponse(param, content)
    if isinstance(content, list):
        dict_data = {}
        for i in range(len(content)):
            try:
                dict_data[str(i)] = eval(content[i])
            except:
                dict_data[str(i)] = content[i]
        param_val = get_param_reponse(param, dict_data)
    if param_val is None:
        return param_val
    else:
        if "$" + param == param_val:
            param_val = None
        return param_val


def get_param_reponse(param_name, dict_data, default=None):
    for k, v in dict_data.items():
        if k == param_name:
            return v
        else:
            if isinstance(v, dict):
                ret = get_param_reponse(param_name, v)
                if ret is not default:
                    return ret
            if isinstance(v, list):
                for i in v:
                    if isinstance(i, dict):
                        ret = get_param_reponse(param_name, i)
                        if ret is not default:
                            return ret
                    else:
                        pass
    return default


# 发送请求
def call_interface(s, method, url, header, data, content_type='json'):
    print('interface params: ', url, header, data, content_type)
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
        if content_type == 'json':
            res = s.request(method=method, url=url, json=data, headers=header, verify=False)
        else:
            res = s.request(method=method, url=url, params=data, headers=header, verify=False)
    if content_type == 'file':
        # res = s.request(method=method, url=url, params=data, headers=header, verify=False)
        res = s.request(method=method, url=url, files=data, headers=header, verify=False)
    print(res.status_code, res.text)
    return res


def get_new_report_html(report_path_html):
    """获取最新的测试报告"""
    lists = os.listdir(report_path_html)
    for file_name in lists:
        if os.path.splitext(file_name)[1] == '.html':
            continue
        else:
            lists.remove(file_name)
    lists.sort(key=lambda a: os.path.getmtime(os.path.join(report_path_html, a)))
    Log().info('最新的测试报告是：%s' % lists[-1])
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
    labels = 'pass', 'fail', 'error'
    my_labels = [pass_num, fail, error]
    colors = ['green', 'orange', 'red']
    explode = [0.1, 0, 0]  # 0.1 凸出这部分，
    plt.axes(aspect=1)  # set this , Figure is round, otherwise it is an ellipse
    # autopct ，show percet
    patches, l_text, p_text = plt.pie(x=my_labels, colors=colors, explode=explode, autopct='%3.1f %%', shadow=True,
                                      labeldistance=1.1, startangle=90, pctdistance=0.6)
    # 方法是把每一个text遍历。调用set_size方法设置它的属性
    for t in l_text:
        t.set_size = (30)
    for t in p_text:
        t.set_size = (20)
    plt.title('Running results of test cases')
    # plt.show()
    # 显示图例,去掉重复的标签
    colors, labels = plt.gca().get_legend_handles_labels()
    by_labels = OrderedDict(zip(labels, colors))
    plt.legend(by_labels.values(), by_labels.keys())
    # plt.legend()
    # 保存饼图
    pic_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'media')
    imgPath = os.path.join(pic_path, str(now_time) + "pie.png")
    plt.savefig(imgPath)
    plt.tight_layout()
    plt.cla()  # 不覆盖
    return str(now_time) + "pie.png"


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def gr_code(url):
    """生成二维码"""
    import qrcode
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    now_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
    pic_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'media')
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


if __name__ == '__main__':
    pass
