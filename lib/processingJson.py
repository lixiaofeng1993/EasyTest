import json
import os, logging
# from common.connectDB import SqL
from jsonpath_rw import jsonpath, parse

log = logging.getLogger('log')  # 初始化log
# sql = SqL()
# windows
sql_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\data' + '\\data.json'  # params json file
res_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\data' + '\\res.json'  # headers json file
rely_on_path = os.path.abspath(
    os.path.dirname(os.path.dirname(__file__))) + '\\data' + '\\rely_on.json'  # 临时文件，存接口返回的参数


# linux
# json_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/data' + '/data.json'

def get_json(path, field=''):
    """获取json文件中的值，data.json和res.json可共用"""
    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        if field:
            data = json_data.get(field)
            return data
        else:
            return json_data


def analysis_json(res, filed):
    """解析请求返回的json数据，返回依赖的字段和值组成的字典"""
    if isinstance(res, dict):
        if filed:
            jsonpath_expr = parse(filed)
            male = jsonpath_expr.find(res)
            value_list = [match.value for match in male]
            for value in value_list:
                data_dict = {filed: value}
                return data_dict
        else:
            log.error('{}传入字段异常！'.format(analysis_json.__name__))
    else:
        log.error('{} 参数不是字典类型'.format(analysis_json.__name__))


def write_body(res, field):
    """请求返回值写入data.json中，在body参数中使用。data.json中要提前写入需要的字段，然后用从返回值中提取的结果替换"""
    if isinstance(res, dict):
        if field:
            with open(sql_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                for key in json_data:
                    if isinstance(json_data[key], dict):
                        for k in json_data[key]:
                            if k == field:
                                json_data[key][field] = res[field]
                                with open(sql_path, 'w', encoding='utf-8') as fp:
                                    fp.write(str(json_data).replace("'", '"'))
                                log.info('请求返回值写入json成功！field ==> {}'.format(field))
        else:
            log.error('{}传入字段异常！'.format(analysis_json.__name__))
    else:
        log.error('{} 参数不是字典类型'.format(write_body.__name__))


def write_data(res, json_path):
    """把处理后的参数写入json文件"""
    if isinstance(res, dict):
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=4)
            log.info('Interface Params Total：{} ,write to json file successfully!\n'.format(len(res)))
    else:
        log.info('{} Params is not dict.\n'.format(write_data.__name__))


if __name__ == '__main__':
    # body = get_json(json_path, 'registered_member')
    # print(body)
    # for k, v in body.items():
    #     print(k,v)
    # data = {'uid': 99, 'ukey': 'bef0246cb2059d90c5e4af8accdf4429'}
    # write_headers(data)
    data = get_json(res_path)
    print(data)
