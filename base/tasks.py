# !/usr/bin/python
# coding:utf-8
from __future__ import absolute_import
from EasyTest.celery import app
# from celery import shared_task
import time, logging, os
from common.connectMySql import SqL
from lib.public import DrawPie, remove_logs
from base.models import Plan, Report
from datetime import datetime
from lib.sql_parameter import test_case, get_sign, get_env
from run_this import send_email
from common import readConfig

log = logging.getLogger('log')
sql = SqL()


# @app.task
# def add(x, y):
#     return x + y


# @shared_task
# def hello_world():
#     log.info('运行定时任务！')
#     with open("output.txt", "a") as f:
#         f.write("hello world --->{}".format(time.strftime('%Y-%m-%d %H-%M-%S')))
#         f.write("\n")

@app.task
# @shared_task
def run_plan():
    log.info('run plan------->执行测试计划中<--------------')
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    plan = Plan.objects.filter(is_task=1).all().values()
    log.info('----------------------------------------- {}'.format(plan))
    plan = sql.execute_sql(
        'select bp.environment_id, bp.content,bp.plan_name,bp.plan_id from base_plan as bp where bp.is_task = 1',
        dict_type=True)
    if plan == None:
        log.error('查询定时任务计划为空！')
        return
    plan_id = plan['plan_id']
    env_id = plan['environment_id']
    case_id_list = eval(plan['content'])
    begin_time = time.clock()
    prj_id, env_url, private_key = get_env(env_id)
    sign_type = get_sign(prj_id)
    case_num = len(case_id_list)
    content = []
    pass_num = 0
    fail_num = 0
    error_num = 0
    i = 0
    for case_id in case_id_list:
        case_result = test_case(case_id, env_id, case_id_list, sign_type, private_key, env_url, begin_time)
        content.append(case_result)
    end_time = time.clock()
    totalTime = str(end_time - begin_time) + 's'
    for step in content:
        for s in step['step_list']:
            if s["result"] == "pass":
                pass_num += 1
                i += 1
                s['id'] = i
            if s["result"] == "fail":
                fail_num += 1
                i += 1
                s['id'] = i
            if s["result"] == "error":
                error_num += 1
                i += 1
                s['id'] = i
    pic_name = DrawPie(pass_num, fail_num, error_num)
    report_name = plan['plan_name'] + "-" + str(start_time)
    sql.execute_sql(
        'insert into base_report(report_name,pic_name,totalTime,startTime,content,case_num,pass_num,fail_num,error_num,plan_id,update_time, update_user) values("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}", "{}")'.format(
            report_name,pic_name,totalTime,start_time,str(content).replace('"', "'"), case_num,pass_num,fail_num,
            error_num,plan_id, str(datetime.now()), 'root'))
    sql.execute_sql('update base_plan set make=0, update_time="{}"'.format(datetime.now()))
    if fail_num or error_num:
        # report_file_html = get_new_report_html(report_path)
        # report_file_list.append(report_file_html)
        user = readConfig.user
        # qq邮箱授权码
        pwd = readConfig.pwd
        user_163 = readConfig.user_163
        # 163邮箱授权码
        pwd_163 = readConfig.pwd_163
        # _to = ['1977907603@qq.com', 'liyongfeng@tzx.com.cn']
        _to = readConfig.to
        smtp_service = readConfig.smtp_service
        smtp_service_163 = readConfig.smtp_service_163
        send_email(user, pwd, user_163, pwd_163, _to, smtp_service, smtp_service_163)
    log.info('测试任务执行完成！')

@app.task
# @shared_task
def delete_logs():
    log.info('remove logs------->删除过期日志中<--------------')
    report_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/templates' + '/report'
    # report_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\templates' + '\\report'
    logs_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/' + 'logs'  # 拼接删除目录完整路径
    # logs_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\' + 'logs'  # 拼接删除目录完整路径
    pic_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/media'
    report_num = remove_logs(report_path)
    logs_num = remove_logs(logs_path)
    pic_num = remove_logs(pic_path)
    total_num = report_num + logs_num + pic_num
    if total_num == 0:
        log.info('remove logs------->没有要删除的文件.<--------------')
    else:
        log.info('remove logs------->删除过期日志文件数量：{}<--------------'.format(total_num))
