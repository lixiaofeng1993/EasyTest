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
from base.models import User
from lib import readConfig

# from lib import readConfig

log = logging.getLogger('log')


def send_email(title, report_id='', register=False):
    """
    发送邮件
    :param title:
    :param report_id:
    :param register:
    :return:
    """
    smtp_service = 'smtp.qq.com'
    user = readConfig.email_user
    pwd = readConfig.email_pwd

    _to = []
    user_ = User.objects.filter(is_superuser=1).filter(is_staff=1).filter(is_active=1).values()
    for u in user_:
        _to.append(u['email'])
    if not _to:
        log.error('收件人邮箱为空，无法发送邮件！请在 EasyTeat接口测试平台 - 用户管理 模块中设置.')
        return

    msg = MIMEMultipart()
    msg['Subject'] = title + ' 执行报告'
    msg['from'] = Header("EasyTest接口测试平台", 'utf-8')
    msg['to'] = "tester"
    msg["Accept-Language"] = "zh-CN"
    msg["Accept-Charset"] = "ISO-8859-1,utf-8"
    # 邮件正文
    if register:
        body = MIMEText(
            '用户： {} 登录并注册成功！'.format(report_id), 'plain', 'utf-8')
    else:
        body = MIMEText(
            '{} 执行出现异常，请查看执行详情：http://www.easytest.xyz/base/report/?report_id={} <测试报告地址>；'.format(title, report_id),
            'plain', 'utf-8')
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
