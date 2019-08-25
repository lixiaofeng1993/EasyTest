#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/5 10:39
# @Author  : lixiaofeng
# @Site    : 
# @File    : swagger.py
# @Software: PyCharm

import requests, logging, json
from lib.processingJson import write_data, get_json

log = logging.getLogger('log')  # 初始化log


class AnalysisJson:
    """swagger自动生成测试用例"""

    def __init__(self, prj_id, url):
        self.prj_id = prj_id
        self.url = url
        self.interface = {}
        self.interface_list = []

    def retrieve_data(self):
        """
        主函数
        :return:
        """
        try:
            r = requests.get(self.url + '/v2/api-docs?group=sign-api').json()
            # write_data(r, 'data.json')
            # r = get_json('D:\EasyTest\data.json')
        except Exception as e:
            log.error('请求swagger url 发生错误. 详情原因: {}'.format(e))
            return 'error'
        self.data = r['paths']  # 接口数据
        self.definitions = r['definitions']  # body参数
        if isinstance(self.data, dict):
            for key, value in self.data.items():
                for method in list(value.keys()):
                    params = value[method]
                    if not params['deprecated']:  # 接口是否被弃用
                        params_key = key.replace('/', '_') + '_' + method
                        interface = self.retrieve_params(params, params_key, method, key)
                        self.interface[params_key] = interface
                    else:
                        log.info('interface path: {}, if name: {}, is deprecated.'.format(key, params['description']))
                        break
            log.info(self.interface)
            return self.interface
        else:
            log.error('解析接口数据异常！url 返回值 paths 中不是字典.')
            return 'error'

    def retrieve_params(self, params, params_key, method, key):
        """
        解析json，把每个接口数据都加入到一个字典中
        :param params:
        :param params_key:
        :param method:
        :param key:
        :return:
        """
        interface = {'tags': ''}
        query_dict = {}
        path_dict = {}
        header_dict = {}
        params_dict = {'header': {}, 'body': {}}
        params_dict['body'][params_key] = {}
        parameters = params.get('parameters')  # 未解析的参数字典
        if not parameters:  # 确保参数字典存在
            parameters = {}
        for each in parameters:
            if each.get('in') == 'body':  # body 和 query 不会同时出现
                schema = each.get('schema').get('$ref')
                if schema:
                    param_key = schema.split('/')[-1]
                    param = self.definitions[param_key]['properties']
                    params_dict['body'][params_key] = param
            elif each.get('in') == 'query':
                name = each.get('name')
                del each['name'], each['in']
                query_dict[name] = json.dumps(each).replace('false', 'False').replace('true', 'True').replace('null', 'None')
                params_dict['body'][params_key] = query_dict
        for each in parameters:
            if each.get('in') == 'path':
                name = each.get('name')
                del each['name'], each['in']
                path_dict[name] = json.dumps(each).replace('false', 'False').replace('true', 'True').replace('null', 'None')
                params_dict['body'][params_key].update(path_dict)
            if each.get('in') == 'header':
                name = each.get('name')
                del each['name'], each['in']
                header_dict[name] = json.dumps(each).replace('false', 'False').replace('true', 'True').replace('null', 'None')
                params_dict['header'][params_key] = header_dict
        if isinstance(params['tags'], list):
            for tag in params['tags']:
                interface['tags'] += tag
        interface['name'] = params['summary']
        interface['method'] = method  # 请求方式
        interface['url'] = key  # 拼接完成接口url
        if params_dict['header']:
            interface['headers'] = params_dict['header'][params_key]  # 是否传header
        else:
            interface['headers'] = ''
        if params_dict['body']:
            interface['body'] = params_dict['body'][params_key]
        else:
            interface['body'] = ''
        if method == 'get':
            interface['type'] = 'data'
        else:
            interface['type'] = 'json'
        interface['prj_id'] = self.prj_id
        return interface


if __name__ == '__main__':
    AnalysisJson('1', '2').retrieve_data()
