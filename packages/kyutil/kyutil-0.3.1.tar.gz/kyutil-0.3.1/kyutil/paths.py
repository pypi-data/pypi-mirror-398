# -*- coding: UTF-8 -*-
import os


class BasePaths(object):
    def __init__(self, base_path):
        self.base_path_ = base_path
        # default paths
        self.compose = ComposePaths(self.base_path_)
        self.log = LogPaths(self.base_path_)
        self.work = WorkPaths(self.base_path_)
        # self.metadata ?

    def topdir(self):
        return self.base_path_


class WorkPaths(object):
    def __init__(self, base_path):
        self.base_path = base_path

    def topdir(self, arch=None, create_dir=False):
        """
        Examples:
            work/global
            work/x86_64
        """
        arch = arch or "global"
        path = os.path.join(self.base_path, "work", arch)
        if create_dir:
            os.makedirs(path)
        return path

    def pkgset_repo(self, pkgset_name='', arch=None, create_dir=False):
        """
        Examples:
            work/x86_64/repo/v11
            work/global/repo/v11
        """
        arch = arch or "global"
        path = os.path.join(self.topdir(arch, create_dir=create_dir), "repo", pkgset_name)
        if create_dir:
            os.makedirs(path)
        return path

    def composeinfo(self, arch=None, create_dir=False):
        arch = arch or "global"
        return os.path.join(self.topdir(arch, create_dir=create_dir), "composeinfo-base.json")


class LogPaths(object):
    def __init__(self, base_path):
        self.base_path = base_path

    def topdir(self, arch=None, create_dir=False):
        """
        Examples:
            log/global
            log/x86_64
        """
        arch = arch or "global"
        path = os.path.join(self.base_path, "logs", arch)
        if create_dir:
            os.makedirs(path)
        return path


class ComposePaths(object):
    def __init__(self, compose):
        self.compose = compose

    def topdir(self, arch=None, variant=None, create_dir=False, relative=False):
        """
        Examples:
            compose
            compose/Server/x86_64
        """
        if bool(arch) != bool(variant):
            raise TypeError("topdir(): either none or 2 arguments are expected")

        path = ""
        if not relative:
            path = os.path.join(self.compose, "compose")

        if arch or variant:
            if variant.type == "addon":
                return self.topdir(
                    arch, variant.parent, create_dir=create_dir, relative=relative
                )
            path = os.path.join(path, variant.uid, arch)
        if create_dir and not relative:
            os.makedirs(path)
        return path
