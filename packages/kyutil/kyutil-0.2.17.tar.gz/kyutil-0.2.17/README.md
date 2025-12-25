# kyutil
麒麟python工具库

    Changelog:
        ### 0.2.16
            - FEATURE: koji客户端增加获取继承tag列表
        ### 0.2.13
            - FIX: pungi-koji集成workdir设置 BUG修复
        ### 0.2.12
            - FEATURE: 仓库比对BUG修复
        ### 0.2.11
            - FEATURE: pungi-koji增加构建类型
        ### 0.2.10
            - FEATURE: 调用jenkins执行任务后，增加执行状态返回值
        ### 0.2.9
            - FIX: 修改集成容器任务为环境变量读取，修改image_tag为外部传入
        ### 0.2.5
            - FIX: 自检报告的文件名称 从 自检报告 改为 self-check-report
        ### 0.2.4
            - FEATURE: Compose制品回传增加os目录回传（除了Packages）    
        ### 0.1.12
            - BUGFIX: 修复在mock环境内找不到celery.log的BUG    
        ### 0.1.0
            - initial release