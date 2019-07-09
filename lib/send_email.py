#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: send_email.py
# 说   明: 
# 创建时间: 2019/7/8 22:53
'''
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

# from lib import readConfig

log = logging.getLogger('log')


def send_email(_to, title, report_id):
    """发送邮件"""
    smtp_service = 'smtp.qq.com'
    user = '954274592@qq.com'
    pwd = 'hlymvkoqcukvbdif'

    msg = MIMEMultipart()
    msg['Subject'] = title + ' 执行报告'
    msg['from'] = Header("EasyTest接口测试平台", 'utf-8')
    msg['to'] = "tester"
    msg["Accept-Language"] = "zh-CN"
    msg["Accept-Charset"] = "ISO-8859-1,utf-8"
    # 邮件正文
    body = MIMEText(
        '{} 执行出现异常，请查看执行详情：http://39.105.136.231/base/report/?report_id={} <测试报告地址>；'.format(title, report_id), 'plain',
        'utf-8')
    msg.attach(body)
    log.info('写入邮件正文')
    i = 0
    while True:
        try:
            s = smtplib.SMTP_SSL(smtp_service)
            s.login(user, pwd)
            s.sendmail(user, _to, msg.as_string())
            s.quit()
            log.info('{} 账号邮件发送成功！请通知相关人员 {} 查收。\n'.format(user, _to))
            break
        except smtplib.SMTPException as e:
            i += 1
            log.info('{} 账号邮件发送失败！第 {} 次尝试中...\n'.format(user, i))
            if i >= 2:
                break
