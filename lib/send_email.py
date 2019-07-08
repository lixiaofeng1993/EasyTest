#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: send_email.py
# 说   明: 
# 创建时间: 2019/7/8 22:53
'''
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# from lib import readConfig

log = logging.getLogger('log')


def send_email(user, pwd, user_163, pwd_163, _to, smtp_service, smtp_service_163, title, email_text, email_task,
               report_file_list=''):
    """发送邮件"""
    make = False
    msg = MIMEMultipart()
    msg['Subject'] = title
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
                mail_body = email_text
                body = MIMEText(mail_body, 'html', 'utf-8')
                msg.attach(body)
                log.info('写入邮件正文')
            att = MIMEText(open(report_file, 'rb').read(), 'base64', 'utf-8')  # 添加多个附件
            att['Content-Type'] = 'application/octet-stream'
            att['Content-Disposition'] = 'attach;filename=' + report_file[-11:]
            msg.attach(att)
        log.info('添加邮件附件')
    else:
        mail_body = email_task
        body = MIMEText(mail_body, 'html', 'utf-8')
        msg.attach(body)
        log.info('写入邮件正文')

    try:
        s = smtplib.SMTP_SSL(smtp_service)
        s.login(user, pwd)
        s.sendmail(user, _to, msg.as_string())
        s.quit()
        if make:
            log.info('%s账号邮件发送成功！请通知相关人员查收。\n' % user)
        else:
            log.info('%s账号邮件发送成功！请通知相关人员查收。\n' % user)
    except smtplib.SMTPException as e:
        if make:
            log.info('邮件发送失败的原因是：%s \n' % e)
        else:
            log.info('邮件发送失败的原因是：%s \n' % e)
        try:
            s = smtplib.SMTP()
            s.connect(smtp_service_163)
            s.login(user_163, pwd_163)
            s.sendmail(user_163, _to, msg.as_string())
            s.quit()
            if make:
                log.info('%s账号邮件发送成功！请通知相关人员查收。\n' % user_163)
            else:
                log.info('%s账号邮件发送成功！请通知相关人员查收。\n' % user_163)
        except smtplib.SMTPException as e:
            if make:
                log.info('邮件发送失败的原因是：%s \n' % e)
            else:
                log.info('邮件发送失败的原因是：%s \n' % e)
