import asyncio
import json
import re
import subprocess
import traceback
from typing import Callable, Union, List, Generator, Any
from cryptography.fernet import Fernet
import base64
from pixelarraylib.monitor.feishu import Feishu
import os
import paramiko
from concurrent.futures import ProcessPoolExecutor

feishu_alert = Feishu("devtoolkit服务报警")


def execute_function_in_other_process(function: Callable, *args, **kwargs) -> Any:
    """
    description:
        在其他进程中执行函数
    parameters:
        function(Callable): 需要执行的函数
        args(tuple): 函数的参数
        kwargs(dict): 函数的关键字参数
    return:
        result(Any): 函数执行结果
    """
    with ProcessPoolExecutor() as executor:
        return executor.submit(function, *args, **kwargs).result()


async def execute_function_in_other_process_async(
    function: Callable, *args, **kwargs
) -> Any:
    """
    description:
        在其他进程中异步执行函数
    parameters:
        function(Callable): 需要执行的函数
        args(tuple): 函数的参数
        kwargs(dict): 函数的关键字参数
    return:
        result(Any): 函数执行结果
    """
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as executor:
        # 在线程池中运行阻塞的executor.submit操作
        result = await loop.run_in_executor(
            None, lambda: executor.submit(function, *args, **kwargs).result()
        )
        return result


async def execute_batch_async_tasks(tasks, semaphore_count=None):
    """
    description:
        批量执行异步任务
    parameters:
        tasks(list): 需要执行的异步任务列表
        semaphore_count(int): 信号量数量，用于控制并发数，默认为None（不限制）
    return:
        results(list): 所有任务的执行结果
    """
    if semaphore_count is None:
        return await asyncio.gather(*tasks)

    semaphore = asyncio.Semaphore(semaphore_count)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


def encode_chinese_string(text: str) -> str:
    """
    description:
        将中文转换为UTF-8编码的字符串
    parameters:
        text(str): 需要转换的字符串
    return:
        converted_text(str): 转换后的字符串（URL安全的base64格式）
    """
    # 使用URL安全的base64编码方法
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii").rstrip("=")


def decode_chinese_string(encoded_text: str) -> str:
    """
    description:
        将UTF-8编码的字符串转换为中文
    parameters:
        encoded_text(str): 编码后的字符串（URL安全的base64格式）
    return:
        text(str): 原始中文字符串
    """
    # 添加回可能被移除的填充字符'='
    padding = 4 - (len(encoded_text) % 4)
    encoded_text += "=" * padding
    # 使用URL安全的base64解码方法
    return base64.urlsafe_b64decode(encoded_text.encode("ascii")).decode("utf-8")


def generate_fernet_key() -> bytes:
    """
    description:
        生成Fernet加密密钥
    return:
        key(str): 加密密钥
    """
    return Fernet.generate_key().decode()


def encrypt_string(text: str, key: str) -> tuple[str, bytes]:
    """
    description:
        使用Fernet对称加密算法加密字符串
    parameters:
        text(str): 需要加密的字符串
        key(str): 加密密钥
    return:
        str: 加密后的字符串
    """
    f = Fernet(key.encode())
    encrypted_data = f.encrypt(text.encode())
    return encrypted_data.decode()


def decrypt_string(encrypted_text: str, key: str) -> str:
    """
    description:
        解密使用Fernet加密的字符串
    parameters:
        encrypted_text(str): 加密后的字符串
        key(str): 加密密钥
    return:
        str: 解密后的原始字符串
    """
    f = Fernet(key.encode())
    decrypted_data = f.decrypt(encrypted_text.encode())
    return decrypted_data.decode()


def decimal(num: float, precision=2):
    """
    description:
        保留小数点后precision位
    parameters:
        num(float): 需要保留小数点的数字
        precision(int): 保留小数点的位数
    return:
        num(float): 保留小数点后的数字
    """
    num_s = f"{num:.{precision}f}"
    return float(num_s)


def percentage(current, target):
    """
    description:
        计算当前值占总值的百分比
    parameters:
        current(float): 当前值
        target(float): 总值
    return:
        percentage_str(str): 百分比字符串
    """
    percentage = decimal((current / target) * 100)
    percentage_str = f"{percentage}%"
    return percentage_str


def size_unit_convert(size, input_unit="B", output_unit="MB", precision=2):
    """
    description:
        单位转换
    parameters:
        size(float): 需要转换的文件大小
        input_unit(str): 输入的单位，默认B
        output_unit(str): 输出的单位，默认MB
        precision(int): 保留小数点的位数，默认2
    return:
        size(float): 转换后的文件大小
    """
    size_unit_list = ["B", "KB", "MB", "GB", "TB"]
    if input_unit not in size_unit_list or output_unit not in size_unit_list:
        return size
    pos_input_unit = size_unit_list.index(input_unit)
    pos_output_unit = size_unit_list.index(output_unit)
    if pos_input_unit == pos_output_unit:
        return size

    mult_num = (
        1 / (1024 ** (pos_output_unit - pos_input_unit))
        if pos_input_unit < pos_output_unit
        else 1024 ** (pos_input_unit - pos_output_unit)
    )
    return decimal(size * mult_num, precision)


def split_content_into_sentences(
    content: str, remove_punctuation: bool = True
) -> tuple[list[str], bool]:
    """
    description:
        将内容按逗号和顿号分割成句子
    parameters:
        content(str): 需要分割的内容
    return:
        sentences(list[str]): 分割后的句子列表
        flag(bool): 是否分割成功
    """
    try:
        split_pattern = r"[。！？；，、：]"
        content = content.strip()
        sentences = re.split(split_pattern, content)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 对每一句话循环去除所有的空格
        sentences = [
            sentence.replace(" ", "")
            for sentence in sentences
            if sentence and sentence.strip() and sentence.strip() != ""
        ]

        if remove_punctuation:
            sentences = [re.sub(r"[^\w\s]", "", s) for s in sentences]
        return sentences, True
    except Exception as e:
        print(f"分割内容时发生错误: {traceback.format_exc()}")
        return [], False


def remove_all_punctuation(text: str) -> tuple[str, bool]:
    """
    description:
        去除字符串中的所有标点符号
    parameters:
        text(str): 需要处理的字符串
    return:
        text(str): 处理后的字符串
        flag(bool): 是否处理成功
    """
    try:
        # 使用正则表达式去除所有标点符号
        return re.sub(r"[^\w\s]", "", text), True
    except Exception as e:
        print(f"去除标点符号时发生错误: {traceback.format_exc()}")
        return text, False


def file_to_base64(file_path: str) -> str:
    """
    description:
        将文件转换为base64
    parameters:
        file_path(str): 文件路径
    return:
        base64_str(str): base64字符串
    """
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def execute_command(command: Union[str, List[str]]) -> str:
    """
    description:
        执行命令
    parameters:
        command(Union[str, List[str]]): 需要执行的命令
    return:
        result(str): 命令执行结果
    """
    try:
        if isinstance(command, str):
            command = command.split()
        result = subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.stdout.decode(), True
    except subprocess.CalledProcessError as e:
        print(
            f"执行命令失败，命令: {command}，错误信息: {e.stderr.decode() if e.stderr else str(e)}"
        )
        return e.stderr.decode() if e.stderr else "", False


async def execute_command_async(command: Union[str, List[str]]) -> str:
    """
    description:
        异步执行命令
    parameters:
        command(Union[str, List[str]]): 需要执行的命令
    return:
        result(str): 命令执行结果
    """
    try:
        if isinstance(command, str):
            command = command.split()
        result = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        return stdout.decode(), True
    except subprocess.CalledProcessError as e:
        print(
            f"异步执行命令失败，命令: {command}，错误信息: {e.stderr.decode() if e.stderr else str(e)}"
        )
        return e.stderr.decode() if e.stderr else "", False


def get_variable_type(variable: object) -> str:
    """
    description:
        获取变量类型
    parameters:
        variable(object): 需要获取类型的变量
    return:
        variable_type(str): 变量类型
    """
    return type(variable).__name__


def extract_json_from_markdown(content: str) -> dict:
    """
    description:
        从Markdown文本中提取JSON内容
    parameters:
        content(str): Markdown文本
    return:
        json_content(dict): JSON内容
    """
    # 首先尝试匹配 ```json 格式
    json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    # 如果没有找到 ```json 格式，尝试直接匹配 JSON 对象
    json_match = re.search(r"({[\s\S]*})", content)
    if json_match:
        return json.loads(json_match.group(1))

    # 如果还是没有找到，尝试直接解析整个内容
    try:
        return json.loads(content)
    except:
        return {}


def get_ssh_config():
    """
    description:
        获取~/.ssh/config中的配置信息
    return:
        configs(list): 配置信息 [{"host": "", "hostname": "", "user": "", "identityfile": ""}, ...]
    """
    ssh_config_file = os.path.expanduser("~/.ssh/config")
    configs = []
    current_config = {}

    with open(ssh_config_file, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("Host "):
                if current_config:
                    configs.append(current_config)
                current_config = {}
                current_config["host"] = line.split()[1]
            elif line.startswith("HostName "):
                current_config["hostname"] = line.split()[1]
            elif line.startswith("User "):
                current_config["user"] = line.split()[1]
            elif line.startswith("IdentityFile "):
                current_config["identityfile"] = os.path.expanduser(line.split()[1])

    if current_config:
        configs.append(current_config)

    return configs


def execute_command_through_ssh_stream(
    hostname: str, command: str
) -> Generator[str, None, None]:
    """
    description:
        SSH到线上机器并执行命令
    parameters:
        hostname(str): 线上机器的IP地址
        command(str): 要执行的命令
    return:
        output(generator): 命令的输出生成器
    """
    ssh_config = next(
        (config for config in get_ssh_config() if config.get("hostname") == hostname),
        None,
    )
    if not ssh_config:
        raise Exception("SSH 配置获取失败")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        ssh_config["hostname"],
        username=ssh_config["user"],
        key_filename=ssh_config["identityfile"],
    )
    try:
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        stdout.channel.settimeout(None)

        while line := stdout.readline():
            yield line.strip() + "\n"

        if stderr.readline():
            raise Exception(f"在host: {hostname}上执行命令{command}失败")
    finally:
        ssh.close()


def execute_command_through_ssh(hostname: str, command: str) -> str:
    """
    description:
        SSH到线上机器并执行命令
    parameters:
        hostname(str): 线上机器的IP地址
        command(str): 要执行的命令
    return:
        output(str): 命令的输出
    """
    result = ""
    for line in execute_command_through_ssh_stream(hostname, command):
        result += line
    return result
