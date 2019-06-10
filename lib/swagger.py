#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/5 10:39
# @Author  : lixiaofeng
# @Site    : 
# @File    : swagger.py
# @Software: PyCharm

import requests, logging, json

log = logging.getLogger('log')  # 初始化log


class AnalysisJson:
    """swagger自动生成测试用例"""

    def __init__(self, prj_id, url):
        self.prj_id = prj_id
        self.url = url
        self.interface_params = {}
        self.interface = []

    def check_data(self, r):
        if not isinstance(r, dict):
            log.info('swagger return json error.')
            return False
        else:
            return True

    def retrieve_data(self):
        """主函数"""
        global body_name, method
        try:
            r = requests.get(self.url + '/v2/api-docs?group=sign-api').json()
        except json.decoder.JSONDecodeError:
            log.error('swagger地址错误！')
            return 0, 0
        if self.check_data(r):
            self.data = r['paths']  # paths中的数据是有用的
        for k, v in self.data.items():
            method_list = []
            for _k, _v in v.items():
                interface = {}
                if not _v['deprecated']:  # 接口是否被弃用
                    method_list.append(_k)
                    api = k  # api地址
                    if len(method_list) > 1:  # api地址下的请求方式不止一个的情况
                        for i in range(len(method_list)):
                            body_name = api.replace('/', '_') + '_' * i  # json文件对应参数名称，excel中body名称
                            method = method_list[-1]  # 请求方式 同一个api地址，不同请求方式
                    else:
                        body_name = api.replace('/', '_')
                        method = _k
                    self.interface_params, interface = self.retrieve_excel(_v, interface, api)
                    self.interface.append(interface)
                else:
                    log.info('interface path: {}, case name: {}, is deprecated.'.format(k, _v['description']))
                    break
        return self.interface_params, self.interface

    def retrieve_excel(self, _v, interface, api):
        """解析参数，拼接为dict--准备完成写入excel的数据"""
        parameters = _v.get('parameters')  # 未解析的参数字典
        if not parameters:  # 确保参数字典存在
            parameters = {}
        # case_name = _v['description']  # 接口名称
        if_name = _v['summary']  # 接口名称
        header_dict, body_dict = self.retrieve_params(parameters)  # 处理接口参数，拼成dict形式
        if body_dict[0] and parameters != {}:  # 单个或多个参数
            interface['name'] = if_name
            _type = 'json'  # 参数获取方式
            interface['method'] = method  # 请求方式
            interface['url'] = api  # 拼接完成接口url
            interface['headers'] = header_dict  # 是否传header
            interface['body'] = body_name
            interface['type'] = _type
            interface['prj_id'] = self.prj_id
            self.interface_params[body_name] = body_dict
        else:  # 不传参数
            _type = 'data'
            interface['name'] = if_name
            interface['method'] = method
            interface['url'] = api
            interface['headers'] = header_dict
            interface['body'] = body_name
            interface['type'] = _type
            interface['prj_id'] = self.prj_id
            self.interface_params[body_name] = body_dict
        return self.interface_params, interface

    def retrieve_params(self, parameters):
        """处理参数，转为dict"""
        header = ''
        body = ''
        for each in parameters:
            if each.get('in') == 'header':
                header += each.get('name')
            elif each.get('in') == 'body':
                body += each.get('name') + '\n'
        header = header.strip('\n')
        body = body.strip('\n')
        header_list = header.split('\n')
        body_list = body.split('\n')
        return header_list, body_list


if __name__ == '__main__':
    AnalysisJson('1', '2').retrieve_data()
