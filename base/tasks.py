# !/usr/bin/python
# coding:utf-8

from __future__ import absolute_import, unicode_literals
import django

django.setup()
from EasyTest.celery import app
from celery import shared_task
import time, os, json
from lib.public import DrawPie, remove_logs
from django.conf import settings
from base.models import Plan, Report, User
from lib.execute import Test_execute
from lib.send_email import send_email
from httprunner.api import logger
from datetime import datetime


@shared_task
def test_httprunner(env_id, case_id_list, plan="", username="root"):
    logger.log_info('test_httprunner------->HttpRunner执行测试计划中<--------------')
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    begin_time = time.clock()
    case_num = len(case_id_list)
    content = []
    j = 0
    execute = Test_execute(env_id, case_id_list, run_mode="1", plan=plan)
    case_result = execute.test_case
    report_path = case_result['report_path']
    for i in range(len(case_result['summary']['details'])):
        for records in case_result['summary']['details'][i]['records']:
            j += 1
            records['id'] = j
            for data in records.get('meta_datas', {}).get('data', {}):
                body = json.dumps(data.get('request', {}).get('body', {}), ensure_ascii=False).replace(
                    'Markup', '').replace('&#34;', '')
                if body:
                    import urllib.parse
                    data['request']['body'] = urllib.parse.unquote(
                        body.encode('utf-8').decode('unicode_escape').encode(
                            'utf-8').decode('unicode_escape'))
    content.append(case_result)
    summary = case_result.get('summary', {})
    stat = summary.get('stat', {}).get('teststeps', {})
    pass_num = stat.get('successes', 0)
    fail_num = stat.get('failures', 0)
    error_num = stat.get('errors', 0)
    end_time = time.clock()
    totalTime = str(end_time - begin_time)[:6] + ' s'
    pic_name = DrawPie(pass_num, fail_num, error_num)
    report_name = plan.plan_name + "-" + str(start_time).replace(':', '-')
    report = Report(plan_id=plan.plan_id, report_name=report_name, content=content, case_num=case_num,
                    pass_num=pass_num, fail_num=fail_num, error_num=error_num, pic_name=pic_name,
                    totalTime=totalTime, startTime=start_time, update_user=username, make=1, report_path=report_path)
    report.save()
    if fail_num or error_num:
        _to = []
        user = User.objects.filter(is_superuser=1).filter(is_staff=1).filter(is_active=1).values()
        for u in user:
            _to.append(u['email'])
        if _to:
            title = plan.plan_name
            report_id = Report.objects.get(report_name=report_name).report_id
            send_email(_to=_to, title=title, report_id=report_id)
        else:
            logger.log_warning('收件人邮箱为空，无法发送邮件！请在 EasyTeat接口测试平台 - 用户管理 模块中设置.')
    logger.log_info('HttpRunner执行测试计划完成！')


@shared_task
def test_plan(env_id, case_id_list, plan="", username="root"):
    logger.log_info('test_plan------->默认方式执行测试计划中<--------------')
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    begin_time = time.clock()
    case_num = len(case_id_list)
    content = []
    pass_num = 0
    fail_num = 0
    error_num = 0
    i = 0
    for case_id in case_id_list:
        execute = Test_execute(env_id, case_id_list, case_id=case_id, run_mode="0")
        case_result = execute.test_case
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
    report_name = plan.plan_name + "-" + str(start_time)
    report = Report(plan_id=plan.plan_id, report_name=report_name, content=content, case_num=case_num,
                    pass_num=pass_num, fail_num=fail_num, error_num=error_num, pic_name=pic_name,
                    totalTime=totalTime, startTime=start_time, update_user='root', make=0)
    report.save()
    Plan.objects.filter(plan_id=plan.plan_id).update(update_user=username, update_time=datetime.now())
    if fail_num or error_num:
        _to = []
        user = User.objects.filter(is_superuser=1).filter(is_staff=1).filter(is_active=1).values()
        for u in user:
            _to.append(u['email'])
        if _to:
            title = plan.plan_name
            report_id = Report.objects.get(report_name=report_name).report_id
            send_email(_to=_to, title=title, report_id=report_id)
        else:
            logger.log_warning('收件人邮箱为空，无法发送邮件！请在 EasyTeat接口测试平台 - 用户管理 模块中设置.')
    logger.log_info('默认方式测试计划执行完成！')


@app.task
def run_plan(task_name=""):
    logger.log_info('run plan------->执行定时任务中<--------------')
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        plan = Plan.objects.get(is_task=1)
    except Plan.DoesNotExist:
        logger.log_error('查询定时任务计划为空！')
        return
    env_id = plan.environment_id
    case_id_list = eval(plan.content)
    begin_time = time.clock()
    case_num = len(case_id_list)
    content = []
    j = 0
    execute = Test_execute(env_id, case_id_list, run_mode="1", plan=plan)
    case_result = execute.test_case
    report_path = case_result['report_path']
    for i in range(len(case_result['summary']['details'])):
        for records in case_result['summary']['details'][i]['records']:
            j += 1
            records['id'] = j
            for data in records.get('meta_datas', {}).get('data', {}):
                body = json.dumps(data.get('request', {}).get('body', {}), ensure_ascii=False).replace(
                    'Markup', '').replace('&#34;', '')
                if body:
                    import urllib.parse
                    data['request']['body'] = urllib.parse.unquote(
                        body.encode('utf-8').decode('unicode_escape').encode(
                            'utf-8').decode('unicode_escape'))
    content.append(case_result)
    summary = case_result.get('summary', {})
    stat = summary.get('stat', {}).get('teststeps', {})
    pass_num = stat.get('successes', 0)
    fail_num = stat.get('failures', 0)
    error_num = stat.get('errors', 0)
    end_time = time.clock()
    totalTime = str(end_time - begin_time)[:6] + ' s'
    pic_name = DrawPie(pass_num, fail_num, error_num)
    if task_name:
        report_name = task_name + "-" + str(start_time).replace(':', '-')
    else:
        report_name = plan.plan_name + "-" + str(start_time).replace(':', '-')
    report = Report(plan_id=plan.plan_id, report_name=report_name, content=content, case_num=case_num,
                    pass_num=pass_num, fail_num=fail_num, error_num=error_num, pic_name=pic_name,
                    totalTime=totalTime, startTime=start_time, update_user="root", make=1, report_path=report_path)
    report.save()
    if fail_num or error_num:
        _to = []
        user = User.objects.filter(is_superuser=1).filter(is_staff=1).filter(is_active=1).values()
        for u in user:
            _to.append(u['email'])
        if _to:
            title = plan.plan_name
            report_id = Report.objects.get(report_name=report_name).report_id
            send_email(_to=_to, title=title, report_id=report_id)
        else:
            logger.log_warning('收件人邮箱为空，无法发送邮件！请在 EasyTeat接口测试平台 - 用户管理 模块中设置.')
    logger.log_info('HttpRunner执行定时任务完成！')


@app.task
# @shared_task
def delete_logs():
    logger.log_info('remove logs------->删除过期日志中<--------------')
    ubuntu_path = '/var/test_app/EasyTest'
    logs_num1 = 0
    report_num1 = 0
    if os.path.exists(ubuntu_path):
        logs_path1 = os.path.join(ubuntu_path, 'logs')
        report_path1 = os.path.join(ubuntu_path, 'reports')
        logs_num1 = remove_logs(logs_path1)
        report_num1 = remove_logs(report_path1)
    logs_path = os.path.join(os.getcwd(), 'logs')
    report_path = os.path.join(os.getcwd(), 'reports')
    pic_path = os.path.join(settings.MEDIA_ROOT)
    logs_num = remove_logs(logs_path)
    pic_num = remove_logs(pic_path)
    report_num = remove_logs(report_path)
    total_num = logs_num + pic_num + report_num + logs_num1 + report_num1
    if total_num == 0:
        logger.log_info('remove logs------->没有要删除的文件.<--------------')
    else:
        logger.log_info('remove logs------->删除过期日志文件数量：{}<--------------'.format(total_num))


@app.task
# @shared_task
def stop_locust():
    logger.log_info('stop locust------->停止locust服务<--------------')
    os.system("/home/lixiaofeng/./stop_locust.sh")
    logger.log_info('remove logs------->停止locust完成.<--------------')
