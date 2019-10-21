#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: httprunner_execute.py
# 说   明: 
# 创建时间: 2019/10/20 15:13
'''


class HttpRunerMain:
    def __init__(self, step_info):
        self.http_test = {"name": "", "output": [], "variables": {}, "request": {}, "extract": [], "validate": []}
        self.http_test_request = {"url": "", "method": "", "headers": {}, "params": {}}
        self.data = step_info

    def splicing_api(self):
        url = self.data.get('base_url', '') + self.data['url']
        method = self.data.get('method')
        self.http_test_request['url'] = url
        self.http_test_request['method'] = method
        if method in ['post', 'put']:
            if self.data['data_type'] == 'json':
                self.http_test_request['json'] = self.data.get('body', '')
            elif self.data['data_type'] == 'data':
                self.http_test_request['data'] = self.data.get('body', '')
        elif method in ['get', 'delete']:
            if self.data['data_type'] == 'json':
                self.http_test_request['json'] = self.data.get('body', '')
            else:
                self.http_test_request['params'] = self.data.get('body', '')
        self.http_test_request['headers'] = self.data.get('header', '')
        self.http_test['request'].update(self.http_test_request)
        self.http_test['name'] = self.data.get('if_name')
        validators = self.data.get('validators', [])
        check_point = {}
        for validator in validators:
            check_point[validator.get('comparator')] = ['content.' + validator.get('check', ''),
                                                        validator.get('expect', '')]
            self.http_test['validate'].append(check_point)
        extract = self.data.get('extract', {})

        if extract:
            extract_dict = {}
            for k, v in extract.items():
                extract_dict[k] = 'content.' + v
            self.http_test['extract'].append(extract_dict)

        return self.http_test
