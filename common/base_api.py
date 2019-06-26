# coding:utf-8
import os
import json
from common.processingJson import write_data, get_json
from common.logger import Log
from lib.public import get_extract, get_param, replace_var, extract_variables, \
    call_interface, format_url

log = Log()  # 初始化log
res_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/common' + '/config' + '/res.json'
# res_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\common' + '\\config' + '\\res.json'
extract_dict = {}


def send_requests(s, data_dict):
    """封装requests请求"""
    if not isinstance(data_dict, dict):  # 判断传入参数类型
        raise TypeError('{} 参数不是字典类型'.format(send_requests.__name__))
    else:
        method = data_dict["method"]  # 获取请求方式
        url = data_dict["url"]  # 获取请求地址
        data_type = data_dict["data_type"]  # 请求参数类型
        test_name = data_dict['if_name']  # 测试用例中文名称
        headers = replace_params(data_dict['headers'], data_dict)
        body = replace_params(data_dict['body'], data_dict, params_type=1)
        if '[' in json.dumps(body):  # body参数是list的情况
            for k, v in body.items():
                body[k] = eval(v)
        url, body = format_url(url, body)
        extract = data_dict['extract']
        checkpoint = data_dict["checkpoint"]
        if_id = data_dict['if_id']

        log.info("*******正在执行用例：-----  {} {}  ----**********".format(if_id, test_name))
        log.info("请求方式： {}, 请求url: {}".format(method, url))
        log.info("请求头部：{}".format(headers))
        log.info("{} 请求，参数类型为：{} ,参数内容为 {}".format(method, data_type, body))

        res = {}  # 接受返回数据
        try:
            # 构造请求
            r = call_interface(s, method, url, headers, body, data_type)
            log.info("页面返回信息：%s" % r.content.decode("utf-8"))
            # 信息存储到res字典中
            res['if_id'] = if_id
            res['test_name'] = test_name
            res["status_code"] = str(r.status_code)  # 状态码转成str
            res["text"] = r.content.decode("utf-8")
            if extract:
                extract_dict = get_extract(extract, res["text"])
                write_data(extract_dict, res_path)
            res["times"] = str(r.elapsed.total_seconds())  # 接口请求时间转str

            if res["status_code"] != "200":  # 判断返回code是否正常
                res["error"] = res["text"]
            else:
                res["error"] = ""
            text = json.loads(res["text"])
            result = ''
            log.info("检查点：%s" % checkpoint)
            for inspect in checkpoint:
                if inspect['expect'] == str(text[inspect['check']]):
                    result += "pass\t"
                else:
                    result += 'fail\t'
            res['result'] = result
            log.info("用例测试结果:   {}---->{}".format(test_name, res["result"]))
            res["msg"] = ""
            return res
        except Exception as msg:
            log.error('请求出现异常！ {}'.format(msg))
            res["msg"] = str(msg)  # 出现异常，保存错误信息
            res["result"] = "error"  # 结果保存错误
            return res


def replace_params(params, data_dict, params_type=0):
    """
    上下文依赖
    :param params:
    :param data_dict:
    :param params_type:
    :return:
    """
    var_list = extract_variables(params)
    if var_list:
        for var_name in var_list:
            var_value = get_param(var_name, data_dict)
            if var_value is None:
                var_value = get_json(res_path, var_name)
            data_dict = json.loads(replace_var(data_dict, var_name, var_value))
        if params_type == 0:
            log.info('headers 替换依赖参数： {}'.format(data_dict['headers']))
            return data_dict['headers']
        if params_type == 1:
            log.info('body 替换上下文依赖参数： {}'.format(data_dict['body']))
            return data_dict['body']
    else:
        return params


if __name__ == "__main__":
    pass
