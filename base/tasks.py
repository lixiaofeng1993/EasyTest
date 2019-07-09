# !/usr/bin/python
# coding:utf-8
from __future__ import absolute_import
from EasyTest.celery import app
# from celery import shared_task
import time, logging, os
from lib.public import DrawPie, remove_logs
from base.models import Plan, Report, User
from datetime import datetime
# from lib.sql_parameter import test_case, get_sign, get_env
from lib.execute import Test_execute
from lib.send_email import send_email

log = logging.getLogger('log')


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
    if plan == None:
        log.error('查询定时任务计划为空！')
        return
    plan_id = plan[0]['plan_id']
    env_id = plan[0]['environment_id']
    case_id_list = eval(plan[0]['content'])
    begin_time = time.clock()
    case_num = len(case_id_list)
    content = []
    pass_num = 0
    fail_num = 0
    error_num = 0
    i = 0
    for case_id in case_id_list:
        execute = Test_execute(case_id, env_id, case_id_list)
        case_result = execute.test_case()
        content.append(case_result)
    end_time = time.clock()
    totalTime = str(end_time - begin_time)[:6] + ' s'
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
    report_name = plan[0]['plan_name'] + "-" + str(start_time)
    report = Report(plan_id=plan_id, report_name=report_name, content=content, case_num=case_num,
                    pass_num=pass_num, fail_num=fail_num, error_num=error_num, pic_name=pic_name,
                    totalTime=totalTime, startTime=start_time, update_user='root')
    report.save()
    Plan.objects.filter(plan_id=plan_id).update(make=0, update_time=datetime.now(), update_user='root')
    if fail_num or error_num:
        _to = []
        user = User.objects.filter(is_superuser=1).filter(is_staff=1).filter(is_active=1).values()
        for u in user:
            _to.append(u['email'])
        title = plan[0]['plan_name']
        report_id = Report.objects.get(report_name=report_name).report_id
        send_email(_to=_to, title=title, report_id=report_id)
    log.info('测试任务执行完成！')


@app.task
# @shared_task
def delete_logs():
    log.info('remove logs------->删除过期日志中<--------------')
    logs_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/' + 'logs'  # 拼接删除目录完整路径
    # logs_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\' + 'logs'  # 拼接删除目录完整路径
    pic_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/media'
    logs_num = remove_logs(logs_path)
    pic_num = remove_logs(pic_path)
    total_num = logs_num + pic_num
    if total_num == 0:
        log.info('remove logs------->没有要删除的文件.<--------------')
    else:
        log.info('remove logs------->删除过期日志文件数量：{}<--------------'.format(total_num))
