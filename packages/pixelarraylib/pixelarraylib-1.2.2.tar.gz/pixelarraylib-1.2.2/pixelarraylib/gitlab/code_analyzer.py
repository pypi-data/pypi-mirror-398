import aiohttp
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional, Tuple


class GitLabCodeAnalyzer:
    def __init__(self, gitlab_url, private_token):
        """
        description:
            初始化GitLab代码分析器
        parameters:
            gitlab_url(str): GitLab服务器URL
            private_token(str): GitLab私有访问令牌
        """
        self.gitlab_url = gitlab_url.rstrip("/")
        self.headers = {"PRIVATE-TOKEN": private_token}
        self.session = None

    async def __aenter__(self):
        """
        description:
            异步上下文管理器入口
        return:
            self(GitLabCodeAnalyzer): 返回自身
        """
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        description:
            异步上下文管理器出口
        parameters:
            exc_type(type): 异常类型
            exc_val(Exception): 异常值
            exc_tb(traceback): 异常追踪信息
        """
        if self.session:
            await self.session.close()

    async def _get_session(self):
        """
        description:
            获取或创建aiohttp会话
        return:
            session(aiohttp.ClientSession): aiohttp会话对象
        """
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def _close_session(self):
        """
        description:
            关闭aiohttp会话
        """
        if self.session:
            await self.session.close()
            self.session = None

    async def get_project_id_name_list(self, group_id=None, owned_only=True):
        """
        description:
            获取项目的 ID 和名称列表
        parameters:
            group_id(int): 组ID，如果指定则只获取该组的项目
            owned_only(bool): 是否只获取用户拥有的项目，默认为True以提高速度
        return:
            project_list(list): 项目列表，每个元素为(id, name)元组
        """
        projects = await self.get_all_projects(
            group_id, owned_only=owned_only, membership_only=True
        )
        return [(p["id"], p["name"]) for p in projects]

    async def get_all_projects(
        self, group_id=None, owned_only=True, membership_only=True
    ):
        """
        description:
            获取项目列表
        parameters:
            group_id(int): 组ID，如果指定则只获取该组的项目
            owned_only(bool): 是否只获取用户拥有的项目
            membership_only(bool): 是否只获取用户有权限的项目
        return:
            projects(list): 项目列表
        """
        if group_id:
            url = f"{self.gitlab_url}/api/v4/groups/{group_id}/projects"
        else:
            url = f"{self.gitlab_url}/api/v4/projects"

        # 构建查询参数
        params = {
            "page": 1,
            "per_page": 100,
            "simple": "true",  # 只返回基本信息，提高速度
            "order_by": "name",
            "sort": "asc",
        }

        if owned_only:
            params["owned"] = "true"
        if membership_only:
            params["membership"] = "true"

        projects = []
        page = 1
        session = await self._get_session()

        while True:
            params["page"] = page
            async with session.get(url, params=params) as response:
                # 检查响应状态
                if response.status != 200:
                    print(f"请求失败，状态码: {response.status}")
                    text = await response.text()
                    print(f"响应内容: {text}")
                    break

                # 获取响应数据
                data = await response.json()
                print(f"第{page}页数据: {len(data)}个项目")

                # 如果返回的数据为空，说明已经到达最后一页
                if not data:
                    break

                projects.extend(data)
                page += 1

                # 如果返回的数据少于per_page，说明这是最后一页
                if len(data) < params["per_page"]:
                    break

        print(f"总共获取到 {len(projects)} 个项目")
        return projects

    async def get_project_code_stats(self, project_id, since=None, until=None):
        """
        description:
            获取项目的代码统计，包括每个贡献者的提交数和代码行数变化
        parameters:
            project_id(int): 项目ID
            since(str): 开始日期，格式为YYYY-MM-DD
            until(str): 结束日期，格式为YYYY-MM-DD
        return:
            stats(dict): 代码统计信息
        """
        session = await self._get_session()

        # 获取贡献者基本信息
        contributors_url = (
            f"{self.gitlab_url}/api/v4/projects/{project_id}/repository/contributors"
        )
        async with session.get(contributors_url) as response:
            if response.status != 200:
                print(f"获取贡献者信息失败，状态码: {response.status}")
                return []
            contributors = await response.json()

        # 获取所有提交的统计信息（避免重复计算）
        all_commits_stats = await self._get_all_commits_stats(
            session, project_id, since, until
        )

        # 为每个贡献者分配统计信息
        for contributor in contributors:
            author_email = contributor.get("email", "")
            author_name = contributor.get("name", "")

            # 从所有提交中筛选该贡献者的提交
            contributor_commits = [
                commit
                for commit in all_commits_stats
                if commit.get("author_email", "").lower() == author_email.lower()
            ]

            # 计算该贡献者的统计信息
            # 注意：这里统计的是代码变化量，不是最终代码量
            total_additions = sum(
                commit.get("additions", 0) for commit in contributor_commits
            )
            total_deletions = sum(
                commit.get("deletions", 0) for commit in contributor_commits
            )

            # 更新贡献者统计信息
            contributor["additions"] = total_additions
            contributor["deletions"] = total_deletions
            contributor["total_changes"] = total_additions + total_deletions
            contributor["commit_details"] = contributor_commits

            # 添加净变化行数（新增 - 删除）
            contributor["net_changes"] = total_additions - total_deletions

        return contributors

    async def _get_all_commits_stats(self, session, project_id, since=None, until=None):
        """获取项目中所有提交的统计信息"""
        commits_url = (
            f"{self.gitlab_url}/api/v4/projects/{project_id}/repository/commits"
        )
        commit_params = {
            "per_page": 100,
            "ref_name": "master",  # 只统计master分支的提交
        }

        if since:
            commit_params["since"] = since
        if until:
            commit_params["until"] = until

        all_commits = []
        page = 1

        while True:
            commit_params["page"] = page
            async with session.get(commits_url, params=commit_params) as response:
                if response.status != 200:
                    print(f"获取提交列表失败，状态码: {response.status}")
                    break

                commits = await response.json()
                if not commits:
                    break

                all_commits.extend(commits)
                page += 1

                if len(commits) < commit_params["per_page"]:
                    break

        # 过滤掉合并提交，只保留真正的功能提交
        filtered_commits = []
        for commit in all_commits:
            title = commit.get("title", "").lower()
            message = commit.get("message", "").lower()

            # 过滤掉合并提交
            if (
                title.startswith("merge branch")
                or title.startswith("merge pull request")
                or "merge" in title
                and "into" in title
            ):
                continue

            filtered_commits.append(commit)

        print(f"总提交数: {len(all_commits)}, 过滤后提交数: {len(filtered_commits)}")

        # 并发获取每个提交的详细统计
        commit_tasks = []
        for commit in filtered_commits:
            task = self._get_commit_details(session, project_id, commit)
            commit_tasks.append(task)

        # 等待所有提交详情获取完成
        commit_details_list = await asyncio.gather(*commit_tasks)

        # 过滤掉None值
        return [commit for commit in commit_details_list if commit is not None]

    async def _get_commit_details(self, session, project_id, commit):
        """获取单个提交的详细信息"""
        commit_id = commit["id"]
        commit_stats_url = f"{self.gitlab_url}/api/v4/projects/{project_id}/repository/commits/{commit_id}"

        async with session.get(commit_stats_url) as commit_response:
            if commit_response.status == 200:
                commit_data = await commit_response.json()
                stats = commit_data.get("stats", {})

                # 返回详细的提交信息
                return {
                    "id": commit_id,
                    "short_id": commit.get("short_id", ""),
                    "title": commit.get("title", ""),
                    "message": commit.get("message", ""),
                    "author_name": commit.get("author_name", ""),
                    "author_email": commit.get("author_email", ""),
                    "committed_date": commit.get("committed_date", ""),
                    "created_at": commit.get("created_at", ""),
                    "additions": stats.get("additions", 0),
                    "deletions": stats.get("deletions", 0),
                    "total": stats.get("total", 0),
                }
            else:
                return None

    async def generate_code_report(self, group_id=None, since=None, until=None):
        """
        description:
            生成代码统计报告
        parameters:
            group_id(int): 组ID，如果指定则只获取该组的项目
            since(str): 开始日期，格式为YYYY-MM-DD
            until(str): 结束日期，格式为YYYY-MM-DD
        return:
            report_data(list): 代码统计报告数据
        """
        projects = await self.get_all_projects(group_id)
        report_data = []

        # 并发处理所有项目
        project_tasks = []
        for project in projects:
            task = self._process_project_for_report(project, since, until)
            project_tasks.append(task)

        # 等待所有项目处理完成
        project_results = await asyncio.gather(*project_tasks)

        # 汇总所有项目的数据
        for project_data in project_results:
            report_data.extend(project_data)

        if not report_data:
            print("没有找到任何贡献者数据")
            return pd.DataFrame()

        return report_data

    async def _process_project_for_report(self, project, since=None, until=None):
        """处理单个项目的报告数据"""
        project_id = project["id"]
        project_name = project["name"]
        project_data = []

        print(f"分析项目: {project_name}")

        # 获取贡献者统计，包含代码行数信息
        contributors = await self.get_project_code_stats(
            project_id, since=since, until=until
        )

        for contributor in contributors:
            project_data.append(
                {
                    "project": project_name,
                    "author": contributor["name"],
                    "email": contributor["email"],
                    "commits": contributor["commits"],
                    "additions": contributor.get("additions", 0),
                    "deletions": contributor.get("deletions", 0),
                    "total_changes": contributor.get("total_changes", 0),
                    "net_changes": contributor.get("net_changes", 0),
                }
            )

        return project_data

    async def get_commit_details_report(self, project_id, since=None, until=None):
        """
        description:
            获取详细的提交信息报告
        parameters:
            project_id(int): 项目ID
            since(str): 开始日期，格式为YYYY-MM-DD
            until(str): 结束日期，格式为YYYY-MM-DD
        return:
            commits(List[Dict]): 包含所有提交详细信息的列表
        """
        contributors = await self.get_project_code_stats(
            project_id, since=since, until=until
        )

        all_commits = []
        for contributor in contributors:
            commit_details = contributor.get("commit_details", [])
            for commit in commit_details:
                commit["contributor_name"] = contributor.get("name", "")
                commit["contributor_email"] = contributor.get("email", "")
                all_commits.append(commit)

        # 按提交日期排序
        all_commits.sort(key=lambda x: x.get("committed_date", ""), reverse=True)

        return all_commits
