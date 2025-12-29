#!/usr/bin/env python3
"""
PixelArrayLib 命令行工具入口点
支持的命令：
- pixelarraylib create_test_case_files
- pixelarraylib collect_code_to_txt [options]
- pixelarraylib nginx_proxy_to_ecs [options]
- pixelarraylib remove_empty_lines <input_file> [output_file]
- pixelarraylib build_website
- pixelarraylib tson_convert [options]
"""

import sys
import argparse


def main():
    """
    description:
        PixelArrayLib命令行工具主入口函数
    """
    # 检查是否有子命令
    if len(sys.argv) < 2:
        parser = argparse.ArgumentParser(
            description="PixelArrayLib 命令行工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  pixelarraylib create_test_case_files --help                    # 创建测试用例文件
  pixelarraylib collect_code_to_txt --help                       # 查看收集工具帮助
  pixelarraylib nginx_proxy_to_ecs --help                        # 查看Nginx反向代理到ECS工具帮助
  pixelarraylib remove_empty_lines --help                        # 查看去除空行工具帮助
  pixelarraylib build_website --help                              # 查看一键构建网站工具帮助
  pixelarraylib tson_convert --help                               # 查看TSON转换工具帮助
            """,
        )
        parser.print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "create_test_case_files":
        # 导入并执行创建测试用例文件功能
        try:
            from pixelarraylib.scripts.create_test_case_files import (
                main as create_test_main,
            )

            create_test_main()
        except ImportError as e:
            print(f"错误：无法导入 create_test_case_files 模块: {e}")
            sys.exit(1)

    elif command == "collect_code_to_txt":
        # 导入并执行代码收集功能
        try:
            from pixelarraylib.scripts.collect_code_to_txt import main as collect_main

            # 修改sys.argv，移除第一个参数（pixelarraylib），让collect_code_to_txt正确处理参数
            original_argv = sys.argv
            sys.argv = [original_argv[0]] + original_argv[2:]
            collect_main()
            sys.argv = original_argv
        except ImportError as e:
            print(f"错误：无法导入 collect_code_to_txt 模块: {e}")
            sys.exit(1)

    elif command == "nginx_proxy_to_ecs":
        # 导入并执行Nginx反向代理到ECS功能
        try:
            from pixelarraylib.scripts.nginx_proxy_to_ecs import (
                main as nginx_proxy_to_ecs,
            )

            # 修改sys.argv，移除第一个参数（pixelarraylib），让nginx_proxy_to_ecs正确处理参数
            original_argv = sys.argv
            sys.argv = [original_argv[0]] + original_argv[2:]
            nginx_proxy_to_ecs()
            sys.argv = original_argv
        except ImportError as e:
            print(f"错误：无法导入 nginx_proxy_to_ecs 模块: {e}")
            sys.exit(1)

    elif command == "remove_empty_lines":
        # 导入并执行去除空行功能
        try:
            from pixelarraylib.scripts.remove_empty_lines import (
                main as remove_empty_lines_main,
            )

            # 修改sys.argv，移除第一个参数（pixelarraylib），让remove_empty_lines正确处理参数
            original_argv = sys.argv
            sys.argv = [original_argv[0]] + original_argv[2:]
            remove_empty_lines_main()
            sys.argv = original_argv
        except ImportError as e:
            print(f"错误：无法导入 remove_empty_lines 模块: {e}")
            sys.exit(1)

    elif command == "build_website":
        # 导入并执行一键构建网站功能
        try:
            from pixelarraylib.scripts.build_website import main as build_website_main
            original_argv = sys.argv
            sys.argv = [original_argv[0]] + original_argv[2:]
            build_website_main()
            sys.argv = original_argv
        except ImportError as e:
            print(f"错误：无法导入 build_website 模块: {e}")
            sys.exit(1)

    elif command == "tson_convert":
        # 导入并执行TSON转换功能
        try:
            from pixelarraylib.scripts.tson_convert import main as tson_convert_main
            original_argv = sys.argv
            sys.argv = [original_argv[0]] + original_argv[2:]
            tson_convert_main()
            sys.argv = original_argv
        except ImportError as e:
            print(f"错误：无法导入 tson_convert 模块: {e}")
            sys.exit(1)

    elif command in ["-h", "--help"]:
        parser = argparse.ArgumentParser(
            description="PixelArrayLib 命令行工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  pixelarraylib create_test_case_files --help                    # 创建测试用例文件
  pixelarraylib collect_code_to_txt --help                       # 查看收集工具帮助
  pixelarraylib nginx_proxy_to_ecs --help                        # 查看Nginx反向代理到ECS工具帮助
  pixelarraylib remove_empty_lines --help                        # 查看去除空行工具帮助
  pixelarraylib build_website --help                              # 查看一键构建网站工具帮助
  pixelarraylib tson_convert --help                               # 查看TSON转换工具帮助
            """,
        )
        parser.print_help()
    else:
        print(f"错误：未知命令 '{command}'")
        print(
            "可用命令：create_test_case_files, collect_code_to_txt, nginx_proxy_to_ecs, remove_empty_lines, build_website, tson_convert"
        )
        print("使用 'pixelarraylib --help' 查看帮助")
        sys.exit(1)


if __name__ == "__main__":
    main()
