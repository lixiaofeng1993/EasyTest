#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: helper.py
# 说   明: httprunner运行支持文件
# 创建时间: 2020/1/9 21:01
'''
from django.conf import settings
import time, os, platform, json, shutil
from httprunner import logger

BASE_DIR = settings.BASE_DIR
pattern = '/' if platform.system() != 'Windows' else '\\'


def get_file_sorted(file_path):
    """最后修改时间顺序升序排列 os.path.getmtime()->获取文件最后修改时间"""
    dir_list = os.listdir(file_path)
    if not dir_list:
        return False
    else:
        dir_list = sorted(dir_list, key=lambda x: os.path.getmtime(os.path.join(file_path, x)))
        return dir_list


def delete_testcase(file_path):
    """
    清理产生的测试文件和报告
    :param file_path:
    :return:
    """
    if os.path.exists(file_path):
        dir_list = get_file_sorted(file_path)
        if len(dir_list) > 4:
            dir_list = dir_list[0:-4]
            for d in dir_list:
                d_path = os.path.join(file_path, d)
                if os.path.isdir(d_path):
                    try:
                        shutil.rmtree(d_path)
                    except PermissionError as e:
                        logger.log_error('权限错误，删除日志文件失败！{}'.format(d_path))
                elif os.path.isfile(d_path):
                    try:
                        print(d_path, 3333333333333)
                        os.remove(d_path)
                    except PermissionError as e:
                        logger.log_error('权限错误，删除日志文件失败！{}'.format(d_path))
    else:
        logger.log_info("要删除的目录不存在！")


def get_time_stamp():
    """当前时间"""
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d-%H-%M-%S", local_time)
    data_secs = (ct - int(ct)) * 1000
    time_stamp = "%s-%03d" % (data_head, data_secs)
    return time_stamp


def check_path(path):
    """路径是否存在"""
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_json(path, field=''):
    """
    获取json文件中的值，data.json和res.json可共用
    :param path:
    :param field:
    :return:
    """
    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        if field:
            data = json_data.get(field)
            return data
        else:
            return json_data


def write_data(res, json_path):
    """
    把处理后的参数写入json文件
    :param res:
    :param json_path:
    :return:
    """
    if isinstance(res, dict) or isinstance(res, list):
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, sort_keys=True, indent=4)
            logger.log_info(
                'Interface Params Total：{} ,write to json file successfully! {}\n'.format(len(res), json_path))
    elif isinstance(res, str):
        with open(json_path, "w", encoding='utf-8') as f:
            f.write(res)
    else:
        logger.log_error('{} Params is not dict.\n'.format(write_data.__name__))


def copy_debugtalk(path, project_id):
    """复制写入debugtalk.py参数化函数"""
    from base.models import DebugTalk
    debugtalk_path = os.path.join(BASE_DIR, "lib/" + "debugtalk.py")
    try:
        debugtalk = DebugTalk.objects.get(belong_project_id=project_id).debugtalk
    except DebugTalk.DoesNotExist:
        debugtalk = ''
    write_data(debugtalk, debugtalk_path)
    if os.path.exists(debugtalk_path):
        with open(debugtalk_path, "rb") as f:
            info = f.read()
            with open(path, "wb") as f:
                f.write(info)
    else:
        with open(path, "w") as f:
            f.write("")
