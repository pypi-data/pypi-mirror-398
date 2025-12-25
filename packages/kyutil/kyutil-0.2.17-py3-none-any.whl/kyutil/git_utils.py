# -*- coding: UTF-8 -*-
import os

from git import Repo
from git.repo.fun import is_git_dir

from kyutil.shell import run_get_return_once


class GitRepository(object):
    # 初始化
    def __init__(self, repo_url, local_path, branch='master'):
        self.local_path = local_path
        self.repo_url = repo_url
        self.repo = None
        self.branch = branch
        self.initial()

    def initial(self):
        # 判断本地仓库存在否，不存在则新建一个
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
        git_local_path = os.path.join(self.local_path, ".git")
        # 单测情况下，初始化虚拟仓库，不clone代码仓，生成一个空git仓
        if not is_git_dir(git_local_path):
            self.repo = Repo.clone_from(self.repo_url, to_path=self.local_path, branch=self.branch)
        else:
            self.repo = Repo(self.local_path)

    # 拉取远程代码
    def pull(self):
        return self.repo.git.pull()

    def get_log(self, repo_dir=None):

        repo_dir = repo_dir or self.local_path
        cmd = f"cd {repo_dir} && git log -5"
        _, r = run_get_return_once(cmd)
        return r

    def get_log2(self, repo_dir=None):
        if repo_dir:
            self.repo = Repo(repo_dir)
        # 获取最近5条提交记录
        commits = list(self.repo.iter_commits(max_count=5))
        # 格式化输出
        log_output = []
        for commit in commits:
            log_output.append(
                f"commit  : {commit.hexsha[:8]}\n"
                f"Author  : {commit.author.name}\n"
                f"Date    : {commit.authored_datetime}\n"
                f"Message : {commit.message.split('Change-Id')[0].strip()}\n"
            )
        return "\n".join(log_output)

    def get_commit_id(self, repo_dir=None):
        if repo_dir:
            self.repo = Repo(self.local_path)
        return self.repo.head.commit.hexsha

    def get_first_commit_time(self, max_count=2000):
        """获取第一次提交时间"""
        commit_log = self.repo.git.log(
            '--pretty={"commit":"%h","author":"%an","summary":"%s","date":"%cd"}',
            max_count=max_count,
            date='format:%Y-%m-%d')
        log_list = commit_log.split("\n")
        real_log_list = [eval(item) for item in log_list]
        return real_log_list[-1].get('date')
