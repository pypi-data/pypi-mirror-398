# -*- coding: UTF-8 -*-
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import stat
import xml.etree.ElementTree as ET
from hashlib import sha256

from kyutil.config import BUILD_PATH_LOGGER_FILE
from kyutil.http_util import send_request
from kyutil.log import zero_log
from kyutil.rpms import read_rpm_header

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)
special_characters = ['、', ':', '；', '。', '？', '（', ]
INSTALL_LOG = "install.log"
FILE_EDIT = '/iso-manager/server-api/office-online/file-edit/?filename='
INTEGRATED_WORK_ORDER = "集成工作单.xlsx"
SCHEMES_ALLOWLIST = ['https', 'http']
DOMAINS_ALLOWLIST = ['server.kylinos.cn']


def gen_file_tree(path: str, tmp_path: str = ""):
    """
    控件参考地址为：  https://ng-zorro.gitee.io/components/tree/zh
    生成iso中的文件树，符合前端控件数据结构
    @param path:
    @param tmp_path:
    @return:
    title	    标题
    key	        整个树范围内的所有节点的 key 值不能重复且不为空！
    children	子节点
    isLeaf  	设置为叶子节点(叶子节点不可被拖拽模式放置)
    [{
      title: '0-0-1',
      key: '0-0-1',
      children: [
        { title: '0-0-1-0', key: '0-0-1-0', isLeaf: true },
        { title: '0-0-1-1', key: '0-0-1-1', isLeaf: true },
        { title: '0-0-1-2', key: '0-0-1-2', isLeaf: true }
      ]
    },
    {
      title: '0-0-2',
      key: '0-0-2',
      isLeaf: true
    }]
    """
    files = []
    if os.path.exists(path):
        for _d in os.listdir(path):
            _p = path + os.sep + _d
            node = {}
            if os.path.isdir(_p):
                node["title"] = _d
                node["key"] = _p.replace(tmp_path, "")
                node["children"] = []
                node["children"].extend(gen_file_tree(_p, tmp_path))
            elif os.path.isfile(_p):
                node["title"] = _d
                node["key"] = _p.replace(tmp_path, "")
                node["isLeaf"] = True
            if node:
                files.append(node)
    return files


def ensure_dir(fp):
    """
    确保目录存在
    Args:
        fp: 文件路径，可以是文件路径，也可以是目录

    Returns:

    """
    if not fp:
        return

    dir_fp = os.path.dirname(fp)
    if not os.path.isdir(dir_fp):
        os.makedirs(dir_fp)
    return os.path.isdir(os.path.dirname(fp))


def remove_file(fp: str) -> bool:
    """
    删除文件
    Args:
        fp: 文件路径

    Returns:

    """
    if fp and os.path.isfile(fp):
        os.remove(fp)
    return not os.path.isfile(fp)


def _item_symlinks(srcname, symlinks, dstname, srcobj, ignore_dangling_symlinks, src_entry, ignore, copy_function, dirs_exist_ok):
    linkto = os.readlink(srcname)
    if symlinks:
        os.symlink(linkto, dstname)
        shutil.copystat(srcobj, dstname, follow_symlinks=not symlinks)
    else:
        if not os.path.exists(linkto) and ignore_dangling_symlinks:
            return
        if src_entry.is_dir():
            my_copytree(srcobj, dstname, symlinks, ignore,
                        copy_function, ignore_dangling_symlinks,
                        dirs_exist_ok)
        else:
            copy_function(srcobj, dstname)


def _item(src_entry, ignored_names, src, dst, use_src_entry, symlinks, ignore_dangling_symlinks, ignore, copy_function, dirs_exist_ok, errors):
    if src_entry.name in ignored_names:
        return
    srcname = os.path.join(src, src_entry.name)
    dstname = os.path.join(dst, src_entry.name)
    srcobj = src_entry if use_src_entry else srcname
    try:
        is_symlink = src_entry.is_symlink()
        if is_symlink and os.name == 'nt':
            lstat = src_entry.stat(follow_symlinks=False)
            if lstat.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT:
                is_symlink = False
        if is_symlink:
            _item_symlinks(srcname, symlinks, dstname, srcobj, ignore_dangling_symlinks, src_entry, ignore, copy_function, dirs_exist_ok)
        elif src_entry.is_dir():
            my_copytree(srcobj, dstname, symlinks, ignore, copy_function,
                        ignore_dangling_symlinks, dirs_exist_ok)
        else:
            copy_function(srcobj, dstname)
    except shutil.Error as err:
        errors.extend(err.args[0])
    except OSError as why:
        errors.append((srcname, dstname, str(why)))


def _copytree(entries, src, dst, symlinks, ignore, copy_function,
              ignore_dangling_symlinks, dirs_exist_ok=False):
    if ignore is not None:
        ignored_names = ignore(os.fspath(src), [x.name for x in entries])
    else:
        ignored_names = set()

    os.makedirs(dst, exist_ok=dirs_exist_ok)
    errors = []
    use_src_entry = copy_function is shutil.copy2 or copy_function is shutil.copy

    for src_entry in entries:
        _item(src_entry, ignored_names, src, dst, use_src_entry, symlinks, ignore_dangling_symlinks, ignore, copy_function, dirs_exist_ok, errors)

    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if getattr(why, 'winerror', None) is None:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
    return dst


def my_copytree(src, dst, symlinks=False, ignore=None, copy_function=shutil.copy2,
                ignore_dangling_symlinks=False, dirs_exist_ok=False):
    with os.scandir(src) as itr:
        entries = list(itr)
    return _copytree(entries=entries, src=src, dst=dst, symlinks=symlinks,
                     ignore=ignore, copy_function=copy_function,
                     ignore_dangling_symlinks=ignore_dangling_symlinks,
                     dirs_exist_ok=dirs_exist_ok)


def reset_dirs(remake_dir):
    """
    函数功能：重置创建多级目录
    函数参数：remake_dir - 需要重建的目录
    函数返回值： 无
    """
    logger.info("重置目录： " + remake_dir)
    if os.path.exists(remake_dir):
        shutil.rmtree(remake_dir)
    try:
        os.makedirs(remake_dir, exist_ok=True)
    except Exception as err:
        logger.error(" == 创建文件失败: {0}".format(err))
        raise FileExistsError("创建文件失败: {0}".format(err))


def delete_dirs(useless_dir, logger_=logger):
    """
    函数功能：通用文件删除
    函数参数：useless_dir - 需要删除的目录或文件
    函数返回值：无
    """
    if not os.path.exists(useless_dir):
        # 仅提示不报错
        logger_.warning(f"要删除的目录：{useless_dir} 不存在!")
    if os.path.isdir(useless_dir):
        shutil.rmtree(useless_dir)
        logger_.info(f"删除结果：{not os.path.isdir(useless_dir)} @ {useless_dir}")
    if os.path.isfile(useless_dir):
        os.remove(useless_dir)
        logger_.info(f"删除结果：{not os.path.isfile(useless_dir)} @ {useless_dir}")


def move_dirs(source, target):
    """
    函数功能：通用文件移动
    函数参数：source_dir-源目录或文件/target_dir-目标目录或文件
    函数返回值: 无
    """
    if not os.path.exists(source):
        logger.error(f"{source} not exist!")
        raise FileNotFoundError(f"src [{source}] not exist!")
    try:
        ensure_dir(target)
        if not os.path.isdir(target):
            os.makedirs(target)
        if os.path.isdir(source):
            for file in os.listdir(source):
                shutil.move(os.path.join(source, file), os.path.join(target, file))
        if os.path.isfile(source):
            shutil.move(source, target)
    except Exception as err:
        logger.error("Move directories error: {0}".format(err))
        raise FileExistsError("Move directories error: {0}".format(err))


def copy_dirs(source, target, logger_=logger):
    """
    函数功能：通用文件复制
    函数参数：source_dir-源目录或文件/target_dir-目标目录或文件
    函数返回值：
    """
    if not os.path.exists(source):
        logger_.info(f"Can't COPY. src [{source}] not exist!")
        raise FileNotFoundError(f"Can't COPY. src [{source}] not exist!")
    try:
        ensure_dir(target)
        if os.path.isdir(source):
            for file in os.listdir(source):
                if os.path.isdir(os.path.join(source, file)):
                    my_copytree(os.path.join(source, file), os.path.join(target, file), dirs_exist_ok=True)
                elif os.path.isfile(os.path.join(source, file)):
                    shutil.copy(os.path.join(source, file), os.path.join(target, file))
                else:
                    logger_.warning(f"文件不存在: {file}")
        elif os.path.isfile(source):
            shutil.copy(source, target)
            if os.path.isfile(target):
                logger_.info(f"文件复制成功：{source} -> {target}")
            else:
                raise RuntimeError(f"文件复制失败：{source} -> {target}")
        else:
            logger_.warning(f"文件不存在: {source}")
    except Exception as err:
        logger_.error("复制命令出错: {0}".format(err))
        raise FileExistsError("复制命令出错: {0}".format(err))


def file_str_switch(_file, old_str, new_str, _g=1, _logger=logger, reason=None):
    """
    函数功能：替换文件指定行内容
    函数参数：file：要更新的文件名称；old_str：被替换的内容；new_str：表示替换后的内容；
    _g默认参数为1，表示只替换第一个匹配到的字符串；
    如果参数为_g = 'g'，则表示全文替换，排除携带#的行；
    函数返回值：无
    """
    _logger.info(f'【FILE_MODIFY】{reason}: 将 {_file} 中 {old_str} 替换为 {new_str}')
    with open(_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(_file, "w", encoding="utf-8") as f_w:
        n = 0
        if _g == 1:
            for line in lines:
                if old_str in line:
                    f_w.write(new_str)
                    n += 1
                    break
                f_w.write(line)
                n += 1
            for i in range(n, len(lines)):
                f_w.write(lines[i])
        elif _g == "g":
            for line in lines:
                if old_str in line:
                    line = new_str
                f_w.write(line)


def file_write(_file, _str):
    """
    函数功能：追加写指定文件
    函数参数：file - 文件路径；new_str - 新字符串
    函数返回值：无
    """
    if not os.path.isdir(os.path.dirname(_file)):
        os.makedirs(os.path.dirname(_file), exist_ok=True)
    with open(_file, "a+", encoding="utf-8") as f:
        json.dumps(_str, indent=4, separators=(",", ":"))
        f.write(_str)
        f.write(os.linesep)


def read_sha256sum_from_file(file_path):
    try:
        with open(file_path) as f:
            sha256sum_line = f.readline()
        return sha256sum_line.split()[0]
    except Exception as e:
        print("读取sha256sum失败，原因：", e)
        return ""


def get_file_list(file_path, exclude_keywords=None):
    if exclude_keywords is None:
        exclude_keywords = []
    for parent, dir_names, file_names in os.walk(file_path):
        dir_names.sort()
        for filename in file_names:
            if any(keyword in filename for keyword in exclude_keywords):
                continue
            yield parent, filename


def get_file_size(fp: str) -> int:
    """
    获取文件大小
    Args:
        fp:

    Returns:

    """
    if os.path.isfile(fp):
        return os.path.getsize(fp)
    return -1


def get_file_sha256sum(fp: str) -> str:
    """
    获取文件sha256
    Args:
        fp: 文件路径

    Returns:

    """
    if os.path.isfile(fp):
        m = hashlib.sha256()  # 创建md5对象
        with open(fp, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                m.update(data)  # 更新md5对象

        return m.hexdigest()  # 返回md5对象
    else:
        raise FileExistsError("File not exists")


def get_comps_list(fp: str) -> set:
    """
    获取文件大小comps文件包列表
    """
    package_names = set()
    if not os.path.exists(fp):
        return package_names
    tree = ET.parse(f'{fp}')
    root = tree.getroot()

    # 遍历XML节点并提取所有包名
    for group in root.findall('.//group'):
        for package in group.findall('.//packagereq'):
            pkg_name = package.text
            package_names.add(pkg_name)
    return package_names


def get_ks_list(fp: str) -> set:
    """
    获取文件大小comps文件包列表
    """
    ks_list = set()
    if not os.path.exists(fp):
        return ks_list
    with open(fp, "r") as f:
        for line in f.readlines()[2:-1]:
            line = line[:-1]
            ks_list.add(line)
    return ks_list


def recursive_chmod(path, mode):
    """
    递归修改目录和文件的所有者权限
    """
    if not os.path.exists(path):
        return
    try:
        os.chmod(path, mode)
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files + dirs:
                    recursive_chmod(os.path.join(root, file), mode)
    except Exception as e:
        logger.warning(f"递归修改目录和文件的所有者权限 失败: [{e}]")


def get_files(path_, index_="", suffix=None):
    f_ = []
    if not os.path.isdir(path_):
        return f_
    for root, dirs, files in os.walk(path_):
        for file in files:
            if index_ in file:
                f_.append(os.path.join(root, file))
    return [x for x in f_ if x.endswith(suffix)]


def comps_verify(fp: str, logger=logger) -> bool:
    """
    核对comps文件是否符合规范(group id唯一)
    @param fp:
    @return:
    """
    # 有无语法错误
    try:
        ET.parse(fp)
        return True
    except Exception as e:
        # print(f"XML文件【{fp}】验证失败: ", e)
        logger.error(e)
        return False


def mkdir(file_path):
    """
    创建目录
    @param file_path:
    @return:
    """
    if not file_path:
        return
    file_path = file_path.strip()
    file_path = file_path.rstrip("\\")
    file_path = file_path.rstrip("/")
    exists = os.path.exists(file_path)
    if not exists:
        os.makedirs(file_path)
    return True


def replace_log(upload_log, log_file):
    """
    替换虚拟机安装日志内容
    @param upload_log:
    @param log_file:
    @return:
    """
    # app.logger.info(f"replace content")
    with open(upload_log, "r+", encoding="utf-8") as f_upload:
        upload_content = f_upload.read()
    with open(log_file, "r+", encoding="utf-8") as f_replace:
        content = f_replace.read()
        if upload_content.find("ks post log") < 0:
            new_content = content.replace("install_content:", upload_content)
        else:
            new_content = content.replace("ks_content:", upload_content)
        f_replace.seek(0)
        f_replace.write(new_content)


def save_chunk_file_obj(file_obj, save_file: str) -> bool:
    """
    存储文件
    @param file_obj:
    @param save_file:
    @return:
    """
    if not file_obj or not save_file:
        return False
    try:
        if not os.path.exists(os.path.dirname(save_file)):
            mkdir(os.path.dirname(save_file))

        file_obj.save(save_file)  # 保存分片到本地
        return True
    except IOError:
        return False


def merge_chunk(file_name: str, save_dir: str, uuid_: str):
    """
    合并切片文件
    @param file_name:
    @param save_dir:
    @param uuid_:
    @return:
    """
    chunk = 0  # 分片序号
    with open(os.path.join(save_dir, file_name), 'wb') as target_file:  # 创建新文件
        all_files = [i for i in os.listdir(save_dir)]
        chunk_files = list(filter(lambda x: x.find(uuid_) >= 0, all_files))  # 获取切片数量
        if not chunk_files:
            return False
        for _ in chunk_files:
            filename = os.path.join(save_dir, uuid_ + "_" + str(chunk))
            if not os.path.exists(filename):
                return False

            chunk_file = open(filename, 'rb')  # 按序打开每个分片
            target_file.write(chunk_file.read())  # 读取分片内容写入新文件
            chunk_file.close()

            chunk += 1

    chunk = 0  # 分片序号
    while True:
        try:
            filename = os.path.join(save_dir, uuid_ + "_" + str(chunk))
            os.remove(filename)  # 删除该分片, 节约空间
        except IOError:
            break
        chunk += 1

    return True


def un_gz(file_name, un_gz_name=None):
    """解压gz文件, 若未指定解压后的文件, 则解压为同名去掉.gz文件
    """
    if not os.path.exists(file_name):
        return False

    un_gz_file = un_gz_name
    if not un_gz_file:
        un_gz_file = file_name.replace(".gz", "")

    if not os.access(file_name, os.R_OK):
        return False

    g_file = gzip.GzipFile(file_name)

    with open(un_gz_file, "wb+") as f:
        f.write(g_file.read())
    g_file.close()

    return True


def get_file_sha256(file_path: str) -> str:
    """
    获取文件的md5值
    :param file_path: 文件路径
    :return:md5字符串
    """
    m = sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


def find_file_starting(path_, start_=""):
    f_ = []
    if os.path.isdir(path_):
        for root, dirs, files in os.walk(path_):
            for file in files:
                if start_ in file and file.startswith(start_):
                    f_.append(os.path.join(root, file))
        return f_


def find_file_(path_, index_=""):
    f_ = []
    if os.path.isdir(path_):
        for root, dirs, files in os.walk(path_):
            for file in files:
                if index_ in file:
                    f_.append(os.path.join(root, file))
        return f_


def file_list_(path):
    files = []
    for file in os.listdir(path):
        files.append(os.path.join(path, file))
    return files


def save_file_from_uri(uri, path):
    """
    根据连接下载文件
    @param uri:
    @param path:
    @param req:
    @param meta:
    @return:
    """
    try:
        resp = send_request(uri, stream=True)
        create_file(resp.raw, path)
    except Exception as e:
        print(f"文件存储错误:{e}")


def create_conf_json(iso_path, json_dict):
    """
    创建json配置文件
    iso_bak路径生成json格式配置文件
    @param iso_path:
    @param json_dict:
    @return:
    """
    conf_path = "conf" + os.sep
    conf_file = "conf.json"

    json_path = iso_path + conf_path
    if not os.path.exists(json_path):
        try:
            os.mkdir(json_path)
        except Exception as e:
            return str(e)
        with open(json_path + conf_file, "w+") as f:
            json.dump(json_dict, f, indent=4)
    return ""


def ks_content_check(file_path) -> tuple:
    """
    iso ks文件内容核查！
    @param file_path:ks文件内容
    @return:

    ks文件格式:
    repo --name=* --baseurl=""
    %packages
    <package_name1>
    <package_name2>
    <package_name3>
    .......
    %end
    """

    format_list = ["repo --name", "%packages", "%end"]
    forbidden_list = [".src.rpm", ".rpm"]

    # 验证关键字段是否出现以及是否在相应位置
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
        for format_str in format_list:
            p = re.search(format_str, file_content)
            if not p:
                return False, f"没有包含{format_str}行！"
            start = int(p.span()[0])
            end = int(p.span()[1])
            if format_str == "repo --name" and start != 0:
                return False, "内容不规范, 检查repo --name"

            if format_str == "%end" and len(file_content[end:]) != file_content[end:].count("\n"):
                return False, "内容不规范, 检查%end"

    # 检查包名不能重复
    err_msg = check_repeat_or_forbidden(file_content, forbidden_list)
    if err_msg:
        return False, err_msg
    return True, "Ok"


def check_repeat_or_forbidden(info, forbidden_list):
    """
    检查重复内容或拒绝
    @param info:
    @param forbidden_list:
    @return:
    """
    lines = info.split("\n")
    err_msg = []
    for i in range(0, len(lines)):
        if i > 0 and lines[i] == lines[i - 1]:
            err_msg.append(f"第{i + 1}行有重复包")

        p = re.search(forbidden_list[0], lines[i]) or re.search(forbidden_list[1], lines[i])
        if p:
            err_msg.append(f"第{i + 1}行不能包含.src.rpm以及.rpm的包")
    return err_msg


def srpms_verify(file_path) -> bool:
    """
    srpm 文件有效性核查!
    @param file_path:srpm文件存在位置
    @return:
    """
    if read_rpm_header(file_path):
        return True
    else:
        return False


def get_prefix(tags, arches):
    """
    获取前缀
    @param tags:
    @param arches:
    @return:
    """
    prefixes = []
    for tag in tags:
        for arch in arches:
            prefixes.append(f"{tag.lower()}-{arch.lower()}")
    return prefixes


def create_file(stream, path):
    """
    创建文件
    @param stream:
    @param path:
    @return:
    """
    buf_size = 8196
    with io.open(path, 'wb') as out:
        read = stream.read(buf_size)

        while len(read) > 0:
            out.write(read)
            read = stream.read(buf_size)


def get_xml_file(path):
    if os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith('.xml'):
                return os.path.join(path, file)
    return None
