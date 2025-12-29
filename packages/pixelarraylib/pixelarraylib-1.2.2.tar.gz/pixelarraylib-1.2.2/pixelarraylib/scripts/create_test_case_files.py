"""
本脚本用于一键创建所有测试用例文件
使用方法：
1. 作为命令行工具：
   pixelarraylib create_test_case_files
   
2. 作为Python模块：
   from pixelarraylib.scripts.create_test_case_files import main
   main()
"""

import os
import fnmatch


def walk_dir(dir_path):
    """
    description:
        递归遍历目录，返回所有文件路径
    parameters:
        dir_path(str): 目录路径
    return:
        file_path(generator): 文件路径生成器
    """
    for file in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, file)):
            yield os.path.join(dir_path, file)
        else:
            yield from walk_dir(os.path.join(dir_path, file))


def main():
    """
    description:
        主函数，创建所有测试用例文件
    """
    # step1: 检查是否存在test_case目录
    if not os.path.exists("test_case"):
        print("test_case目录不存在！创建test_case目录")
        os.makedirs("test_case")
    else:
        print("test_case目录存在！")

    # step2：找出所有需要创建的测试用例文件
    not_need_dir = [
        "test_case",
        "scripts",
        ".venv",
        ".git",
        ".idea",
        "dist",
        "build",
        "docs",
        "tests",
        "src",
        "tests",
        "__pycache__",
        ".pytest_cache",
    ]
    not_need_path = []
    not_need_file = [
        "__init__.py",
        "__main__.py",
        "wsgi.py",
        "settings.py",
        "local_settings.py",
        "test.py",
        "temp.py",
        "base.py",
        "main.py",
        "setup.py",
    ]
    test_case_files = []
    for file_path in filter(lambda x: x.endswith(".py"), walk_dir(os.getcwd())):
        relative_path = os.path.relpath(file_path, os.getcwd())
        dirs = os.path.dirname(relative_path).split("/")
        # 检查是否匹配通配符路径
        if any(
            fnmatch.fnmatch(os.path.dirname(relative_path), path)
            for path in not_need_path
        ):
            continue
        if (
            any(dir in not_need_dir for dir in dirs[::-1])
            or os.path.basename(file_path) in not_need_file
        ):
            continue

        test_case_files.append(
            os.path.join(
                "test_case",
                os.path.dirname(relative_path),
                "test_" + os.path.basename(file_path),
            )
        )

    # step3: 检查并创建测试用例文件
    created_test_case_files = []
    for test_case_file_path in test_case_files:
        if not os.path.exists(test_case_file_path):
            os.makedirs(os.path.dirname(test_case_file_path), exist_ok=True)
            open(test_case_file_path, "w").close()
            created_test_case_files.append(test_case_file_path)

    # step4: 打印创建的测试用例文件
    print(f"已成功创建测试用例文件{len(created_test_case_files)}个，文件路径如下：")
    for test_case_file_path in created_test_case_files:
        print(test_case_file_path)


if __name__ == "__main__":
    main()
