import subprocess
import tempfile
import os
import re
import traceback
from typing import List, Dict, Optional
from pixelarraylib.system.common import execute_command


class CronManager:
    def __init__(self):
        self.cron_file = self._load_crontab()

    def _load_crontab(self) -> str:
        """
        description:
            加载crontab文件
        return:
            crontab_file(str): crontab文件内容
        """
        output, success = execute_command(["crontab", "-l"])
        if success:
            return output
        else:
            return ""

    def _save_crontab(self) -> bool:
        """
        description:
            保存crontab文件
        return:
            success(bool): 是否成功
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            content = self.cron_file
            if content and not content.endswith("\n"):
                content += "\n"
            f.write(content)
            temp_file = f.name

        _, success = execute_command(["crontab", temp_file])
        os.remove(temp_file)
        return success

    def _extract_job_name_from_comment(self, line: str) -> str:
        """
        description:
            从cron行中提取任务名称（如果有注释）
        parameters:
            line(str): cron行
        return:
            job_name(str): 任务名称
        """
        match = re.search(r"# JOB_NAME:\s*([^\s]+)", line)
        if match:
            return match.group(1)
        return None

    def _extract_status_from_comment(self, line: str) -> str:
        """
        description:
            从cron行中提取状态（STATUS:OPEN 或 STATUS:CLOSE）
        parameters:
            line(str): cron行
        return:
            status(str): 状态，OPEN 或 CLOSE，默认为 OPEN
        """
        match = re.search(r"STATUS:\s*(\w+)", line)
        if match:
            return match.group(1).upper()
        return "OPEN"

    def _generate_job_name_from_command(self, command: str) -> str:
        """
        description:
            从命令中生成任务名称
        parameters:
            command(str): 任务命令
        return:
            job_name(str): 生成的任务名称
        """
        # 尝试从命令中提取模块名
        if "python -m" in command:
            # 提取模块名
            match = re.search(r"python -m\s+([^\s]+)", command)
            if match:
                module_name = match.group(1)
                # 将模块名转换为任务名
                return module_name.replace(".", "_").replace("/", "_")

        # 如果无法提取模块名，使用命令的hash值
        import hashlib

        return f"task_{hashlib.md5(command.encode()).hexdigest()[:8]}"

    def _validate_schedule(self, schedule: str) -> bool:
        """
        description:
            验证cron时间格式
        parameters:
            schedule(str): 任务时间安排
        return:
            valid(bool): 是否有效
        """
        parts = schedule.strip().split()
        if len(parts) != 5:
            return False

        ranges = [
            (0, 59),  # 分钟
            (0, 23),  # 小时
            (1, 31),  # 日期
            (1, 12),  # 月份
            (0, 6),  # 星期 (0=周日)
        ]

        try:
            for i, part in enumerate(parts):
                if part == "*":
                    continue

                min_val, max_val = ranges[i]

                if "," in part:
                    for val in part.split(","):
                        if "-" in val:
                            range_parts = val.split("-")
                            if len(range_parts) == 2:
                                start = int(range_parts[0].strip())
                                end = int(range_parts[1].strip())
                                if not (
                                    min_val <= start <= max_val
                                    and min_val <= end <= max_val
                                    and start <= end
                                ):
                                    return False
                            else:
                                return False
                        else:
                            val_int = int(val.strip())
                            if not (min_val <= val_int <= max_val):
                                return False
                elif "-" in part:
                    if "/" in part:
                        range_part, step_part = part.split("/")
                        step = int(step_part.strip())
                        if step <= 0:
                            return False

                        if "-" in range_part:
                            start, end = range_part.split("-")
                            start = int(start.strip())
                            end = int(end.strip())
                            if not (
                                min_val <= start <= max_val
                                and min_val <= end <= max_val
                                and start <= end
                            ):
                                return False
                        else:
                            base = int(range_part.strip())
                            if not (min_val <= base <= max_val):
                                return False
                    else:
                        start, end = part.split("-")
                        start = int(start.strip())
                        end = int(end.strip())
                        if not (
                            min_val <= start <= max_val
                            and min_val <= end <= max_val
                            and start <= end
                        ):
                            return False
                elif "/" in part:
                    base, step = part.split("/")
                    step = int(step.strip())
                    if step <= 0:
                        return False

                    if base == "*":
                        continue
                    base_int = int(base.strip())
                    if not (min_val <= base_int <= max_val):
                        return False
                else:
                    val = int(part)
                    if not (min_val <= val <= max_val):
                        return False
        except (ValueError, IndexError):
            return False

        return True

    def list_cron_jobs(self) -> List[Dict[str, str]]:
        """
        description:
            获取所有cron任务
        return:
            jobs(list[dict]): 所有cron任务
        """
        jobs = []
        if not self.cron_file:
            return jobs

        lines = self.cron_file.strip().split("\n")
        for line in lines:
            original_line = line
            line = line.strip()

            # 检查是否是被注释的cron任务行（以#开头但包含JOB_NAME）
            is_commented = line.startswith("#")
            if is_commented:
                # 移除开头的#，继续处理
                line = line[1:].strip()

            # 检查是否包含JOB_NAME注释（无论是启用还是禁用状态）
            job_name = self._extract_job_name_from_comment(original_line)
            if not job_name:
                # 如果不是我们的任务行（没有JOB_NAME），跳过
                if is_commented or not line or line.startswith("#"):
                    continue
                # 对于没有JOB_NAME的普通cron行，尝试从命令生成任务名
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    schedule = " ".join(parts[:5])
                    command = parts[5]
                    job_name = self._generate_job_name_from_command(command)
                    status = "OPEN" if not is_commented else "CLOSE"
                    jobs.append(
                        {
                            "job_name": job_name,
                            "schedule": schedule,
                            "command": command,
                            "raw_line": original_line,
                            "enabled": not is_commented,
                        }
                    )
                continue

            # 提取状态
            status = self._extract_status_from_comment(original_line)
            enabled = not is_commented and status == "OPEN"

            # 解析cron行
            parts = line.split(None, 5)
            if len(parts) >= 6:
                schedule = " ".join(parts[:5])
                command_with_comment = parts[5]
                command = command_with_comment

                # 从命令中移除注释部分
                # 移除 JOB_NAME 注释
                if f" # JOB_NAME: {job_name}" in command:
                    command = command.replace(f" # JOB_NAME: {job_name}", "")
                # 移除 STATUS 注释
                status_pattern = r"\s*STATUS:\s*\w+"
                command = re.sub(status_pattern, "", command).strip()

                jobs.append(
                    {
                        "job_name": job_name,
                        "schedule": schedule,
                        "command": command,
                        "raw_line": original_line,
                        "enabled": enabled,
                    }
                )

        return jobs

    def get_job_by_name(self, job_name: str) -> Optional[Dict[str, str]]:
        """
        description:
            根据名称获取任务
        parameters:
            job_name(str): 任务名称
        return:
            job(dict): 任务
        """
        jobs = self.list_cron_jobs()
        for job in jobs:
            if job["job_name"] == job_name:
                return job
        return None

    def add_cron_job(
        self, job_name: str, command: str, schedule: str, enabled: bool = True
    ) -> bool:
        """
        description:
            添加cron任务
        parameters:
            job_name(str): 任务名称
            command(str): 任务命令
            schedule(str): 任务时间安排
            enabled(bool): 是否启用，默认为True
        return:
            success(bool): 是否成功
        """
        if self.job_exists(job_name):
            raise ValueError(f"任务 '{job_name}' 已存在")
        if not self._validate_schedule(schedule):
            raise ValueError(f"无效的cron时间格式: {schedule}")

        status = "OPEN" if enabled else "CLOSE"
        new_line = f"{schedule} {command} # JOB_NAME: {job_name} STATUS:{status}"

        # 如果禁用，在行首添加#
        if not enabled:
            new_line = f"# {new_line}"

        if self.cron_file:
            self.cron_file += f"\n{new_line}"
        else:
            self.cron_file = new_line

        success = self._save_crontab()
        return success

    def remove_cron_job(self, job_name: str):
        """
        description:
            删除cron任务
        parameters:
            job_name(str): 任务名称
        return:
            success(bool): 是否成功
        """
        if not self.job_exists(job_name):
            raise ValueError(f"任务 '{job_name}' 不存在")

        lines = self.cron_file.strip().split("\n")
        self.cron_file = "\n".join(
            [
                line
                for line in lines
                if not (line.strip() and f"# JOB_NAME: {job_name}" in line)
            ]
        )
        success = self._save_crontab()
        return success

    def enable_cron_job(self, job_name: str) -> bool:
        """
        description:
            启用cron任务（移除行首的#注释）
        parameters:
            job_name(str): 任务名称
        return:
            success(bool): 是否成功
        """
        if not self.job_exists(job_name):
            raise ValueError(f"任务 '{job_name}' 不存在")

        lines = self.cron_file.strip().split("\n")
        updated_lines = []

        for line in lines:
            if f"# JOB_NAME: {job_name}" in line:
                # 移除行首的#（如果存在）
                if line.strip().startswith("#"):
                    line = line.strip()[1:].strip()

                # 更新STATUS为OPEN
                line = re.sub(r"STATUS:\s*\w+", "STATUS:OPEN", line)
                updated_lines.append(line)
            else:
                updated_lines.append(line)

        self.cron_file = "\n".join(updated_lines)
        success = self._save_crontab()
        return success

    def disable_cron_job(self, job_name: str) -> bool:
        """
        description:
            禁用cron任务（在行首添加#注释）
        parameters:
            job_name(str): 任务名称
        return:
            success(bool): 是否成功
        """
        if not self.job_exists(job_name):
            raise ValueError(f"任务 '{job_name}' 不存在")

        lines = self.cron_file.strip().split("\n")
        updated_lines = []

        for line in lines:
            if f"# JOB_NAME: {job_name}" in line:
                # 如果还没有被注释，添加#
                if not line.strip().startswith("#"):
                    line = f"# {line.strip()}"

                # 更新STATUS为CLOSE
                line = re.sub(r"STATUS:\s*\w+", "STATUS:CLOSE", line)
                # 如果原来没有STATUS，添加STATUS:CLOSE
                if "STATUS:" not in line:
                    line = line.rstrip() + " STATUS:CLOSE"
                updated_lines.append(line)
            else:
                updated_lines.append(line)

        self.cron_file = "\n".join(updated_lines)
        success = self._save_crontab()
        return success

    def trigger_cron_job(self, job_name: str) -> tuple[str, bool]:
        """
        description:
            手动触发cron任务
        parameters:
            job_name(str): 任务名称
        return:
            output(str): 命令执行输出
            success(bool): 是否成功
        """
        job = self.get_job_by_name(job_name)
        if not job:
            raise ValueError(f"任务 '{job_name}' 不存在")

        # 使用shell执行命令，确保环境变量和路径正确
        command = job["command"]
        print(f"执行cron任务命令: {command}")

        try:
            # 使用subprocess直接执行命令，设置工作目录和环境变量
            # 从命令中提取工作目录，如果命令以cd开头
            working_dir = None
            if command.startswith("cd "):
                # 提取cd后的目录
                parts = command.split("&&", 1)
                if len(parts) > 1:
                    cd_part = parts[0].strip()
                    if cd_part.startswith("cd "):
                        working_dir = cd_part[3:].strip()
                        # 更新命令，移除cd部分
                        command = parts[1].strip()

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir or os.getcwd(),  # 使用提取的工作目录或当前目录
                env={
                    **os.environ,  # 继承当前环境变量
                    "PYTHONPATH": working_dir or os.getcwd(),  # 设置Python路径
                },
                timeout=300,  # 5分钟超时
            )

            success = result.returncode == 0
            output = result.stdout + result.stderr if result.stderr else result.stdout

            print(f"命令执行结果: success={success}, returncode={result.returncode}")
            print(f"输出: {output}")

            return output, success

        except subprocess.TimeoutExpired:
            error_msg = f"任务执行超时: {command}"
            print(error_msg)
            return error_msg, False
        except Exception as e:
            error_msg = f"执行任务时发生错误: {str(e)}"
            print(error_msg)
            return error_msg, False

    def job_exists(self, job_name: str) -> bool:
        """
        description:
            检查任务是否存在
        parameters:
            job_name(str): 任务名称
        return:
            exists(bool): 是否存在
        """
        return self.get_job_by_name(job_name) is not None

    def change_cron_job_schedule(self, job_name: str, schedule: str) -> bool:
        """
        description:
            修改cron任务的时间安排
        parameters:
            job_name(str): 任务名称
            schedule(str): 任务时间安排
        return:
            success(bool): 是否成功
        """
        if not self.job_exists(job_name):
            raise ValueError(f"任务 '{job_name}' 不存在")

        if not self._validate_schedule(schedule):
            raise ValueError(f"无效的cron时间格式: {schedule}")

        lines = self.cron_file.strip().split("\n")
        updated_lines = []

        for line in lines:
            if f"# JOB_NAME: {job_name}" in line:
                # 检查是否被注释
                is_commented = line.strip().startswith("#")
                if is_commented:
                    line = line.strip()[1:].strip()

                parts = line.split(None, 5)
                if len(parts) >= 6:
                    command_with_comment = parts[5]
                    command = command_with_comment
                    # 移除旧的注释
                    if f" # JOB_NAME: {job_name}" in command:
                        command = command.replace(f" # JOB_NAME: {job_name}", "")
                    # 移除旧的STATUS
                    command = re.sub(r"\s*STATUS:\s*\w+", "", command).strip()

                    # 提取当前状态
                    status = self._extract_status_from_comment(line)
                    new_line = (
                        f"{schedule} {command} # JOB_NAME: {job_name} STATUS:{status}"
                    )

                    # 如果原来是被注释的，保持注释状态
                    if is_commented:
                        new_line = f"# {new_line}"

                    updated_lines.append(new_line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        self.cron_file = "\n".join(updated_lines)
        success = self._save_crontab()
        return success
