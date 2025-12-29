#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PixelArray Python开发工具库

这个库包含了常用的开发工具和服务集成：
- aliyun: 阿里云服务集成 (STS, SMS, OSS, FC, Email, ECS, 内容扫描等)
- db_utils: 数据库工具 (Redis, MySQL)  
- decorators: 装饰器工具
- gitlab: GitLab工具 (PyPI包管理)
- monitor: 监控工具 (飞书通知)
- net: 网络请求工具
- system: 系统工具

使用示例:
    from pixelarraylib.aliyun import oss
    from pixelarraylib.db_utils import mysql
    from pixelarraylib.decorators import decorators
    from pixelarraylib.gitlab import pypi_package_manager
"""

__version__ = "1.2.2"
__author__ = "PixelArray"
__email__ = "qi.lu@pixelarrayai.com"

# 导出主要模块
__all__ = [
    'aliyun',
    'db_utils', 
    'decorators',
    'gitlab',
    'monitor',
    'net',
    'system', 
]
