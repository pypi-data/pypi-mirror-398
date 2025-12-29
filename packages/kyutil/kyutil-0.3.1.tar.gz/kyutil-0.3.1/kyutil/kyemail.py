#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""release_mail.py"""
import lzma
import os
import shutil
import smtplib
from email import encoders
from email.header import Header, make_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logzero

SCALE = 1024
MAX_SIZE = 20


class EmailBase(object):
    """EmailBase(object)"""

    def __init__(self, **kwargs):
        """设置邮件默认值"""
        self.cc = ["825477418@qq.com"]
        self.sender = kwargs.get("sender")
        self.receivers = ['xxx@kylinos.cn', 'xxx1@kylinos.cn']
        self.passwd = kwargs.get("passwd")
        self.subject = kwargs.get("subject")  # '集成构建平台预约构建结果通知'
        self.context = '详情如下'
        self.msg = None
        self.log_file_list = ['/var/log/messages', '/opt/cve_manager/backend_code/cve_server_api.runlog']
        self.logger = kwargs.get("logger", logzero.logger)
        self.smtp_ip = kwargs.get("SMTP_IP")
        self.smtp_port = kwargs.get("SMTP_PORT", 465)

    def set_receivers(self, receive_list):
        self.receivers = receive_list

    def set_cc(self, cc_list):
        self.cc = cc_list

    def set_subject(self, subject):
        self.subject = subject

    def set_context(self, context):
        self.context = context

    def set_xz_file(self, tar_name, filename):
        with open(filename, 'rb') as f:
            with lzma.open(tar_name, 'wb') as output:
                shutil.copyfileobj(f, output)

    def set_text_msg(self):
        """文本email"""
        self.msg = MIMEText(self.context, 'plain', 'utf-8')
        self.msg['From'] = Header(self.sender)
        self.msg['To'] = Header(','.join(self.receivers))
        self.msg['Subject'] = Header(self.subject)
        self.msg['Cc'] = Header(','.join(self.cc))

    def set_html_msg(self, from_=None):
        self.msg = MIMEText(self.context, 'html', 'utf-8')
        self.msg['From'] = Header(from_ or self.sender)
        self.msg['To'] = Header(','.join(self.receivers))
        self.msg['Subject'] = Header(self.subject)
        self.msg['Cc'] = Header(','.join(self.cc))

    def set_attach_msg(self, file_abs_path):
        """邮件发送日志文件。文件大于20M，压缩后发送"""
        self.msg = MIMEMultipart()
        self.msg['From'] = Header(self.sender, 'utf-8')
        self.msg['To'] = Header(','.join(self.receivers), 'utf-8')
        self.msg['Subject'] = Header(self.subject, 'utf-8')
        self.msg['Cc'] = Header(','.join(self.cc), 'utf-8') if self.cc else None
        self.msg.attach(MIMEText(self.context, 'plain', 'utf-8'))

        def attach_file(_file):
            try:
                file_size = os.stat(_file).st_size
                file_name = os.path.basename(_file)
                if file_size > MAX_SIZE * SCALE * SCALE:
                    _file_name = _file + '.xz'
                    self.set_xz_file(_file_name, _file)
                else:
                    _file_name = _file
                att = MIMEBase('application', 'octet-stream')
                att.set_payload(open(_file_name, 'rb').read())
                # 解决中文乱码问题
                att.add_header('Content-Disposition', 'attachment',
                               filename=(make_header([(file_name, 'UTF-8')]).encode('UTF-8')))
                encoders.encode_base64(att)
                self.msg.attach(att)
            except FileNotFoundError:
                self.logger.error("attach file <%s> failed" % os.path.basename(_file))

        if file_abs_path.endswith("log"):
            for log_file in self.log_file_list:
                attach_file(log_file)
        else:
            attach_file(file_abs_path)

    def send_email(self):
        try:
            smtp_conn = smtplib.SMTP_SSL(host=self.smtp_ip, port=self.smtp_port, timeout=5)
            smtp_conn.login(self.sender, self.passwd)
            smtp_conn.sendmail(self.sender, self.receivers, self.msg.as_string())
            smtp_conn.quit()
        except smtplib.SMTPException as e:
            self.logger.error(f" === send email error: {e}")


class EmailHelper(EmailBase):
    """EmailHelper(EmailBase)"""

    def __int__(self, **kwargs):
        super.__init__(**kwargs)

    def set_email_receiver(self, receiver_list):
        """
        设置邮件接收者
        """
        self.set_receivers(receiver_list)

    def set_email_cc(self, cc_list):
        """
        设置邮件抄送者
        """
        self.set_cc(cc_list)

    def set_email_subject_context(self, subject, context):
        """
        发送邮件前，获取邮箱配置信息
        """
        self.set_context(context)
        self.set_subject(subject)

    def send_text_email(self):
        self.set_text_msg()
        self.send_email()

    def send_html_email(self, from_=None):
        self.set_html_msg(from_=from_)
        self.send_email()

    def send_attach_email(self, attach_path):
        self.set_attach_msg(file_abs_path=attach_path)
        self.send_email()
