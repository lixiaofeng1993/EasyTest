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
        self.http = {"config": {"name": "", "base_url": "", "variables": {}, "output": []},
                     "testcases": [{"teststeps": []}]}

        self.data_list = step_info

    def splicing_api(self):

        for data in self.data_list:
            self.http_test = {"name": "", "output": [], "variables": {}, "request": {}, "extract": [], "validate": []}
            self.http_test_request = {"url": "", "method": "", "headers": {}, "params": {}}
            url = data.get('base_url', '') + data['url']
            method = data.get('method')
            self.http_test_request['url'] = url
            self.http_test_request['method'] = method
            if method in ['post', 'put']:
                if data['data_type'] == 'json':
                    self.http_test_request['json'] = data.get('body', '')
                elif data['data_type'] == 'data':
                    self.http_test_request['data'] = data.get('body', '')
            elif method in ['get', 'delete']:
                if data['data_type'] == 'json':
                    self.http_test_request['json'] = data.get('body', '')
                else:
                    self.http_test_request['params'] = data.get('body', '')
            self.http_test_request['headers'] = data.get('header', '')
            self.http_test['request'].update(self.http_test_request)
            self.http_test['name'] = data.get('if_name')
            validators = data.get('validators', [])
            check_point = {}
            for validator in validators:
                check_point[validator.get('comparator')] = ['content.' + validator.get('check', ''),
                                                            validator.get('expect', '')]
                self.http_test['validate'].append(check_point)
            extract = data.get('extract', {})

            if extract:
                extract_dict = {}
                for k, v in extract.items():
                    extract_dict[k] = 'content.' + v
                self.http_test['extract'].append(extract_dict)
            self.http['testcases'][0]['teststeps'].append(self.http_test)
        return self.http
