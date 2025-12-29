# -*- coding: UTF-8 -*-
"""shell.py"""
import subprocess
import time
import traceback

import logzero

from kyutil.config import BUILD_PATH_LOGGER_FILE
from kyutil.log import zero_log

logger = zero_log(__file__, BUILD_PATH_LOGGER_FILE)


class Shell(object):
    """Shell(object)"""

    def __init__(self):
        self.ret_code = None
        self.ret_info = None
        self.err_info = None
        self.process = None

    def run_background(self, cmd):
        """
        后台执行命令
        @param cmd:
        @return:
        """
        self.process = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    def get_output(self):
        return self.process.stdout.read()

    def loading_output(self):
        return iter(self.process.stdout.readline, 'b')

    def kill(self):
        self.process.kill()


def run_command(cmd: str, _logger=logger, error_message=None, cwd=None, timeout=14400) -> int:
    """
    函数功能：command in bash子进程函数
    特点：支持cmd输出写入logfile文件
    _logger为自定义logger，默认使用zero的logger，不写入文件
    """
    result = ""
    try:
        _logger.info(f"CMD:[{cmd}]")
        sign = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)
        time_start = time.time()
        while sign.poll() is None:
            if time.time() - time_start > timeout:
                sign.kill()
                logger.error(f"cmd Timeout: {cmd} ")
                raise TimeoutError(f"cmd Timeout: {cmd}")
            out = sign.stdout.readline()
            if out is None:
                continue
            else:
                result = out.decode(encoding='utf-8', errors='ignore') if isinstance(out, bytes) else str(out)
                if result.strip():
                    _logger.info(result.strip())
        sign.wait()
        if sign.returncode != 0:
            if error_message is not None:
                _logger.error(error_message)
            _logger.error(f"ERROR CMD:[{cmd}] Return CODE: {sign.returncode} RESULT:\n {result}")
            return sign.returncode
        return 0
    except Exception as e:
        _logger.error(str(e))
        logger.error(f"cmd : {cmd} 运行失败。{e}")
        return -1


def run_get_return_once(cmd, _logger=logzero.logger) -> tuple:
    """
    函数功能：bash command执行，将所有命令stdout保存至变量，从中提取信息
    """
    try:
        all_stdout = ""
        _logger.info(f"CMD:[{cmd}]")
        sign = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = sign.stdout.readlines()
        for line in out:
            all_stdout = all_stdout + line.decode('utf-8').strip() + '\n'
        sign.wait()
        _logger.info(all_stdout.strip())
        if sign.returncode != 0:
            _logger.error("ERROR CMD:[" + cmd + "]")
        return sign.returncode == 0, all_stdout
    except Exception as e:
        traceback.print_exc()
        _logger.error(str(e))
        raise SystemExit(cmd, str(e))


def run_command_without_info(cmd: str, _logger=logger, error_message=None):
    """
    函数功能：02-command in bash静止执行
    函数：无bash输出，无终端或日志输出
    """
    try:
        _logger.info(f"CMD:[{cmd}]")
        sign = subprocess.Popen(cmd, shell=True)
        sign.wait()
        if sign.returncode != 0:
            if error_message is not None:
                _logger.error(error_message)
            _logger.error(f"ERROR CMD:[{cmd}] Return CODE: {sign.returncode}")
            raise subprocess.CalledProcessError(sign.returncode, cmd)
    except Exception as e:
        _logger.error(str(e))
        return False
    return True


def run_get_str(cmd: str, match_str, _logger=logger):
    """
    函数功能：类bash执行并获取包含所需字符串的整行输出
    """
    try:
        stdout = ""
        _logger.info(f"CMD:[{cmd}]")
        sign = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while sign.poll() is None:
            out = sign.stdout.readline()
            if out is None:
                continue
            else:
                result = out.decode(encoding='utf-8', errors='ignore') if isinstance(out, bytes) else str(out)
                if result.strip():
                    result = result.strip()
                if match_str in result:
                    stdout = result
        sign.wait()
        return stdout
    except Exception as e:
        traceback.print_exc()
        _logger.error(str(e))


def run_get_return(cmd: str, _logger=logger, timeout=7200, cwd=None) -> tuple:
    """
    函数功能：bash command执行，将所有命令stdout保存至变量，从中提取信息
    Args:
        cmd:
        _logger:
        timeout:
        cwd:
    Returns:
        ok, out
    """
    try:
        all_stdout = ""
        _logger.info(f"CMD:[{cmd}]")
        sign = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)
        time_start = time.time()
        while sign.poll() is None:
            if time.time() - time_start > timeout:
                sign.kill()
            out = sign.stdout.readline()
            if out is None:
                continue
            else:
                result = out.decode(encoding='utf-8', errors='ignore') if isinstance(out, bytes) else str(out)
                if result.strip() and result != "" and result != "b''":
                    _logger.debug(result.strip())
            all_stdout = all_stdout + result + '\n'
        sign.wait()
        if sign.returncode != 0:
            print("ERROR CMD:[" + cmd + "]")
            _logger.error("ERROR CMD:[" + cmd + "]")
        return sign.returncode == 0, all_stdout
    except Exception as e:
        print(e)
        traceback.print_exc()
        _logger.error(str(e))
        raise SystemExit(cmd, str(e))


def run_command_ll(cmd: str, error_message=None, _logger=logger):
    """
    执行Shell命令
    @param cmd:
    @param error_message:
    @param _logger:
    @return:
    """
    try:
        _logger.info(f"CMD:[{cmd}]")
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            if error_message is not None:
                _logger.info(f"CMD err: [{error_message}]")
            return False
        else:
            return True
    except TimeoutError:
        _logger.error("cmd Timeout")
    except Exception as e:
        _logger.error(e)
        _logger.error(f"cmd XXX : {cmd}")
    return False


def run_command_with_return(cmd: str, _logger=logger, err_msg="") -> tuple:
    """
    执行Shell命令
    Args:
        cmd: 命令
        _logger: 日志
        err_msg: 如果发生错误了，输出的消息

    Returns:

    """
    try:
        _logger.info(f"CMD:[{cmd}]")
        result = subprocess.Popen(cmd, bufsize=8192, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        if result.returncode != 0:
            if err_msg:
                _logger.error(err)
                _logger.error(err_msg)
            return False, str(err)
        else:
            _logger.info(f"CMD OUT: [{out.decode(encoding='utf-8', errors='ignore')}]")
            return True, out
    except Exception as e:
        _logger.error(f"CMD 执行失败 : {cmd}, Err: {e}")
        return False, str(e)


def rum_command_and_log(cmd: str, log_file_path: str, _logger=logger):
    """
    执行Shell命令
    Args:
        cmd: 命令
        log_file_path: 日志文件路径
        @param _logger:
        @param cmd:
        @type log_file_path: object
    """
    _logger.info(f"执行开始：{cmd}")
    with open(log_file_path, 'w', encoding="utf-8") as f:
        # 写入命令行文本
        f.write(f"【CMD】: {cmd}\n\n")
        # 使用subprocess.run()执行命令并获取输出
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # 将命令执行结果写入文件
        f.write("Command output:\n")
        f.write(result.stdout)
        if result.returncode != 0 or "Error" in result.stdout or "error" in result.stdout:
            f.write("\nCommand execution failed with exit code: {}\n".format(result.returncode))
            return False
    _logger.info(f"执行成功：{cmd}")
    return True


def start_httpd():
    """
    如果httpd没启动，启动httpd
    """
    cmd = "service httpd start"
    run_command_without_info(cmd, logger, "httpd 启动失败！")
    logger.debug("httpd 服务启动成功")
