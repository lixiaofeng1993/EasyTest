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
    # import requests
    #
    # he = {
    #     "Accept": "application/json;charset=UTF-8",
    #     "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjE2MzM2MTk1OTAsImV4cGlyZVRpbWUiOjE1NjI5Mjk2MTk1OTAsImlkZW50aWZ5IjoyMTg0NH0.knX1auEN4crYkmzAXYjUHaalYQzlRzV6dqo3SsMxw3A"
    # }
    # data = {
    #     "headimg": "https://coursecdn.xxbmm.com/xxbmm-course-image/2019/06/27/18/827f6d30-5af2-4f5b-9483-f752dea00541.jpg",
    #     "birthday": "2019-01-22",
    #     "gender": "MAN",
    #     "name": "张三"}
    # # ss = {
    # #     "birthday": "2019-01-22",
    # #     "gender": "MAN",
    # #     "headimg": "head.jpg",
    # #     "name": "张三"
    # # }
    # res = requests.post(url='https://course.rest.xxbmm.com/babys', json=data, headers=he, verify=False)
    # print(res.text)
    import urllib.request
    import urllib.parse
    import json

    # appid = 'wx506830910cbd77e9'
    # appsecret = 'e0e5d5ed1d507103f73d6667eef00d7a'
    appid = 'wx5767473a100552ea'
    appsecret = 'bEX44UJ4EBz6ibkWhQVX0ywdccjC60us1X9JmqEgICR'


    # 获取TOKEN
    def getToken(appid, appsecret):
        # 这个是微信获取小程序码的接口
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}'.format(
            appid=appid, appsecret=appsecret)
        # 准备一下头
        headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }

        request = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request)
        readData = response.read()
        readData = readData.decode('utf-8')
        obj = json.loads(readData)
        print(obj)
        print(obj['access_token'])
        return obj['access_token']


    # 获取小程序码
    def getACodeImage(token, file):
        # 这个是微信获取小程序码的接口
        url = 'https://api.weixin.qq.com/wxa/getwxacode?access_token={token}'.format(token=token)
        # 准备一下头
        headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        # 用Post传值，这里值用JSON的形式
        values = {"path": "?from=1"}
        # 将字典格式化成能用的形式,urlencode不能用
        # data = urllib.parse.urlencode(values).encode('utf-8')
        # 使用json.dumps的方式序列化为字符串，然后bytes进行编码
        data = json.dumps(values)
        data = bytes(data, 'utf8')
        # 创建一个request,放入我们的地址、数据、头
        request = urllib.request.Request(url, data, headers)
        # 将获取的数据存在本地文件
        readData = urllib.request.urlopen(request).read()
        f = open(file, "wb")
        f.write(readData)
        f.close()


    token = getToken(appid, appsecret)
    getACodeImage(token, 'wxCode.jpg')
