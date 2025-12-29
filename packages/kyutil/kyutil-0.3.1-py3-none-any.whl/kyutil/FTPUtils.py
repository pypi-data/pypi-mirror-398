# -*- coding: UTF-8 -*-
"""FTPUtils.py"""
import ftplib
import os
import ssl
import traceback

from celery import states
from logzero import logger


class ReusedSslSocket(ssl.SSLSocket):
    def unwrap(self):
        pass


# MyFTP_TLS is derived to support TLS_RESUME(filezilla server)
class MyFtpTLS(ftplib.FTP_TLS):
    """Explicit FTPS, with shared TLS session"""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session)

            conn.__class__ = ReusedSslSocket

        return conn, size


MSG_FTP_CONNECT_SUCCESS = "FTP链接成功！"
MSG_FTP_CONNECT_FAILED = "FTP链接失败！"
MSG_FTP_LOGIN_SUCCESS = "FTP登录成功！"
MSG_FTP_LOGIN_FAILED = "FTP登录失败！"

STOR_CMD = 'STOR '


class FTP(object):
    """FTPUtils(object)"""
    # 上传过程必需参数列表

    celery_task_field = [
        'ftpaddress',  # ftp连接地址
        'ftpport',  # ftp连接端口
        'ftpuser',  # ftp连接用户
        'ftppassword',  # ftp连接密码
        'upload_path',  # ftp上传远端路径
        'isoname',  # 上传的本地iso路径
    ]

    # celery参数
    process_rate_status = 0  # 当前处理的进度，取值从0-100

    def __init__(self, update_status_func, cfg, task_id, logger=logger):
        """
        :param update_status_func:
        :param cfg:
            cfg = {
            'ftpaddress': "server.kylinos.cn",
            'ftpport': "21",
            'ftpuser': "user_name",
            'ftppassword': "***",
            'upload_path': "/vsftpd/os/ISO/HOSTOS/x86_64/2022/06/test",
            'isoname': "/v10-sp1-0518-kx-x86_64-b3532/iso/Kylin-Server-10-SP1-kx.iso",  # 上传的本地iso路径
            }
        :param task_id:
        :param logger:
        """
        self.logger = logger
        # celery状态更新函数以及taskid
        self.call_back_task_process = update_status_func

        # 本地ftp目录 默认上传标志关闭
        self.process_rate_status = 10
        self.celery_task_param = cfg
        self.task_id = task_id
        self.ftp_instance = self.ftp_connect()
        self.log_and_send_task_status("ftp登录成功")

    # log信息输出&日志信息回传&进度设置！
    def log_and_send_task_status(self, msg):
        self.logger.info(f"{msg},【{self.task_id[:4]}】 目前进度{self.process_rate_status}%")
        # 得想办法把logger.info的输出放到msg里面，这样日志信息会携带时间戳等信息
        if self.call_back_task_process is not None:
            if self.process_rate_status == 0:
                self.call_back_task_process(
                    state=states.FAILURE,
                    meta={'current': 0, 'total': 100, 'status': msg, "exc_type": "RuntimeException", "exc_message": msg}
                )
            elif self.process_rate_status == 100:
                self.call_back_task_process(
                    state=states.SUCCESS,
                    meta={'current': 100, 'total': 100, 'status': msg, "exc_type": "RuntimeException", "exc_message": msg}
                )
            else:
                self.call_back_task_process(
                    state=states.STARTED,
                    meta={'current': self.process_rate_status, 'total': 100, 'status': msg, "exc_type": "RuntimeException", "exc_message": msg}
                )

    def ftp_connect(self):
        ftp_address = self.celery_task_param.get('ftpaddress')
        ftp_port = int(self.celery_task_param.get('ftpport'))
        ftp = MyFtpTLS(host=ftp_address, timeout=15)
        ftp.auth()
        ftp.port = ftp_port
        ftp.prot_p()
        ftp.set_pasv(1)
        ftp.encoding = 'utf-8'
        ftp_user = self.celery_task_param.get('ftpuser')
        ftp_password = self.celery_task_param.get('ftppassword')

        try:
            self.process_rate_status = 20
            ftp.connect(ftp_address, ftp_port)
            self.log_and_send_task_status(MSG_FTP_CONNECT_SUCCESS)
        except Exception:
            self.log_and_send_task_status(MSG_FTP_CONNECT_FAILED)
            raise ConnectionError(MSG_FTP_CONNECT_FAILED)
        try:
            self.process_rate_status = 40
            ftp.login(ftp_user, ftp_password)  # user/passwd
            ftp.prot_p()
            self.log_and_send_task_status(MSG_FTP_LOGIN_SUCCESS)
        except Exception:
            traceback.print_exc()
            self.log_and_send_task_status(MSG_FTP_LOGIN_FAILED)
            raise ConnectionError(MSG_FTP_LOGIN_FAILED)
        return ftp

    def is_same_size(self, local_file, remote_file):
        """
        判断远程文件和本地文件大小是否一致

        Args:
            local_file: 本地文件
            remote_file: 远程文件

        Returns:

        """
        try:
            remote_file_size = self.ftp_instance.size(remote_file)
        except Exception as err:
            self.logger.debug("get remote file_size failed, Err:%s" % err)
            remote_file_size = -1

        try:
            local_file_size = os.path.getsize(local_file)
        except Exception as err:
            self.logger.debug("get local file_size failed, Err:%s" % err)
            local_file_size = -1

        result = True if (remote_file_size == local_file_size) else False

        return result, remote_file_size, local_file_size

    def upload_file(self, local_file, remote_file, ftp):
        # 本地是否有此文件
        if not os.path.exists(local_file):
            self.logger.debug('no such file or directory %s.' % local_file)
            return False

        result, remote_file_size, local_file_size = self.is_same_size(local_file, remote_file)
        if not result:
            self.logger.debug('remote_file %s is not exist, now trying to upload...' % remote_file)
            buff_size = 8192
            try:
                with open(local_file, 'rb') as file_handler:
                    if ftp.storbinary(STOR_CMD + remote_file, file_handler, buff_size):
                        result, remote_file_size, local_file_size = self.is_same_size(local_file, remote_file)
            except Exception as err:
                self.logger.debug(
                    'some error happened in storbinary file :%s. Err:%s' % (local_file, err))
                result = False

        self.logger.debug('Upload 【%s】 %s , remote_file_size = %d, local_file_size = %d.' \
                          % (
                              remote_file, 'success' if (result is True) else 'failed', remote_file_size,
                              local_file_size))
        self.logger.info('Upload 【%s】 %s , remote_file_size = %d, local_file_size = %d.' \
                         % (
                             remote_file, 'success' if (result is True) else 'failed', remote_file_size,
                             local_file_size))

    # 01-ftp-connect连接及登录

    # 02-创建远端文件目录
    def create_remote_dir(self, upload_path):
        try:
            self.ftp_instance.cwd(upload_path)
        except Exception as e:
            self.log_and_send_task_status(f"ftp cwd异常：{e}")
            self.ftp_instance.cwd('/')
            # 分割目录名
            base_dir, part_path = self.ftp_instance.pwd(), upload_path.split('/')
            for p in part_path[1:]:
                # 拼接子目录
                base_dir = base_dir + p + '/'
                try:
                    # 尝试切换子目录
                    self.ftp_instance.cwd(base_dir)
                except Exception as e:
                    self.log_and_send_task_status(f"ftp cwd异常：{e}")
                    # 不存在创建当前子目录
                    self.ftp_instance.mkd(base_dir)
        # 确保最后路径修改
        self.ftp_instance.cwd(upload_path)
        return True

    # 03-上传本地指定文件
    def ftp_upload_file(self, root_path_iso_path="/opt/integration_iso_files/") -> str:
        iso_file = self.celery_task_param.get('isoname')
        iso_rename = self.celery_task_param.get('filename_rename')

        buffsize = 1024
        self.ftp_instance.cwd(self.ftp_instance.pwd())

        with open(root_path_iso_path + iso_file, 'rb') as f:
            self.log_and_send_task_status('正在上传' + str(f))
            if iso_rename is not None:
                self.ftp_instance.storbinary(STOR_CMD + iso_rename, f, buffsize)
                remote_file = str(self.ftp_instance.pwd()) + '/' + iso_rename
            else:
                self.ftp_instance.storbinary(STOR_CMD + iso_file.split('/')[-1], f, buffsize)
                remote_file = str(self.ftp_instance.pwd()) + '/' + iso_file.split('/')[-1]
        return remote_file

    def instance_cwd(self, remote_path):
        try:
            self.ftp_instance.cwd(remote_path)  # 切换工作路径
        except Exception as e:
            self.logger.error('Except INFO:', e)
            base_dir, part_path = self.ftp_instance.pwd(), remote_path.split('/')
            for sub_path in part_path:
                # 针对类似  '/home/billing/scripts/zhf/send' 和 'home/billing/scripts/zhf/send' 两种格式的目录
                # 如果第一个分解后的元素是''这种空字符，说明根目录是从/开始，如果最后一个是''这种空字符，说明目录是以/结束
                # 例如 /home/billing/scripts/zhf/send/ 分解后得到 ['', 'home', 'billing', 'scripts', 'zhf', 'send', '']
                # 首位和尾都不是有效名称
                if '' == sub_path:
                    continue
                base_dir = str(os.path.join(base_dir, sub_path))  # base_dir + subpath + '/'  # 拼接子目录
                try:
                    self.ftp_instance.cwd(base_dir)  # 切换到子目录, 不存在则异常
                except Exception as e:
                    self.logger.error('Except INFO:', e)
                    self.logger.error('remote not exist directory %s , create it.' % base_dir)
                    self.ftp_instance.mkd(base_dir)  # 不存在创建当前子目录 直到创建所有
                    continue

    # 03-上传目录
    def upload_file_tree(self, local_path, remote_path, recursively):
        # 创建服务器目录 如果服务器目录不存在 就从当前目录创建目标外层目录
        # 打开该远程目录
        self.instance_cwd(remote_path)

        # 本地目录切换
        try:
            # 远端目录通过ftp对象已经切换到指定目录或创建的指定目录
            file_list = os.listdir(local_path)
            for file_name in file_list:
                if os.path.isdir(os.path.join(local_path, file_name)):
                    self.logger.debug('%s is a directory...' % file_name)
                    if recursively:  # 递归目录上传
                        # 创建相关的子目录 创建不成功则目录已存在
                        try:
                            cwd = self.ftp_instance.pwd()
                            self.ftp_instance.cwd(file_name)  # 如果cwd成功 则表示该目录存在 退出到上一级
                            self.ftp_instance.cwd(cwd)
                        except Exception as e:
                            self.logger.error(
                                'check remote directory %s not eixst, now trying to create it! Except INFO:%s.' % (
                                    file_name, e))
                            self.ftp_instance.mkd(file_name)

                        self.logger.debug('trying to upload directory %s --> %s ...' % (file_name, remote_path))
                        p_local_path = os.path.join(local_path, file_name)
                        p_remote_path = os.path.join(self.ftp_instance.pwd(), file_name)
                        self.upload_file_tree(p_local_path, p_remote_path, recursively)
                        # 对于递归 ftp 每次传输完成后需要切换目录到上一级
                        self.ftp_instance.cwd("..")
                    else:
                        self.logger.debug(
                            'translate mode is UnRecursively, %s is a directory, continue ...' % file_name)
                        continue
                else:
                    # 是文件 直接上传
                    local_file = os.path.join(local_path, file_name)
                    remote_file = os.path.join(remote_path, file_name)
                    self.upload_file(local_file, remote_file, self.ftp_instance)
        except Exception as e:
            traceback.format_exc()
            self.logger.debug(f'FTP 无法上传目录。 错误消息:{e}')

    # 04-核实iso名称
    def ftp_check_iso(self):
        upload_path = self.celery_task_param.get('upload_path')
        iso_file = self.celery_task_param.get('isoname')
        iso_rename = self.celery_task_param.get('filename_rename')

        flist = self.ftp_instance.nlst(upload_path)
        for f in flist:
            if f.endswith('.iso') and f.split('/')[-1] == iso_file.split('/')[-1] or (
                    f.endswith('.iso') and f.split('/')[-1] == iso_rename):
                self.ftp_instance.quit()
                return f
        return None

    # 外部调用ftp主函数入口
    def upload_iso(self, root_path_iso_path="/opt/integration_iso_files/") -> str:
        try:
            self.process_rate_status = 50
            self.create_remote_dir(self.celery_task_param.get('upload_path'))
            self.log_and_send_task_status(
                f'ftp上传路径:{self.celery_task_param.get("ftpaddress")}:{self.ftp_instance.pwd()}')

            self.process_rate_status = 60

            # 是否为空
            if self.ftp_instance.nlst():
                raise RuntimeError("目录不为空，无法上传")

            self.log_and_send_task_status("ftp开始上传本地iso文件")
            isoname = self.celery_task_param.get("isoname")
            if self.celery_task_param.get("is_pungi", False):
                # ftp上传pungi-koji构建的镜像，路径为compose的上一层
                local_dir = root_path_iso_path + isoname[:isoname.rfind("/compose/")]
            else:
                local_dir = root_path_iso_path + isoname[:isoname.rfind("/")]
            self.upload_file_tree(local_dir, self.celery_task_param.get('upload_path'), True)

            self.process_rate_status = 80
            self.log_and_send_task_status("校验ftp远端iso文件")
            if not self.ftp_check_iso():
                self.log_and_send_task_status("ftp上传iso失败")

            self.process_rate_status = 100
            self.log_and_send_task_status("ftp上传iso完成")
            return self.celery_task_param.get('upload_path')
        except Exception as e:
            self.process_rate_status = 0
            self.log_and_send_task_status(f"ftp上传失败！{e}")
        return ""
