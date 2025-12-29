# -*- coding: UTF-8 -*-
"""koji class"""
import json
import os
import re
import time
import traceback
from datetime import datetime
from optparse import SUPPRESS_HELP, OptionParser
from urllib import parse

from koji import ClientSession
from koji_cli.commands import koji
from koji_cli.lib import _, get_epilog_str

from kyutil.base import dict_to_argv
from kyutil.log import zero_log
from kyutil.rpm_operation import get_nvr

TS_10YEAR = 10 * 365 * 86400
SRC_SUFFIX = ".src.rpm"


def print_task(task, depth=0):
    """Print a task"""
    task = task.copy()
    task['state'] = koji.TASK_STATES.get(task['state'], 'BADSTATE')
    fmt = "%(id)-8s %(priority)-4s %(owner_name)-20s %(state)-8s %(arch)-10s "
    if depth:
        indent = "  " * (depth - 1) + " +"
    else:
        indent = ''
    label = koji.taskLabel(task)
    print(''.join([fmt % task, indent, label]))


def get_task_method_by_cmd(cmd):
    """get task method name by cmd"""
    if cmd == "image-build":
        return 'image'
    else:
        return cmd


def print_task_recurse(task, depth=0):
    """Print a task and its children"""
    print_task(task, depth)
    for child in task.get('children', ()):
        print_task_recurse(child, depth + 1)


def get_task_label_by_task(task_info):
    """get koji task label by task info"""
    method = task_info['method']
    label = task_info['arch']
    if method in ('livecd', 'appliance', 'image', 'livemedia') and 'request' in task_info:
        stuff = task_info['request']
        label = f'{stuff[0]}-{stuff[1]}'
    return label


def print_task_headers():
    """Print the column headers"""
    print("ID       Pri  Owner                State    Arch       Name")


class CtdyKoji(object):
    """koji class"""
    HTTP_PREFIX = "http:"
    TASK_INFO_URL = "/koji/taskinfo?taskID="
    KOJI_FILES_URL = "/kojifiles/work/tasks/"
    user = password = ""

    def __init__(self, baseurl, koji_options=None, instances=None, app=None, logger=None):
        """
        init koji server config and command arguments
        @param baseurl: koji server url
        @param logger: logger handler
        """
        self.owner = None
        self.baseurl = baseurl
        self.fake_server_argv = self._init_argv(baseurl)
        self.session = None
        self.koji_options = koji_options
        if logger:
            self.logger = logger
        else:
            self.logger = zero_log("ctdy_koji")
        options, _, _ = self._get_options(self.fake_server_argv)
        if options.server.find("237") > 0:
            self.session = instances.get("koji_237")
        elif options.server.find("238") > 0:
            self.session = instances.get("koji_238")
        elif options.server.find("239") > 0:
            self.session = instances.get("koji_239")
        elif options.server.find("240") > 0:
            self.session = instances.get("koji_240")
        elif options.server.find("241") > 0:
            self.session = instances.get("koji_241")

        if self.session is None:
            session_opts = koji.grab_session_options(options)
            session_opts.update(koji_options)
            self.session = ClientSession(options.server, session_opts)

    def _init_argv(self, baseurl):
        """
        init koji configuration parameters
        @param baseurl: koji server url
        @return: fake server dict
        """
        if not baseurl.startswith('http'):
            baseurl = self.HTTP_PREFIX + '//' + baseurl
        url_data = parse.urlparse(baseurl)
        host_url = self.HTTP_PREFIX + '//' + url_data.netloc
        opt_dict = {
            'server': parse.urljoin(host_url, 'kojihub'),
            'weburl': parse.urljoin(host_url, 'koji'),
            'topurl': parse.urljoin(host_url, 'kojifiles'),
            'topdir': '/mnt/koji', 'keycloakcert': True
        }
        fake_server_argv = dict_to_argv(opt_dict)

        ctdy_info = self._get_project_info()
        if ctdy_info.get('user'):
            fake_server_argv.append(f"--user={ctdy_info.get('user')}")
            self.owner = ctdy_info.get('user')
        if ctdy_info.get('password'):
            fake_server_argv.append(f"--password={ctdy_info.get('password')}")
        return fake_server_argv

    def _get_options(self, opts):
        """process options from command line and config file"""
        (options, args) = self.parse_koji_cli_top_args(opts)

        # load local config
        try:
            result = koji.read_config(options.profile, user_config=options.configFile)
        except koji.ConfigurationError as e:
            traceback.print_exc()
            # parser.error(e.args[0])
            self.logger.error(e.args[0])
            assert False

        # update options according to local config
        for name, value in result.items():
            if getattr(options, name, None) is None:
                setattr(options, name, value)

        dir_opts = ('topdir', 'cert', 'serverca')
        for name in dir_opts:
            # expand paths here, so we don't have to worry about it later
            value = os.path.expanduser(getattr(options, name))
            setattr(options, name, value)

        # honor topdir
        if options.topdir:
            koji.BASEDIR = options.topdir
            koji.pathinfo.topdir = options.topdir

        # load_plugins(options.plugin_paths)

        if not args:
            options.help_commands = True
        if options.help_commands:
            # hijack args to [return_code, message]
            return options, '_list_commands', [0, '']

        aliases = {
            'cancel-task': 'cancel',
            'cxl': 'cancel',
            'list-commands': 'help',
            'move-pkg': 'move-build',
            'move': 'move-build',
            'latest-pkg': 'latest-build',
            'tag-pkg': 'tag-build',
            'tag': 'tag-build',
            'untag-pkg': 'untag-build',
            'untag': 'untag-build',
            'watch-tasks': 'watch-task',
        }
        cmd = args[0]
        cmd = aliases.get(cmd, cmd)

        cmd = cmd.replace('-', '_')
        if ('anon_handle_' + cmd) in globals():
            if not options.force_auth and '--mine' not in args:
                options.noauth = True
            cmd = 'anon_handle_' + cmd
        elif ('handle_' + cmd) in globals():
            cmd = 'handle_' + cmd
        else:
            # hijack args to [return_code, message]
            return options, '_list_commands', [1, 'Unknown command: %s' % args[0]]

        return options, cmd, args[1:]

    def _get_project_info(self):
        """
        获取koji有效用户名/密码
        section_name = 'koji'
        """
        result = {'user': self.user, 'password': self.password}
        return result

    def parse_koji_cli_top_args(self, args):
        """process options from command line and config file"""

        common_commands = ['build', 'help', 'download-build',
                           'latest-build', 'search', 'list-targets']
        usage = _("%%prog [global-options] command [command-options-and-arguments]"
                  "\n\nCommon commands: %s" % ', '.join(sorted(common_commands)))
        parser = OptionParser(usage=usage)
        parser.disable_interspersed_args()
        progname = 'koji'
        parser.__dict__['origin_format_help'] = parser.format_help
        parser.__dict__['format_help'] = lambda formatter=None: (
                "%(origin_format_help)s%(epilog)s" % ({
            'origin_format_help': parser.origin_format_help(formatter),
            'epilog': get_epilog_str()}))
        parser.add_option("-c", "--config", dest="configFile",
                          help=_("use alternate configuration file"), metavar="FILE")
        parser.add_option("-p", "--profile", default=progname,
                          help=_("specify a configuration profile"))
        parser.add_option("--keytab", help=_("specify a Kerberos keytab to use"), metavar="FILE")
        parser.add_option("--principal", help=_("specify a Kerberos principal to use"))
        parser.add_option("--cert", help=_("specify a SSL cert to use"), metavar="FILE")
        parser.add_option("--runas", help=_("run as the specified user (requires special privileges)"))
        parser.add_option("--user", help=_("specify user"))
        parser.add_option("--password", help=_("specify password"))
        parser.add_option("--noauth", action="store_true", default=False,
                          help=_("do not authenticate"))
        parser.add_option("--force-auth", action="store_true", default=False,
                          help=_("authenticate even for read-only operations"))
        parser.add_option("--authtype", help=_("force use of a type of authentication, options: "
                                               "noauth, ssl, password, or kerberos"))
        parser.add_option("-d", "--debug", action="store_true",
                          help=_("show debug output"))
        parser.add_option("--debug-xmlrpc", action="store_true",
                          help=_("show xmlrpc debug output"))
        parser.add_option("-q", "--quiet", action="store_true", default=False,
                          help=_("run quietly"))
        parser.add_option("--skip-main", action="store_true", default=False,
                          help=_("don't actually run main"))
        parser.add_option("-s", "--server", help=_("url of XMLRPC server"))
        parser.add_option("--topdir", help=_("specify topdir"))
        parser.add_option("--weburl", help=_("url of the Koji web interface"))
        parser.add_option("--topurl", help=_("url for Koji file access"))
        parser.add_option("--pkgurl", help=SUPPRESS_HELP)
        parser.add_option("--plugin-paths", metavar='PATHS',
                          help=_("specify additional plugin paths (colon separated)"))
        parser.add_option("--help-commands", action="store_true", default=False,
                          help=_("list commands"))
        # parser.add_option("--keycloakcert", action="store_true", default=True,
        #                   help=_("keycloak authenticate"))
        parser.add_option("--keycloakcert", default='True',
                          help=_("keycloak authenticate"))
        return parser.parse_args(args)

    def list_tasks(self, owner, cmd, create_time, all=False):
        "Retrieve a list of tasks"
        method = get_task_method_by_cmd(cmd)
        user = self.session.getUser(owner)
        callopts = {
            'decode': True,
            'createdAfter': create_time,
            'owner': user['id'],
            'method': method,
        }
        if not all:
            callopts['state'] = [0, 1, 4]
        qopts = {'order': 'priority,create_time'}
        tasklist = self.session.listTasks(callopts, qopts)
        tasks = {x['id']: x for x in tasklist}

        # thread the tasks
        for t in tasklist:
            if t['parent'] is not None:
                parent = tasks.get(t['parent'])
                if parent:
                    parent.setdefault('children', [])
                    parent['children'].append(t)
                    t['sub'] = True

        if not tasklist:
            return None
        print_task_headers()
        for t in tasklist:
            if t.get('sub'):
                # this subtask will appear under another task
                continue
            print_task_recurse(t)
        return tasklist

    def get_latest_koji_task_id(self, owner, cmd, cmd_label, create_time, all=False):
        """get latest koji task id"""
        task_id = None
        tasks = self.list_tasks(owner, cmd, create_time, all)
        if not tasks:
            tasks = self.list_tasks(owner, cmd, None, all)
        if tasks:
            tasks.reverse()
            for task_info in tasks:
                if cmd_label:
                    task_label = get_task_label_by_task(task_info)
                    if cmd_label == task_label:
                        task_id = task_info['id']
                        break
                else:
                    task_id = task_info['id']
                    break
        return task_id

    def get_latest_task_id(self, cmd, task_label, all=False):
        create_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        task_id = self.get_latest_koji_task_id(self.owner, cmd, task_label, create_time, all)
        return task_id

    def get_task_state(self, task_id):
        """
        获取任务信息的state状态码
        2 : 成功
        3 : 取消
        5 : 失败
        @param task_id:
        @return:
        """
        return self.session.getTaskInfo(task_id).get("state")

    def task_succeed_finished(self, task_id):
        """
        根据koji getTaskInfo接口获取状态码， 2 代表成功
        @param task_id:
        @return:
        """
        task_state = self.session.getTaskInfo(task_id).get("state")
        return task_state == 2

    def task_finished(self, task_id: int) -> bool:
        """
        任务结束状态
        @param task_id:
        @return:
        """
        return self.session.taskFinished(task_id)

    def task_result_url(self, koji_url, task_id):
        """
        koji任务详情页
        @param koji_url:
        @param task_id:
        @return:
        """
        return self.HTTP_PREFIX + koji_url + self.TASK_INFO_URL + str(task_id)

    def task_koji_files_url(self, koji_url, task_id):
        """
        根据task_id 查看kojifiles的输出文件
        @param koji_url:
        @param task_id:
        @return:
        """
        return self.HTTP_PREFIX + koji_url + self.KOJI_FILES_URL + str(task_id + 1)[-4:] + "/" + str(task_id + 1)

    def get_tagged_rpm(self, tag_name, ts=None, latest=False, inherit=False) -> list:
        """
        获取tag下所有的软件包
        Args:
            tag_name:
            ts:
            latest:
            inherit:

        Returns:
            [
            二进制包列表：
                [
                    {
                        'arch': 'noarch','build_id': 22029,'buildroot_id': 79196,'buildtime': 1639968496,
                        'epoch': None,'extra': None,'id': 170579,'metadata_only': False,'name': 'python-ovs-help',
                        'payloadhash': '6b0fa2aa77b197a4a2d255069b753c76','release': '2.ky10','size': 6728,
                        'version': '2.11.0'
                    },
                ],
            源码包列表：
                [
                    {
                        "tag_id": 149,"tag_name": "v10-sp3","id": 25058,"build_id": 25058,
                        "version": "0.18","release": "3.ky10","epoch": null,"state": 1,
                        "completion_time": "2022-03-22 18:04:17.034721+08:00",
                        "start_time": "2022-03-22 17:27:46.372950+08:00",
                        "task_id": 304353,"creation_event_id": 386348,
                        "creation_time": "2022-03-22 17:27:46.385286+08:00",
                        "volume_id": 0,"volume_name": "DEFAULT","package_id": 489,
                        "package_name": "jbig2dec","name": "jbig2dec","nvr": "jbig2dec-0.18-3.ky10",
                        "owner_id": 56,"owner_name": "yangxudong"
                    },
                ]
        ]
        """
        if tag_name is None:
            return []

        tag_id = self.session.getTagID(tag_name)
        if not tag_id:
            self.logger.error("根据tag名称: %s ,获取tag_id失败，请确认此tag是否存在指定koji上" % tag_name)
            return []

        if not ts:
            return self.session.listTaggedRPMS(tag_id, latest=latest, inherit=inherit)
        else:
            event = self.session.getLastEvent(before=ts)
            event_id = None
            if event:
                event_id = event['id']
                event['timestr'] = ts

            return self.session.listTaggedRPMS(tag_id, event=event_id)

    def get_add_pkg_from_tag_by_time(self, tag_pkgs, begin_time=None, end_time=None,
                                     time_fmt="%Y-%m-%dT%H:%M:%S.%f") -> list:
        """
        根据起止时间，查询tag内新增的软件包
        @param tag_pkgs:    tag内的所有软件包
        @param begin_time:  开始时间对象
        @param end_time:    结束时间对象
        @param time_fmt:    开始 & 结束 时间格式
        @return:
        """
        add_pkgs = []
        try:
            if not tag_pkgs:
                return add_pkgs

            if not any([begin_time, end_time]):
                return add_pkgs

            begin_dt = None
            end_dt = None
            if begin_time:
                begin_dt = datetime.strptime(str(begin_time), time_fmt)  # 开始时间对象
            if end_time:
                end_dt = datetime.strptime(str(end_time), time_fmt)  # 结束时间对象

            for pkg_info in tag_pkgs:
                ts = pkg_info.get('completion_time')
                # 根据koji 接口listTaggedRPMS 获取到的源码包信息，其中completion_time 为ISO8601时间格式
                completion_dt = datetime.strptime(ts[:-6], '%Y-%m-%d %H:%M:%S.%f')
                if (begin_dt and end_dt and begin_dt <= completion_dt <= end_dt) or (
                        begin_dt and begin_dt <= completion_dt) or (
                        end_dt and completion_dt <= end_dt):
                    # 存在 begin end参数, 取区间begin<= x <=end]内的; 存在begin参数，取区间 >= begin内的; 存在end 取 <=end内的
                    add_pkgs.append(pkg_info)

        except (ValueError, TypeError) as e:
            self.logger.error("获取介于时间[ %s  %s]内的软件包错误， 错误原因: %s" % (begin_time, end_time, e))
        return add_pkgs

    def get_task_info(self, task_id):
        """
        获取任务信息的state状态码
        2 : 成功
        3 : 取消
        5 : 失败
        @param task_id:
        @return:
        """
        return self.session.getTaskInfo(buildID=task_id)

    def get_rpm_info_list(self, build_id):
        """获取BuildID下编译出的软件包信息
        @param build_id:
        """
        return self.session.listRPMs(buildID=build_id)

    def get_tag_names(self, build_id):
        tag_list = []
        for tag in self.session.listTags(build_id):
            tag_list.append(tag['name'])
        return tag_list

    def get_tagged(self, tag_name, ts=None, latest=False, inherit=False) -> list:
        """
        获取tag下的build列表
        Args:
            tag_name: tag名称
            ts: 时间戳
            latest: 是否最新版
            inherit: 是否继承

        Returns:

        """
        if tag_name is None:
            return []

        tag_id = self.session.getTagID(tag_name)
        if not tag_id:
            self.logger.error("根据tag名称: %s ,获取tag_id失败，请确认此tag是否存在指定koji上" % tag_name)
            return []

        if not ts:
            return self.session.listTagged(tag_id, latest=latest, inherit=inherit)
        else:
            event = self.session.getLastEvent(before=ts)
            event_id = None
            if event:
                event_id = event['id']
                event['timestr'] = ts

            return self.session.listTagged(tag_id, event=event_id)

    def check_tag_exists(self, tag_name):
        try:
            tag_info = self.session.getTag(tag_name)
            if tag_info:
                return True
            return False
        except koji.GenericError as e:
            self.logger.error(f"koji查询tag信息失败，原因为 {e}")

    def create_tag(self, tag_name):
        try:
            if self.check_tag_exists(tag_name):
                return False
            self.session.createTag(tag_name, None)
            return True
        except Exception as e:
            self.logger.error(f"koji新增tag信息失败，原因为 {e}")

    def add_tag(self, tag_name, packages_list, pak, target_build):
        if pak not in packages_list:
            self.session.packageListAdd(tag_name, pak, 'ctdy-build')
        tagged_id = [p.get('build_id') for p in self.session.listTagged(tag_name)]
        if target_build.get('build_id') not in tagged_id:
            self.session.tagBuild(tag_name, target_build.get("build_id"))

    def tag_build(self, tag_name, packages):
        try:
            if not self.session.logged_in:
                self.session.keycloak_cli_login(self.koji_options)
            self.create_tag(tag_name)
            packages_nvr = [pak.replace(SRC_SUFFIX, "") if pak.endswith(SRC_SUFFIX) else pak for pak in packages]
            packages_name = [get_nvr(pak)[0] for pak in packages]
            packages_list = []
            if self.session.listPackages(tagID=tag_name):
                packages_list = [p.get('package_name') for p in self.session.listPackages(tagID=tag_name)]
            for index, pak in enumerate(packages_name):
                pack = self.session.listBuilds(packageID=pak)
                target_build = [p for p in pack if packages_nvr[index] == p.get('nvr')]
                if target_build:
                    self.add_tag(tag_name, packages_list, pak, target_build[0])
        except Exception as e:
            self.logger.error(f"{packages} 加入到tag {tag_name}失败，原因为: {e}")
        finally:
            if self.session.logged_in:
                self.session.keycloak_cli_logout(self.koji_options)

    def is_influence(self, tag_name, rpm_src, build_tags, all_tagged=None) -> bool:
        """
        判断当前rpm是否影响tag中
        1. 就再本Tag下，就影响
        2. 在本tag继承的tag下，本tag没有软件包，就影响
        3. 在本tag继承的tag下，本tag有软件包，就不影响
        Args:
            all_tagged: tag_name下所有的build
            tag_name: 当前ISO集成时用的Tag的名称
            rpm_src: 源码包名称 带.src.rpm
            build_tags: 当前Build的Tag列表
        Returns:

        """
        if not all([tag_name, rpm_src]):
            return False
        tag_list = build_tags.split("\n")
        if tag_name in tag_list:  # 软件包包含此产品的Tag，就认为是对当前产品的影响
            return True
        # 没有此源码
        if not all_tagged:
            all_tagged = self.get_tagged(tag_name, latest=True)
        # 在继承Tag下，而且本Tag有源码包
        all_tagged_names = [i['name'] for i in all_tagged]
        if get_nvr(rpm_src)[0] in all_tagged_names:  # 在本tag继承的tag下，本tag有软件包，就不影响
            return True
        return True

    def get_build_info(self, build, redis_cache=None) -> dict:
        """根据源码包名称（不带.src.rpm部分）获取build信息"""
        cache_key = f"s_get_build_info_{self.baseurl}_{build}"
        r = None
        if redis_cache:
            r = redis_cache.get(cache_key)
        try:
            if r and json.loads(r):
                return json.loads(r)
        except Exception as e:
            print(f"cache error:{self.baseurl}_{build}. E:{e}")
        r = self.session.getBuild(build.replace("--", "-").replace(SRC_SUFFIX, ""))
        if r and redis_cache:
            redis_cache.set(cache_key, json.dumps(r), timeout=TS_10YEAR)
        if not r:
            print("根据：" + build.replace("--", "-").replace(SRC_SUFFIX, "") + "获取不到build info")
        return r

    def get_rpms_by_srpm(self, srpm: str, redis_cache=None) -> dict:
        """
        根据srpm获取所有的rpm，区分架构
        Args:
            srpm: 源码包名称（可能会带.src.rpm） 或者 build id（是个数字）
            redis_cache : redis cache
        Returns:
            {
                "arch":[rpms],
            }

        """
        r = None
        cache_key = f"s_get_rpms_by_srpm_{self.baseurl}_{srpm}"
        if redis_cache:
            r = redis_cache.get(cache_key)
        try:
            if r and json.loads(r):
                return json.loads(r)
        except Exception as e:
            print(f"cache error:{self.baseurl}_{srpm}. E:{e}")
        srpm = re.sub(f"{SRC_SUFFIX}$", "", srpm)
        srpm = srpm.replace("--", "-")
        build_info = self.get_build_info(srpm, redis_cache)
        rpm_arch_fullname_map = {}
        if build_info:
            rpm_info_list = self.get_rpm_info_list(build_info.get("build_id"))
            for rpm_info in rpm_info_list:
                arch = rpm_info.get("arch")
                nvr = rpm_info.get("nvr")
                fullname = f"{nvr}.{arch}.rpm"
                if arch in rpm_arch_fullname_map:
                    rpm_arch_fullname_map[arch].append(fullname)
                else:
                    rpm_arch_fullname_map[arch] = [fullname]
        else:
            print(f"NO build_info：{self.baseurl}  {srpm} ")
        if rpm_arch_fullname_map and redis_cache:
            redis_cache.set(cache_key, json.dumps(rpm_arch_fullname_map), timeout=TS_10YEAR)
        return rpm_arch_fullname_map

    def get_inherit_tag(self, tag_name):
        """
        根据tag名称 获取此tag继承的所有tag列表
        Args:
            tag_name: tag名称

        Returns:
            list: 继承的tag列表
        """
        try:
            inherit_list = self.session.getFullInheritance(tag_name)
            return [tag['name'] for tag in inherit_list]
        except Exception as e:
            self.logger.error(f"获取tag {tag_name} 的继承关系失败，原因为 {e}")
            return []
