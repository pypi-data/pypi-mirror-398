"""
PixelArrayLib 脚本工具包
包含各种实用的命令行工具和脚本
"""

__version__ = "1.2.2"
__author__ = "Lu qi"

# 导出主要的脚本函数
from pixelarraylib.scripts.create_test_case_files import main as create_test_case_files
from pixelarraylib.scripts.collect_code_to_txt import main as collect_code_to_txt
from pixelarraylib.scripts.nginx_proxy_to_ecs import main as nginx_proxy_to_ecs
from pixelarraylib.scripts.remove_empty_lines import main as remove_empty_lines
from pixelarraylib.scripts.build_website import main as build_website
from pixelarraylib.scripts.tson_convert import main as tson_convert

__all__ = [
    "create_test_case_files",
    "collect_code_to_txt",
    "nginx_proxy_to_ecs",
    "remove_empty_lines",
    "build_website",
    "tson_convert",
]
