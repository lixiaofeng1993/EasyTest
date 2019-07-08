import json
# from common.connectDB import SqL
# import logging
from common.logger import Log

# sql = SqL()
# log = logging.getLogger('log')  # 初始化log
log = Log()  # 初始化log


def get_json(path, field=''):
    """获取json文件中的值，data.json和res.json可共用"""
    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        if field:
            data = json_data.get(field)
            return data
        else:
            return json_data


def write_data(res, json_path):
    """把处理后的参数写入json文件"""
    if isinstance(res, dict) or isinstance(res, list):
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, sort_keys=True, indent=4)
            log.info('Interface Params Total：{} ,write to json file successfully!\n'.format(len(res)))
    else:
        log.info('{} Params is not dict.\n'.format(write_data.__name__))


if __name__ == '__main__':
    pass
