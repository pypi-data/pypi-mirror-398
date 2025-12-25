# -*- coding: UTF-8 -*-
"""
@Project ：kyutil 
@File    ：release_dependency.py
@IDE     ：PyCharm 
@Author  ：xuyong@kylinos.cn
@Date    ：2025/3/17 下午4:09 
@Desc    ：说明：
"""
import locale
import os
import subprocess

import networkx as nx

from kyutil.file import get_files
from kyutil.shell import run_command

_, ENCODING = locale.getdefaultlocale()


class ReleaseDependency(object):

    def generate_rpmgraph(self):
        """生成依赖关系图"""
        cmd1 = f"cd {self.build_mockroot}/root/buildiso/Packages/"
        cmd2 = f"rpmgraph *.rpm > {self.rpm_graph_dot}"
        cmd3 = ' && '.join([cmd1, cmd2])
        cmd4 = f"dot -Tpdf {self.rpm_graph_dot} -o {self.rpm_graph_pdf}"
        cmds = [cmd3, cmd4]
        for cmd in cmds:
            res = run_command(cmd, self.build_logger, "生成依赖关系图失败！")
            self.command_logger.info(f'【CMD】生成依赖关系图\t命令:{cmd}\t状态:{res}')
            self.build_logger.info(f'【CMD】生成依赖关系图\t命令:{cmd}\t状态:{res}')
        try:
            self.generate_dependencies_csv()
            self.build_logger.info("生成依赖关系图CSV成功！")
        except Exception as e:
            self.build_logger.info(f"生成依赖关系图CSV失败：{e} ")

    def compare(self, ver1, rls1, ver2, rls2):
        if ver1 == ver2:
            token1 = rls1.split('_')
            token2 = rls2.split('_')
            if len(token1) == 1:
                return int(token1[0]) - int(token2[0])
            else:
                return int(token1[1]) - int(token2[1])
        else:
            token1 = ver1.split('.')
            token2 = ver2.split('.')
            for i in range(len(token1)):
                if token1[i] != token2[i]:
                    return int(token1[i]) - int(token2[i])
            return len(token1) - len(token2)

    def gen_rpm_map(self, packages):
        maps = {}
        for pak in packages:
            # query the actual name of package
            cmd = 'rpm -qp --queryformat "%{Name}\n"' + ' %s' % pak.strip()
            name = subprocess.check_output(cmd, shell=True)
            name = name.strip().decode(ENCODING)

            # query the version of package
            cmd = 'rpm -qp --queryformat "%{Version}\n"' + ' %s' % pak.strip()
            version = subprocess.check_output(cmd, shell=True)
            version = version.strip().decode(ENCODING)

            # query the release of package
            cmd = 'rpm -qp --queryformat "%{Release}\n"' + ' %s' % pak.strip()
            release = subprocess.check_output(cmd, shell=True)
            release = release.strip().decode(ENCODING)

            # map: name --> {version, release, path}
            if name not in maps:
                maps[name] = {"version": version, "release": release, "path": pak.strip()}
            else:
                version1 = maps[name]["version"]
                release1 = maps[name]["release"]
                if self.compare(version, release, version1, release1) > 0:
                    maps[name] = {"version": version, "release": release, "path": pak.strip()}
        return maps

    def fd_writer(self, fd, maps, name):
        release = maps[name]["release"]
        cmd = 'rpm -qp --provides %s | grep -v "rpmlib(" | cut -d" " -f 1' % (maps[name]["path"])
        rc = subprocess.check_output(cmd, shell=True)
        provides = rc.decode(ENCODING).split('\n')
        if "installonlypkg" not in provides:
            fd.write("    \"%s\" [color=red]\n" % name)

        # query the dependencies
        cmd = 'rpm -qp --requires %s | grep -v "rpmlib(" | cut -d" " -f 1' % maps[name]["path"]
        rc = subprocess.check_output(cmd, shell=True)
        requires = rc.decode(ENCODING).split('\n')
        count = False
        for line in requires:
            if line.strip() != '':
                count = True
                if line.split('(')[0] in maps:  # 处理  polkit 依赖 polkit-libs(aarch-64) 这种情况
                    if f"{name}_{line.split('(')[0]}" not in release:
                        fd.write("    \"%s\" -> \"%s\"\n" % (name, line.split('(')[0]))
                else:
                    continue
        if not count:
            fd.write("    { rank=max ; \"%s\" }\n" % name)

    def generate_rpmgraph(self, spin_name=None):
        spin_name = spin_name or os.path.basename(self.build_inmock_packages)
        self.build_logger.info("开始生成依赖关系图...")

        packages = get_files(self.build_inmock_packages, suffix='rpm')
        maps = self.gen_rpm_map(packages)

        # write the header of the metadata file
        fd = open(self.rpm_graph_dot, 'w+')
        fd.write("digraph XXX {\n")
        fd.write("    rankdir=LR\n")
        fd.write("    //===== Packages:\n")

        # write comments for this graph
        # comment(fd)
        for name in sorted(maps.keys()):
            self.fd_writer(fd, maps, name)
        fd.write("}\n")

        # close the metadata file
        fd.flush()
        fd.close()

        # convert the format to pdf
        cmd = 'dot -Tpdf %s -o %s' % (self.rpm_graph_dot, self.rpm_graph_pdf)
        subprocess.check_output(cmd, shell=True)
        self.generate_dependencies_csv()

    def generate_dependencies_csv(self):
        if not os.path.exists(self.rpm_graph_dot):
            raise FileNotFoundError("graph_dot生成失败，检查是否同时安装了rpm-devel和graphviz !")
        with open(self.rpm_dep_csv, 'w') as fout:
            fout.writelines('二进制包' + ',' + '被依赖关系\n')
            res = self.read_dep_from_dot()
            for r in res:
                fout.writelines(r + '\n')

    def read_dep_from_dot(self):
        try:
            graph = nx.nx_pydot.read_dot(self.rpm_graph_dot)
            edges = list(graph.edges())
            nodes = list(graph.nodes())
            res = []
            # 获取不依赖其他包的二进制
            for node in nodes:
                node = node.strip('"')
                if not any(node == edge[0].strip('"') for edge in edges):
                    if f"{node},不依赖其他二进制" not in res:
                        res.append(f"{node},不依赖其他二进制")

            # 获取二进制依赖关系
            for source, target in edges:
                source = source.strip('"')
                target = target.strip('"')
                if f"{source},{target}" not in res:
                    res.append(f"{source},{target}")
            return res

        except Exception as e:
            self.build_logger.error(f'检查环境组件数据是否安装齐全：{e}')
            return []
