import os
import smtplib
import time
import unittest
import importlib, logging
from BeautifulReport import BeautifulReport
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from common.logger import Log
from common import readConfig
from case import test_api
from lib.public import get_new_report_html

log = logging.getLogger('log')


def add_case(case_path):
    """加载所有的测试用例"""
    importlib.reload(test_api)  # 每次执行前重新加载 test_api.py 文件
    discover = unittest.defaultTestLoader.discover(case_path, pattern='test*.py', top_level_dir=None)  # 定义discover方法的参数
    Log().info('测试用例：%s' % discover)
    return discover


def run_case(all_case, report_path):
    """执行所有测试用例，并把结果写入报告"""
    result = BeautifulReport(all_case)
    now = time.strftime('%Y-%m-%d %H-%M-%S')
    result.report(filename=now + 'report.html', description=readConfig.title, report_dir=report_path)
    Log().info('执行用例，生成HTML报告: {}\n'.format(now + 'report.html'))


def send_email(user, pwd, user_163, pwd_163, _to, smtp_service, smtp_service_163, report_file_list=''):
    """发送邮件"""
    make = False
    msg = MIMEMultipart()
    msg['Subject'] = readConfig.title
    msg['from'] = user
    msg['to'] = ';'.join(_to)  # 支持多个收件人
    msg["Accept-Language"] = "zh-CN"
    msg["Accept-Charset"] = "ISO-8859-1,utf-8"
    # 邮件正文
    # part = MIMEText('使用Jenkins第一次自动化测试报告尝试 定时 发送邮件')
    if report_file_list:
        make = True
        for report_file in report_file_list:
            if os.path.splitext(report_file)[1] == '.html':
                mail_body = readConfig.email_text
                body = MIMEText(mail_body, 'html', 'utf-8')
                msg.attach(body)
                Log().info('写入邮件正文')
            att = MIMEText(open(report_file, 'rb').read(), 'base64', 'utf-8')  # 添加多个附件
            att['Content-Type'] = 'application/octet-stream'
            att['Content-Disposition'] = 'attach;filename=' + report_file[-11:]
            msg.attach(att)
        Log().info('添加邮件附件')
    else:
        mail_body = readConfig.email_task
        body = MIMEText(mail_body, 'html', 'utf-8')
        msg.attach(body)
        log.info('写入邮件正文')

    try:
        s = smtplib.SMTP_SSL(smtp_service)
        s.login(user, pwd)
        s.sendmail(user, _to, msg.as_string())
        s.quit()
        if make:
            Log().info('%s账号邮件发送成功！请通知相关人员查收。\n' % user)
        else:
            log.info('%s账号邮件发送成功！请通知相关人员查收。\n' % user)
    except smtplib.SMTPException as e:
        if make:
            Log().info('邮件发送失败的原因是：%s \n' % e)
        else:
            log.info('邮件发送失败的原因是：%s \n' % e)
        try:
            s = smtplib.SMTP()
            s.connect(smtp_service_163)
            s.login(user_163, pwd_163)
            s.sendmail(user_163, _to, msg.as_string())
            s.quit()
            if make:
                Log().info('%s账号邮件发送成功！请通知相关人员查收。\n' % user_163)
            else:
                log.info('%s账号邮件发送成功！请通知相关人员查收。\n' % user_163)
        except smtplib.SMTPException as e:
            if make:
                Log().info('邮件发送失败的原因是：%s \n' % e)
            else:
                log.info('邮件发送失败的原因是：%s \n' % e)


def run_email():
    report_file_list = []
    # 测试用例路径，匹配规则
    case_path = os.path.abspath(os.path.dirname(__file__)) + '/case'
    all_case = add_case(case_path)
    # 生成报告测试路径
    report_path = os.path.abspath(os.path.dirname(__file__)) + '/templates' + '/report'
    if not os.path.exists(report_path): os.mkdir(report_path)  # 创建report目录
    run_case(all_case, report_path)
    # 获取最新的测试报告
    # report_file_html = get_new_report_html(report_path)
    # report_file_list.append(report_file_html)
    # user = readConfig.user
    # # qq邮箱授权码
    # pwd = readConfig.pwd
    # user_163 = readConfig.user_163
    # # 163邮箱授权码
    # pwd_163 = readConfig.pwd_163
    # # _to = ['1977907603@qq.com', 'liyongfeng@tzx.com.cn']
    # _to = readConfig.to
    # smtp_service = readConfig.smtp_service
    # smtp_service_163 = readConfig.smtp_service_163
    # send_email(user, pwd, user_163, pwd_163, _to, smtp_service, smtp_service_163, report_file_list)


if __name__ == '__main__':
    # run_email()
    import requests

    data = {
        "gender": 1,
        "headimg": "https://coursecdn.xxbmm.com/xxbmm-course-image/2019/06/03/17/d65c1319-29bc-40f7-b6aa-de400258879f.jpg",
        "nickname": "除却巫山不是云",
        "openid": "ocIIn4934mT7ZtqsbK8rKa2QLiaY",
        "source": "APPLET",
        "unionid": "oPmunjvnN9uIP-xEdZTUnj-e3KrI"
    }
    res = requests.post(url='https://course.rest.xxbmm.com/ops', json=data, verify=False)
    print(res.text)
