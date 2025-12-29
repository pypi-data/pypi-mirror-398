#!/usr/bin/env python3
"""
去除Markdown文档中的所有空行

用法:
    pixelarraylib remove_empty_lines <input_file> [output_file]

参数:
    input_file    输入的Markdown文件路径
    output_file   输出的文件路径（可选，默认覆盖原文件）

示例:
    pixelarraylib remove_empty_lines test.md
    pixelarraylib remove_empty_lines test.md output.md
"""

import sys
import argparse
import os
from pathlib import Path


def remove_empty_lines(input_file, output_file=None):
    """
    description:
        去除文件中的所有空行
    parameters:
        input_file(str): 输入文件路径
        output_file(str): 输出文件路径，如果为None则覆盖原文件
    return:
        success(bool): 处理是否成功
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误：文件 '{input_file}' 不存在")
            return False
        
        # 读取文件内容
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 过滤掉空行（包括只包含空白字符的行）
        filtered_lines = [line for line in lines if line.strip()]
        
        # 确定输出文件路径
        if output_file is None:
            output_file = input_file
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(filtered_lines)
        
        # 统计信息
        original_lines = len(lines)
        filtered_lines_count = len(filtered_lines)
        removed_lines = original_lines - filtered_lines_count
        
        print(f"处理完成！")
        print(f"原始行数: {original_lines}")
        print(f"处理后行数: {filtered_lines_count}")
        print(f"移除空行数: {removed_lines}")
        print(f"输出文件: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"错误：处理文件时发生异常: {e}")
        return False


def main():
    """
    description:
        主函数，处理命令行参数并执行去除空行操作
    """
    parser = argparse.ArgumentParser(
        description="去除Markdown文档中的所有空行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  pixelarraylib remove_empty_lines test.md                    # 去除test.md中的空行并覆盖原文件
  pixelarraylib remove_empty_lines test.md output.md          # 去除test.md中的空行并保存到output.md
        """
    )
    
    parser.add_argument(
        "input_file",
        help="输入的Markdown文件路径"
    )
    
    parser.add_argument(
        "output_file",
        nargs="?",
        help="输出的文件路径（可选，默认覆盖原文件）"
    )
    
    # 如果没有命令行参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # 检查输入文件扩展名
    input_path = Path(args.input_file)
    if not input_path.suffix.lower() in ['.md', '.markdown', '.txt']:
        print(f"警告：文件 '{args.input_file}' 不是标准的Markdown文件")
        response = input("是否继续处理？(y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("操作已取消")
            return
    
    # 执行去除空行操作
    success = remove_empty_lines(args.input_file, args.output_file)
    
    if success:
        print("✅ 空行去除完成！")
    else:
        print("❌ 空行去除失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
