#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: httprunner_execute.py
# 说   明: 
# 创建时间: 2019/10/20 15:13
'''
from lib.public import str_number
from lib.helper import *
import os, re, time


class HttpRunerMain:
    def __init__(self, step_info, locust=False):
        self.case_name_list = []
        self.data_list = step_info
        self.locust = locust
        self.project_id = 0

    @property
    def splicing_api(self):
        for data in self.data_list:
            case_name = data.get("case_name", "")
            self.project_id = data.get("project_id", 0)
            if case_name:
                self.case_name_list.append(case_name)
            else:
                raise ValueError("case_id打印为0！")

        if self.locust:
            testcase_dir = check_path(os.path.join(BASE_DIR, "performance"))
            testsuites_dir = check_path(os.path.join(testcase_dir, "testsuites"))
            testcases_dir = check_path(os.path.join(testcase_dir, "testcases"))
            api_dir = check_path(os.path.join(testcase_dir, "api"))
            debugtalk_path = os.path.join(testcase_dir, "debugtalk.py")
            copy_debugtalk(debugtalk_path, self.project_id)
        else:
            testcase_dir = os.path.join(BASE_DIR, "testcase")
            delete_testcase(testcase_dir)
            report_path = os.path.join(BASE_DIR, "reports")
            delete_testcase(report_path)
            logs_path = os.path.join(BASE_DIR, "logs")
            delete_testcase(logs_path)
            logs_path = os.path.join(BASE_DIR, "media")
            delete_testcase(logs_path)
            testcase_dir_path = os.path.join(testcase_dir, get_time_stamp())
            testsuites_dir = check_path(os.path.join(testcase_dir_path, "testsuites"))
            testcases_dir = check_path(os.path.join(testcase_dir_path, "testcases"))
            api_dir = check_path(os.path.join(testcase_dir_path, "api"))
            debugtalk_path = os.path.join(testcase_dir_path, "debugtalk.py")
            copy_debugtalk(debugtalk_path, self.project_id)

        testsuites_json = {
            "config": {
                "base_url": "",
                "name": "",
                "variables": {}
            },
            "noReset": True,
            "testcases": [

            ]
        }

        self.case_name_list = list(set(self.case_name_list))
        for _case_name in self.case_name_list:
            testcases_json = {
                "config": {
                    "base_url": "",
                    "name": "",
                    "variables": {}
                },
                "noReset": True,
                "teststeps": [
                ]
            }
            for data in self.data_list:
                # tsetsuites
                self.testcases = {
                    "name": "",
                    "testcase": "",
                    "parameters": [],
                    "variables": {}
                }
                self.teststeps = {
                    "api": "",
                    "extract": [],
                    "name": "",
                    "skip": "",
                    "output": [],
                    "validate": [],
                    "variables": {}
                }
                base_url = data.get("url", "")
                # api = data.get("url", "")
                method = data.get('method', "")
                plan_name = data.get("plan_name", "")
                case_name = data.get("case_name", "")
                weight = data.get("weight", 1)
                if_name = data.get("if_name", "")
                skip = data.get("skip", "")
                testsuites_json["config"]["base_url"] = base_url
                if plan_name:
                    testsuites_json["config"]["name"] = plan_name
                else:
                    testsuites_json["config"]["name"] = case_name
                self.testcases["name"] = case_name
                self.testcases["weight"] = weight
                self.testcases["testcase"] = "testcases/" + case_name + '.json'
                # body = data.get("body", {})
                # if body:
                #     for key, value in body.items():
                #         if "list(" in str(value):
                #             patt = re.compile("list\((.+)\)")
                #             params = patt.findall(value)[0]  # TODO:parameters和官方文档存在差距，待修改
                #             if "$" in params:
                #                 self.testcases["parameters"].append({key: params})
                #             else:
                #                 params_list = params.split(',')
                #                 self.testcases["parameters"].append({key: params_list})
                #             data["body"][key] = "$" + key
                parameters = data.get("parameters", [])
                if parameters:
                    for parameter in parameters:
                        for key, value in parameter.items():
                            if "list(" in str(value):
                                patt = re.compile("list\((.+)\)")
                                params = patt.findall(value)[0]
                                params_list = params.split(',')
                                self.testcases["parameters"].append({key: params_list})
                            else:
                                self.testcases["parameters"].append({key: value})

                if case_name not in str(testsuites_json["testcases"]):
                    testsuites_json["testcases"].append(self.testcases)

                # tsetcases
                testcases_json["config"]["base_url"] = base_url
                testcases_json["config"]["name"] = case_name

                self.teststeps["name"] = if_name
                self.teststeps["skip"] = skip
                self.teststeps["api"] = "api/" + case_name + "/" + if_name + ".json"
                extract = data.get('extract', {})
                if extract:
                    for k, v in extract.items():
                        extract_dict = {}
                        extract_dict[k] = 'content.' + v
                        self.teststeps["extract"].append(extract_dict)

                if_name_list = []
                for step in testcases_json["teststeps"]:
                    if_name_list.append(step["name"])
                if if_name not in if_name_list and _case_name == case_name:
                    testcases_json["teststeps"].append(self.teststeps)

                # api
                if _case_name == case_name:
                    api_json = {
                        "name": "",
                        "noReset": True,
                        "output": [],
                        "request": {
                            "headers": {},
                            "json": {},
                            "method": "",
                            "url": ""
                        },
                        "validate": [],
                        "variables": {}
                    }
                    api_json["name"] = if_name
                    api_json["request"]["url"] = base_url
                    api_json["request"]["method"] = method
                    api_json["request"]["headers"] = data.get("header", {})
                    if method in ['post', 'put']:
                        if data['data_type'] == 'json':
                            api_json["request"]['json'] = data.get('body', '')
                        elif data['data_type'] == 'data':
                            api_json["request"]['data'] = data.get('body', '')
                    elif method in ['get', 'delete']:
                        if data['data_type'] == 'json':
                            api_json["request"]['json'] = data.get('body', '')
                        else:
                            api_json["request"]['params'] = data.get('body', '')
                    validators = data.get('validators', [])
                    for validator in validators:
                        check_point = {}
                        validator = str_number(validator)
                        check_point[validator.get('comparator')] = ['content.' + validator.get('check', ''),
                                                                    validator.get('expect', '')]

                        api_json["validate"].append(check_point)

                    api_json_path_dir = check_path(os.path.join(api_dir, _case_name))
                    api_json_path = os.path.join(api_json_path_dir, if_name + ".json")
                    write_data(api_json, api_json_path)
            testcases_json_path = os.path.join(testcases_dir, _case_name + ".json")
            write_data(testcases_json, testcases_json_path)
        testsuites_json_path = os.path.join(testsuites_dir, testsuites_json["config"]["name"] + ".json")
        write_data(testsuites_json, testsuites_json_path)
        while True:
            if not os.path.exists(testsuites_json_path):
                time.sleep(1)
                continue
            return testsuites_json_path
