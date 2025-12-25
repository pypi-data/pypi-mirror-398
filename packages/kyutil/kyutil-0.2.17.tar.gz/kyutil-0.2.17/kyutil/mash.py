# -*- coding: UTF-8 -*-
"""@File ：client koji tag mash synchronous module"""
import os
import shutil
import time
import uuid

from kyutil.celery_util import celery_state_update as _update_celery
from kyutil.config import BUILD_PATH, file_http_mapping, HOST_HTTP, HOST_HTTPS, APACHE_READ_MODEL
from kyutil.download import download_file
from kyutil.exceptions import MashException
from kyutil.file import reset_dirs
from kyutil.http_util import send_request
from kyutil.log import zero_log
from kyutil.shell import run_get_return
from kyutil.url import url_filename


class MashGather:
    """通用mash构建过程主入口"""
    process = 0  # 当前任务进度，取值从0-100

    def __init__(self, update_celery_status, celery_params: dict, task_id: str, **kwargs):
        """初始化Mash相关属性"""
        # celery状态更新
        self._update_celery_func = update_celery_status
        self.task_id = task_id or uuid.uuid4().hex
        self.params = celery_params
        self.suffix = str(kwargs.get("suffix", ""))
        self.suffix = "-" + self.suffix if self.suffix else ""
        self.cur_day = time.strftime('%Y%m%d', time.localtime(time.time()))

        self.tag = self.params.get('tag', '')
        self.day_mash_dir = f"{self.cur_day}/{self.tag.replace('/', '_')}/{self.task_id[0:4]}{self.suffix}"
        self.mash_des_dir = f"{BUILD_PATH}/mash/{self.day_mash_dir}"
        self.mash_log_file = f"{self.mash_des_dir}/logs/mash-{self.task_id[0:4]}{self.suffix}.log"
        self.scripts_dir = f"{self.mash_des_dir}/script_dir/"
        reset_dirs(os.path.dirname(self.mash_log_file))
        self.output_subdir = f"{self.mash_des_dir}/mash_data"
        self.mash_cache = f"{BUILD_PATH}/mash/mash_cache/{self.params.get('koji_ip')}"

        self.mash_logger = zero_log("mash", self.mash_log_file)
        self.mash_logger.debug(f"Mash 缓存文件路径：{self.mash_cache}")
        self.mash_logger.debug(f"Mash 结果文件路径：{self.mash_des_dir}")

        # mash参数文件名称, 保留下载后的文件名
        self.black_list = url_filename(
            self.params.get('mash_blacklist_path')) or self.task_id[0:4] + "-" + self.tag + ".txt"
        self.comps_path = url_filename(self.params.get('comps_path')) or self.task_id[0:4] + "-" + self.tag + ".xml"

        self.scripts = []

    def mash_download_file(self):
        """获取用户自定义文件"""
        self.process = 10
        if not self.params.get('mash_blacklist_path') or len(self.params.get('mash_blacklist_path', '')) < 10:
            # 生成空黑名单文件
            str0 = ""
            black_list = os.path.join(self.mash_des_dir, self.black_list)
            with open(black_list, 'w', encoding="utf-8") as f:
                f.write(str0)
                f.write(os.linesep)
        else:
            download_file(self.params.get('mash_blacklist_path'), dir_=self.mash_des_dir, logger=self.mash_logger)

        if not self.params.get('comps_path', "") or len(self.params.get('comps_path', "")) < 10:
            # 生成空comps文件
            str0 = ""
            comps = os.path.join(self.mash_des_dir, self.comps_path)
            with open(comps, 'w', encoding="utf-8") as f:
                f.write(str0)
                f.write(os.linesep)
        else:
            download_file(self.params.get('comps_path'), dir_=self.mash_des_dir, logger=self.mash_logger)

        if not self.params.get('mash_multilib_path') or len(self.params.get('mash_multilib_path')) < 10:
            str2 = "no multilib rpms"
            self.mash_logger.info(str2)
        else:
            download_file(self.params.get('mash_multilib_path'), dir_=self.mash_des_dir, logger=self.mash_logger)

        if not self.params.get('script_after_mash') or len(self.params.get('script_after_mash')) < 10:
            str3 = "no script_after_mash scripts"
            self.mash_logger.info(str3)
        else:
            scripts = self.params.get('script_after_mash').split('\n')
            for script in scripts:
                script_name = os.path.basename(script)
                download_file(script, self.scripts_dir, script_name, logger=self.mash_logger)

    def config_mash_by_tag(self):
        """生成指定tag的tag.mash配置文件"""
        self.process = 20
        # mash.arch.conf default配置 TODO:文件名随机。
        mash_koji = f"/etc/mash/mash.{self.params.get('target_arch').replace(' ', '_')}.conf"
        # os.chdir(SOURCE_PATH)
        content = open('/etc/mash/mash.arch.conf', encoding="utf-8").read()
        content = content.replace("{koji_ip}", self.params.get('koji_ip'))
        with open(mash_koji, 'w', APACHE_READ_MODEL, encoding="utf-8") as f:
            f.write(content)
        os.chmod(mash_koji, APACHE_READ_MODEL)
        msg = "mash默认配置文件 mash.arch.conf: [" + mash_koji + "]"
        _update_celery(self._update_celery_func, self.mash_logger, msg, self.process, None, self.task_id)

        # tag.mash配置
        mash_tag_file = f"/etc/mash/{self.tag.replace('/', '_') + '-' + self.task_id[0:4]}.mash"
        content = open('/etc/mash/tag.mash.templ', encoding="utf-8").read()
        content = content.replace("{koji_ip}", self.params.get('koji_ip'))
        content = content.replace("{mash_tag}", f"{self.tag}-{self.task_id[0:4]}{self.suffix}")
        content = content.replace("{arch}", self.params.get('target_arch'))
        content = content.replace("{mash_data}", f"{self.output_subdir}")
        content = content.replace("{tag}", self.params.get('tag'))
        content = content.replace("{black_list}", os.path.join(self.mash_des_dir, self.black_list))
        content = content.replace("{comps_file}", os.path.join(self.mash_des_dir, self.comps_path))
        content = content.replace("{latest}", "False" if self.params.get('latest') == "False" else "True")
        content = content.replace("{inherit}", self.params.get('inherit'))
        content = content.replace("{strict_keys}", self.params.get('strict_keys'))
        content = content.replace("{keys}", self.params.get('keys'))
        content = content.replace("{mash_cache}", f"{self.mash_cache}")
        content = content.replace("{source}", self.params.get('source'))
        content = content.replace("{debuginfo}", self.params.get('debuginfo'))
        content = content.replace("{debugsource}", self.params.get('debugsource'))
        content = content.replace("{multilib}", self.params.get('multilib'))
        content = content.replace("{multilib_method}", self.params.get('multilib_method'))
        with open(mash_tag_file, 'w', encoding="utf-8") as f:
            f.write(content)

        _update_celery(self._update_celery_func, self.mash_logger, "mash-tag配置文件[" + mash_tag_file + "]", self.process, None, task_id=self.task_id)
        return mash_koji, mash_tag_file

    def run_mash(self):
        """mash主工作流程,采用"""
        self.process = 50
        _update_celery(self._update_celery_func, self.mash_logger, f"Mash开始,Tag:{self.tag}", self.process, None, task_id=self.task_id)
        rpm_no_signed = []

        mash_cmd = f"mash -c /etc/mash/mash.{self.params.get('target_arch').replace(' ', '_')}.conf " \
                   f"-f {self.mash_des_dir}/{self.comps_path} -o " \
                   f"{self.mash_des_dir} {self.tag}-{self.task_id[0:4]}{self.suffix}"
        cmd_stdout = run_get_return(mash_cmd, self.mash_logger)[1] or ""
        mash_content = list(filter(None, cmd_stdout.split("\n")))
        done_flag = 'mash done'
        if mash_content and (
                done_flag in mash_content[len(mash_content) - 2] or done_flag in mash_content[len(mash_content) - 1]):
            _update_celery(self._update_celery_func, self.mash_logger, "Mash成功", self.process, None, task_id=self.task_id)
        else:
            for i in mash_content:
                if '(signed with no key)' in i:
                    rpm_name_tail = i.rfind(" is not signed")
                    rpm_name_head = i.rfind("package ")
                    rpm_no_signed.append(i[rpm_name_head + 8: rpm_name_tail])
            if rpm_no_signed:
                _update_celery(self._update_celery_func, self.mash_logger, f"未签名的包:{rpm_no_signed}", self.process, None, task_id=self.task_id)
        if not mash_content or (done_flag not in mash_content[len(mash_content) - 2] and done_flag not in mash_content[len(mash_content) - 1]):
            _update_celery(self._update_celery_func, self.mash_logger, "Mash失败", self.process, False, task_id=self.task_id)
            raise MashException("检查不到结束标志。mash命令执行失败")
        return rpm_no_signed

    def check_mash_log(self, _url="http://localhost/iso-manager/server-api/task-manager/real_task/real_log"):
        """
        获取mash_log路径回传后端
        编译机日志回传到build端
        """

        if os.path.exists(self.mash_log_file):
            real_log = f"{HOST_HTTP}/log_show_tools.py?num=0&path={self.mash_log_file}"
            send_request(url=str(_url), method="POST", data={"log_url": real_log}, verify=False)
            return file_http_mapping(self.mash_log_file)
        else:
            return None

    def mash_package_list(self):
        """创建mash-packages列表"""
        self.process = 80
        _update_celery(self._update_celery_func, self.mash_logger, "创建mash导出的packages列表", self.process, None, task_id=self.task_id)
        r = []
        for arch in self.params.get('target_arch').split(' '):
            package_dir = f"{self.mash_des_dir}/mash_data/{arch}"
            pkg_list_file = f"{self.mash_des_dir}/logs/%s" % '-'.join([self.params.get('tag'), 'mash', 'packages.txt'])
            args = rf"find {package_dir} |grep '\.rpm$' " + f" |sort > {pkg_list_file}"
            command_status = run_get_return(args, self.mash_logger)[0]
            if not command_status:
                _update_celery(self._update_celery_func, self.mash_logger, "创建mash-packages-file失败", self.process, False, self.task_id)
                raise MashException("创建mash-packages-file失败")
            r.append(file_http_mapping(pkg_list_file))
        return r

    def mash_clean(self):
        """mash程序终止环境清理"""
        # ps -ef |grep mash |awk '{print $2}' |xargs kill -15
        _update_celery(self._update_celery_func, self.mash_logger, f"clean {self.mash_des_dir}/", self.process, None, task_id=self.task_id)
        if os.path.isdir(self.mash_des_dir):
            shutil.rmtree(self.mash_des_dir)

    def mash_process(self, tag_count=1, tag_index=1):
        """外部调用mash主函数入口"""
        self.mash_download_file()
        self.config_mash_by_tag()
        self.run_mash()
        self.run_scripts()

        _update_celery(self._update_celery_func, self.mash_logger, f"返回mash源地址, Tag:{self.tag}", self.process, None, task_id=self.task_id)
        arch = self.params.get('target_arch').strip()

        # httpd路径部分
        httpd_mash = ""
        if " " in arch:
            # 多架构
            httpd_mash = f"{HOST_HTTPS}/mash/{self.day_mash_dir}/mash_data/"
        else:
            # 单架构
            mash_packages = os.path.join(self.output_subdir, arch, 'Packages')
            mash_repodata = os.path.join(self.output_subdir, arch, 'repodata')
            mash_path = f"mash/{self.day_mash_dir}/mash_data/{arch}"
            if os.path.exists(mash_packages) and os.path.exists(mash_repodata):
                if len(os.listdir(mash_packages)) > 0 and len(os.listdir(mash_repodata)) > 0:
                    httpd_mash = f"{HOST_HTTPS}/{mash_path}"

            self.process = 100 / tag_count * tag_index
            self.mash_logger.info(f"mash源地址是：{httpd_mash}")
            info = {"mash_log": file_http_mapping(self.mash_log_file), "mash_httpd": httpd_mash, "mash_list": ""}
            _update_celery(self._update_celery_func, self.mash_logger, f" Tag:{self.tag} 的 mash 完成", self.process, 'SUCCESS', task_id=self.task_id, **info)

        return httpd_mash

    def run_scripts(self):
        if not os.path.exists(self.scripts_dir):
            return
        self.scripts = os.listdir(self.scripts_dir)
        # 遍历每个文件
        for script in self.scripts:
            # 判断文件是否以".sh"结尾
            if script.endswith(".sh"):
                # 记录执行日志
                self.mash_logger.info(f" 执行 {script} 脚本")
                # 构建脚本路径
                script_path = f"{self.scripts_dir}/{script}"
                # 调用子进程执行脚本
                os.system(f'cd {self.output_subdir} && sh {script_path}')
