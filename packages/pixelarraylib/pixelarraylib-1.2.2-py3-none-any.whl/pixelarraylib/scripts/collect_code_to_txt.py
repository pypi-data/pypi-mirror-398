#!/usr/bin/env python3
"""
Git仓库代码收集工具
该脚本用于收集当前目录下所有git仓库中提交的代码文件，并写入txt文件

使用方法:
1. 作为命令行工具：
   pixelarraylib collect_code_to_txt --output=all_code.txt
   pixelarraylib collect_code_to_txt --extensions="py,js,vue" --output=frontend_code.txt
   pixelarraylib collect_code_to_txt --since="2024-01-01" --output=recent_code.txt

2. 作为Python模块：
   from pixelarraylib.scripts.collect_code_to_txt import collect_git_repos_code
   collect_git_repos_code(output_file="code.txt")
"""

import os
import subprocess
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class GitCodeCollector:
    def __init__(self, base_dir="."):
        """
        description:
            初始化Git代码收集器
        parameters:
            base_dir(str): 基础目录路径，默认为当前目录
        """
        self.base_dir = Path(base_dir).resolve()
        self.collected_files = set()  # 用于去重
        self.file_hashes = {}  # 用于检测重复内容
        self.stats = {
            "repos_found": 0,
            "files_collected": 0,
            "total_lines": 0,
            "total_size": 0,
            "errors": 0
        }

    def is_git_repo(self, path):
        """
        description:
            检查目录是否为git仓库
        parameters:
            path(str): 目录路径
        return:
            is_repo(bool): 是否为git仓库
        """
        return (Path(path) / ".git").exists()

    def find_git_repos(self):
        """
        description:
            查找当前目录下的所有git仓库
        return:
            git_repos(list): git仓库路径列表
        """
        git_repos = []
        
        # 检查当前目录是否为git仓库
        if self.is_git_repo(self.base_dir):
            git_repos.append(self.base_dir)
        
        # 递归查找子目录中的git仓库
        for item in self.base_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if self.is_git_repo(item):
                    git_repos.append(item)
        
        return git_repos

    def run_git_command(self, command, cwd):
        """
        description:
            执行git命令
        parameters:
            command(str): git命令
            cwd(str): 执行命令的工作目录
        return:
            output(str): 命令输出结果
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git命令执行失败: {command}")
            print(f"   错误信息: {e.stderr}")
            return ""

    def get_committed_files(self, repo_path, since_date=None, until_date=None, extensions=None):
        """
        description:
            获取git仓库中已提交的文件列表
        parameters:
            repo_path(str): git仓库路径
            since_date(str): 起始日期，可选
            until_date(str): 结束日期，可选
            extensions(list): 文件扩展名列表，可选
        return:
            files(list): 文件路径列表
        """
        # 获取所有提交的文件
        command = "git ls-files"
        if since_date:
            command += f' --since="{since_date}"'
        
        output = self.run_git_command(command, repo_path)
        if not output:
            return []
        
        files = []
        for line in output.split('\n'):
            if line.strip():
                file_path = Path(repo_path) / line.strip()
                if file_path.exists() and file_path.is_file():
                    # 检查文件扩展名
                    if extensions:
                        file_ext = file_path.suffix.lower()
                        if file_ext not in extensions:
                            continue
                    files.append(file_path)
        
        return files

    def get_file_content(self, file_path):
        """
        description:
            读取文件内容，处理编码问题
        parameters:
            file_path(Path): 文件路径
        return:
            content(str): 文件内容，如果读取失败返回None
        """
        try:
            # 首先尝试UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            try:
                # 尝试其他编码
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content
            except Exception as e:
                print(f"⚠️  无法读取文件 {file_path}: {e}")
                return None
        except Exception as e:
            print(f"⚠️  读取文件失败 {file_path}: {e}")
            return None

    def calculate_file_hash(self, content):
        """
        description:
            计算文件内容的哈希值
        parameters:
            content(str): 文件内容
        return:
            hash(str): MD5哈希值
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def should_skip_file(self, file_path, content):
        """
        description:
            判断是否应该跳过文件
        parameters:
            file_path(Path): 文件路径
            content(str): 文件内容
        return:
            should_skip(bool): 是否应该跳过
        """
        # 跳过空文件
        if not content or not content.strip():
            return True
        
        # 跳过二进制文件（简单检测）
        if '\x00' in content:
            return True
        
        # 跳过过大的文件（超过1MB）
        if len(content) > 1024 * 1024:
            print(f"⚠️  跳过大文件: {file_path} ({len(content)} 字节)")
            return True
        
        # 检查重复内容
        content_hash = self.calculate_file_hash(content)
        if content_hash in self.file_hashes:
            print(f"⚠️  跳过重复文件: {file_path} (与 {self.file_hashes[content_hash]} 内容相同)")
            return True
        
        self.file_hashes[content_hash] = str(file_path)
        return False

    def collect_repo_files(self, repo_path, output_file, extensions=None, since_date=None, until_date=None):
        """
        description:
            收集单个git仓库的文件
        parameters:
            repo_path(Path): git仓库路径
            output_file(file): 输出文件对象
            extensions(list): 文件扩展名列表，可选
            since_date(str): 起始日期，可选
            until_date(str): 结束日期，可选
        """
        repo_name = repo_path.name
        print(f"📁 正在处理仓库: {repo_name}")
        
        files = self.get_committed_files(repo_path, since_date, until_date, extensions)
        if not files:
            print(f"   ⚠️  未找到符合条件的文件")
            return
        
        print(f"   📄 找到 {len(files)} 个文件")
        
        repo_files_count = 0
        repo_lines_count = 0
        
        for file_path in files:
            try:
                content = self.get_file_content(file_path)
                if content is None:
                    self.stats["errors"] += 1
                    continue
                
                if self.should_skip_file(file_path, content):
                    continue
                
                # 写入文件内容
                relative_path = file_path.relative_to(self.base_dir)
                output_file.write(f"\n\n{'='*80}\n")
                output_file.write(f"文件: {relative_path}\n")
                output_file.write(f"仓库: {repo_name}\n")
                output_file.write(f"大小: {len(content)} 字节\n")
                output_file.write(f"行数: {len(content.splitlines())}\n")
                output_file.write(f"{'='*80}\n\n")
                output_file.write(content)
                output_file.write("\n")
                
                repo_files_count += 1
                repo_lines_count += len(content.splitlines())
                self.stats["files_collected"] += 1
                self.stats["total_lines"] += len(content.splitlines())
                self.stats["total_size"] += len(content)
                
            except Exception as e:
                print(f"   ⚠️  处理文件失败 {file_path}: {e}")
                self.stats["errors"] += 1
        
        print(f"   ✅ 收集了 {repo_files_count} 个文件，共 {repo_lines_count} 行")

    def collect_all_repos(self, output_file_path, extensions=None, since_date=None, until_date=None):
        """
        description:
            收集所有git仓库的代码文件
        parameters:
            output_file_path(str): 输出文件路径
            extensions(list): 文件扩展名列表，可选
            since_date(str): 起始日期，可选
            until_date(str): 结束日期，可选
        return:
            success(bool): 是否成功
        """
        print("🔍 正在搜索Git仓库...")
        git_repos = self.find_git_repos()
        
        if not git_repos:
            print("❌ 未找到任何Git仓库")
            return False
        
        self.stats["repos_found"] = len(git_repos)
        print(f"📦 找到 {len(git_repos)} 个Git仓库")
        
        # 显示仓库列表
        for i, repo in enumerate(git_repos, 1):
            print(f"   {i}. {repo.name} ({repo})")
        
        print(f"\n📝 开始收集代码文件...")
        print(f"📁 输出文件: {output_file_path}")
        if extensions:
            print(f"📄 文件类型: {', '.join(extensions)}")
        if since_date:
            print(f"📅 开始日期: {since_date}")
        if until_date:
            print(f"📅 结束日期: {until_date}")
        
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            # 写入文件头
            output_file.write("Git仓库代码收集报告\n")
            output_file.write("=" * 80 + "\n")
            output_file.write(f"收集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output_file.write(f"基础目录: {self.base_dir}\n")
            output_file.write(f"仓库数量: {len(git_repos)}\n")
            if extensions:
                output_file.write(f"文件类型: {', '.join(extensions)}\n")
            if since_date:
                output_file.write(f"开始日期: {since_date}\n")
            if until_date:
                output_file.write(f"结束日期: {until_date}\n")
            output_file.write("=" * 80 + "\n\n")
            
            # 收集每个仓库的文件
            for repo_path in git_repos:
                self.collect_repo_files(
                    repo_path, 
                    output_file, 
                    extensions, 
                    since_date, 
                    until_date
                )
        
        # 打印统计信息
        self.print_stats(output_file_path)
        return True

    def print_stats(self, output_file_path):
        """
        description:
            打印统计信息
        parameters:
            output_file_path(str): 输出文件路径
        """
        print(f"\n📊 收集完成统计:")
        print(f"   📦 处理的仓库数: {self.stats['repos_found']}")
        print(f"   📄 收集的文件数: {self.stats['files_collected']}")
        print(f"   📝 总代码行数: {self.stats['total_lines']:,}")
        print(f"   💾 总文件大小: {self.stats['total_size']:,} 字节 ({self.stats['total_size']/1024/1024:.2f} MB)")
        print(f"   ⚠️  错误数量: {self.stats['errors']}")
        print(f"   📁 输出文件: {output_file_path}")


def collect_git_repos_code(output_file="collected_code.txt", extensions=None, since_date=None, until_date=None, base_dir="."):
    """
    description:
        收集Git仓库代码的主函数
    parameters:
        output_file(str): 输出文件名
        extensions(list): 文件扩展名列表，如 ['.py', '.js']
        since_date(str): 开始日期 (YYYY-MM-DD)
        until_date(str): 结束日期 (YYYY-MM-DD)
        base_dir(str): 基础目录
    return:
        success(bool): 收集是否成功
    """
    collector = GitCodeCollector(base_dir)
    
    # 处理扩展名格式
    if extensions and isinstance(extensions, str):
        extensions = [ext.strip() for ext in extensions.split(',')]
    
    # 确保扩展名以点开头
    if extensions:
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    success = collector.collect_all_repos(output_file, extensions, since_date, until_date)
    return success


def main():
    """
    description:
        主函数，处理命令行参数并执行代码收集
    """
    parser = argparse.ArgumentParser(
        description="Git仓库代码收集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--output", "-o", default="collected_code.txt", 
                       help="输出文件名 (默认: collected_code.txt)")
    parser.add_argument("--extensions", "-e", 
                       help="文件扩展名，用逗号分隔 (如: py,js,vue)")
    parser.add_argument("--since", "-s", 
                       help="开始日期 (格式: YYYY-MM-DD)")
    parser.add_argument("--until", "-u", 
                       help="结束日期 (格式: YYYY-MM-DD)")
    parser.add_argument("--base-dir", "-d", default=".", 
                       help="基础目录 (默认: 当前目录)")
    
    args = parser.parse_args()
    
    # 处理文件扩展名
    extensions = None
    if args.extensions:
        extensions = [ext.strip() for ext in args.extensions.split(',')]
    
    # 执行收集
    success = collect_git_repos_code(
        output_file=args.output,
        extensions=extensions,
        since_date=args.since,
        until_date=args.until,
        base_dir=args.base_dir
    )
    
    if success:
        print(f"\n✅ 代码收集完成！文件已保存到: {args.output}")
    else:
        print(f"\n❌ 代码收集失败！")


if __name__ == "__main__":
    main()
