# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import json

from typing import List

from alibabacloud_polardb20170801.client import Client as polardb20170801Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_polardb20170801 import models as polardb_20170801_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class PolarDBUtils:
    def __init__(self, region_id: str, access_key_id: str, access_key_secret: str):
        """
        description:
            初始化PolarDB工具类
        parameters:
            region_id(str): 阿里云区域ID
            access_key_id(str): 阿里云访问密钥ID
            access_key_secret(str): 阿里云访问密钥Secret
        """
        self.region_id = region_id
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.client = self._create_client()

    def _create_client(self) -> polardb20170801Client:
        """
        description:
            创建PolarDB客户端
        return:
            polardb20170801Client: PolarDB客户端实例
        """
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id,
        )
        config.endpoint = f"polardb.aliyuncs.com"
        return polardb20170801Client(config)

    def list_regions(
        self,
    ) -> tuple[dict, bool]:
        describe_regions_request = polardb_20170801_models.DescribeRegionsRequest()
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.describe_regions_with_options(
                describe_regions_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            print("error", error)
            return {}, False

    async def list_regions_async(self) -> tuple[dict, bool]:
        describe_regions_request = polardb_20170801_models.DescribeRegionsRequest()
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.describe_regions_with_options_async(
                describe_regions_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            print("error", error)
            return {}, False

    def list_region_ids(self) -> tuple[list, bool]:
        """
        description:
            列出PolarDB区域ID
        return:
            region_ids: 区域ID列表
            success: 操作是否成功
        """
        resp, success = self.list_regions()
        if not success:
            return [], False
        return [
            region["RegionId"] for region in resp.get("Regions", {}).get("Region", [])
        ], True

    async def list_region_ids_async(self) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB区域ID
        return:
            region_ids: 区域ID列表
            success: 操作是否成功
        """
        resp, success = await self.list_regions_async()
        if not success:
            return [], False
        return [
            region["RegionId"] for region in resp.get("Regions", {}).get("Region", [])
        ], True

    def list_clusters(
        self,
    ) -> tuple[dict, bool]:
        describe_dbclusters_request = polardb_20170801_models.DescribeDBClustersRequest(
            region_id=self.region_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.describe_dbclusters_with_options(
                describe_dbclusters_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            print("error", error)
            return {}, False

    def list_cluster_ids(
        self,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB集群ID
        return:
            cluster_ids: 集群ID列表
            success: 操作是否成功
        """
        try:
            resp, success = self.list_clusters()
            if not success:
                return [], False

            clusters = resp.get("Items", {}).get("DBCluster", [])
            return [cluster["DBClusterId"] for cluster in clusters], True
        except Exception as error:
            print("error", error)
            return [], False

    async def list_clusters_async(
        self,
    ) -> tuple[dict, bool]:
        describe_dbclusters_request = polardb_20170801_models.DescribeDBClustersRequest(
            region_id=self.region_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.describe_dbclusters_with_options_async(
                describe_dbclusters_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            print("error", error)
            return {}, False

    async def list_cluster_ids_async(
        self,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB集群ID
        return:
            cluster_ids: 集群ID列表
            success: 操作是否成功
        """
        try:
            resp, success = await self.list_clusters_async()
            if not success:
                return [], False
            clusters = resp.get("Items", {}).get("DBCluster", [])
            return [cluster["DBClusterId"] for cluster in clusters], True
        except Exception as error:
            print("error", error)
            return [], False

    def list_character_set_names(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB字符集名称
        parameters:
            cluster_id(str): 集群ID
        return:
            character_set_names: 字符集名称列表
            success: 操作是否成功
        """
        describe_character_set_name_request = (
            polardb_20170801_models.DescribeCharacterSetNameRequest(
                region_id=self.region_id, dbcluster_id=cluster_id
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.describe_character_set_name_with_options(
                describe_character_set_name_request, runtime
            )
            return (
                resp.body.to_map()
                .get("CharacterSetNameItems", {})
                .get("CharacterSetName", []),
                True,
            )
        except Exception as error:
            print("error", error)
            return [], False

    async def list_character_set_names_async(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB字符集名称
        parameters:
            cluster_id(str): 集群ID
        return:
            character_set_names: 字符集名称列表
            success: 操作是否成功
        """
        describe_character_set_name_request = (
            polardb_20170801_models.DescribeCharacterSetNameRequest(
                region_id=self.region_id, dbcluster_id=cluster_id
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.describe_character_set_name_with_options_async(
                describe_character_set_name_request, runtime
            )
            return (
                resp.body.to_map()
                .get("CharacterSetNameItems", {})
                .get("CharacterSetName", []),
                True,
            )
        except Exception as error:
            print("error", error)
            return [], False

    def create_database(
        self,
        cluster_id: str,
        database_name: str,
        character_set_name: str = "utf8mb4",
    ) -> bool:
        """
        description:
            创建PolarDB数据库
        parameters:
            cluster_id(str): 集群ID
            database_name(str): 数据库名称
            character_set_name(str): 字符集名称
        return:
            bool: 创建结果
        """
        create_database_request = polardb_20170801_models.CreateDatabaseRequest(
            character_set_name=character_set_name,
            dbcluster_id=cluster_id,
            dbname=database_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.create_database_with_options(
                create_database_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    async def create_database_async(
        self,
        cluster_id: str,
        database_name: str,
        character_set_name: str = "utf8mb4",
    ) -> bool:
        """
        description:
            异步创建PolarDB数据库
        parameters:
            cluster_id(str): 集群ID
            database_name(str): 数据库名称
            character_set_name(str): 字符集名称
        return:
            bool: 创建结果
        """
        create_database_request = polardb_20170801_models.CreateDatabaseRequest(
            character_set_name=character_set_name,
            dbcluster_id=cluster_id,
            dbname=database_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.create_database_with_options_async(
                create_database_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    def delete_database(
        self,
        cluster_id: str,
        database_name: str,
    ) -> bool:
        """
        description:
            删除PolarDB数据库
        parameters:
            cluster_id(str): 集群ID
            database_name(str): 数据库名称
        return:
            bool: 删除结果
        """
        delete_database_request = polardb_20170801_models.DeleteDatabaseRequest(
            dbcluster_id=cluster_id,
            dbname=database_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.delete_database_with_options(
                delete_database_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            return False

    async def delete_database_async(
        self,
        cluster_id: str,
        database_name: str,
    ) -> bool:
        """
        description:
            异步删除PolarDB数据库
        parameters:
            cluster_id(str): 集群ID
            database_name(str): 数据库名称
        return:
            bool: 删除结果
        """
        delete_database_request = polardb_20170801_models.DeleteDatabaseRequest(
            dbcluster_id=cluster_id,
            dbname=database_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.delete_database_with_options_async(
                delete_database_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    def list_databases(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB数据库
        parameters:
            cluster_id(str): 集群ID
        return:
            databases: 数据库列表
            success: 操作是否成功
        """
        describe_databases_request = polardb_20170801_models.DescribeDatabasesRequest(
            dbcluster_id=cluster_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.describe_databases_with_options(
                describe_databases_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            print("error", error)
            return [], False

    async def list_databases_async(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB数据库
        parameters:
            cluster_id(str): 集群ID
        return:
            databases: 数据库列表
            success: 操作是否成功
        """
        describe_databases_request = polardb_20170801_models.DescribeDatabasesRequest(
            dbcluster_id=cluster_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.describe_databases_with_options_async(
                describe_databases_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            print("error", error)
            return [], False

    def list_database_names(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB数据库名称
        parameters:
            cluster_id(str): 集群ID
        return:
            database_names: 数据库名称列表
            success: 操作是否成功
        """
        try:
            resp, success = self.list_databases(cluster_id)
            if not success:
                return [], False

            return [
                database["DBName"]
                for database in resp.get("Databases", {}).get("Database", [])
            ], True
        except Exception as error:
            print("error", error)
            return [], False

    async def list_database_names_async(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB数据库名称
        parameters:
            cluster_id(str): 集群ID
        return:
            database_names: 数据库名称列表
            success: 操作是否成功
        """
        try:
            resp, success = await self.list_databases_async(cluster_id)
            if not success:
                return [], False

            return [
                database["DBName"]
                for database in resp.get("Databases", {}).get("Database", [])
            ], True
        except Exception as error:
            print("error", error)
            return [], False

    def list_accounts(
        self,
        cluster_id: str,
        account_name: str = None,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB账号
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
        return:
            accounts: 账号列表
            success: 操作是否成功
        """
        describe_accounts_request = polardb_20170801_models.DescribeAccountsRequest(
            dbcluster_id=cluster_id,
            account_name=account_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.describe_accounts_with_options(
                describe_accounts_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            return [], False

    async def list_accounts_async(
        self,
        cluster_id: str,
        account_name: str = None,
    ) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB账号
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
        return:
            accounts: 账号列表
            success: 操作是否成功
        """
        describe_accounts_request = polardb_20170801_models.DescribeAccountsRequest(
            dbcluster_id=cluster_id,
            account_name=account_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.describe_accounts_with_options_async(
                describe_accounts_request, runtime
            )
            return resp.body.to_map(), True
        except Exception as error:
            return [], False

    def list_account_names(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB账号名称
        parameters:
            cluster_id(str): 集群ID
        return:
            account_names: 账号名称列表
            success: 操作是否成功
        """
        try:
            resp, success = self.list_accounts(cluster_id)
            if not success:
                return [], False

            return [
                account["AccountName"] for account in resp.get("Accounts", [])
            ], True
        except Exception as error:
            return [], False

    async def list_account_names_async(
        self,
        cluster_id: str,
    ) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB账号名称
        parameters:
            cluster_id(str): 集群ID
        return:
            account_names: 账号名称列表
            success: 操作是否成功
        """
        try:
            resp, success = await self.list_accounts_async(cluster_id)
            if not success:
                return [], False

            return [
                account["AccountName"] for account in resp.get("Accounts", [])
            ], True
        except Exception as error:
            return [], False

    def create_account(
        self,
        cluster_id: str,
        account_name: str,
        account_password: str,
        account_type: str = "Normal",
    ) -> bool:
        """
        description:
            创建PolarDB账号
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            account_password(str): 账号密码
            account_type(str): 账号类型
        return:
            bool: 创建结果
        """
        create_account_request = polardb_20170801_models.CreateAccountRequest(
            dbcluster_id=cluster_id,
            account_name=account_name,
            account_password=account_password,
            account_type=account_type,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.create_account_with_options(
                create_account_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    async def create_account_async(
        self,
        cluster_id: str,
        account_name: str,
        account_password: str,
        account_type: str = "Normal",
    ) -> bool:
        """
        description:
            异步创建PolarDB账号
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            account_password(str): 账号密码
            account_type(str): 账号类型
        return:
            bool: 创建结果
        """
        create_account_request = polardb_20170801_models.CreateAccountRequest(
            dbcluster_id=cluster_id,
            account_name=account_name,
            account_password=account_password,
            account_type=account_type,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.create_account_with_options_async(
                create_account_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    def delete_account(
        self,
        cluster_id: str,
        account_name: str,
    ) -> bool:
        """
        description:
            删除PolarDB账号
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
        return:
            bool: 删除结果
        """
        delete_account_request = polardb_20170801_models.DeleteAccountRequest(
            dbcluster_id=cluster_id,
            account_name=account_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.delete_account_with_options(
                delete_account_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            return False

    async def delete_account_async(
        self,
        cluster_id: str,
        account_name: str,
    ) -> bool:
        """
        description:
            异步删除PolarDB账号
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
        return:
            bool: 删除结果
        """
        delete_account_request = polardb_20170801_models.DeleteAccountRequest(
            dbcluster_id=cluster_id,
            account_name=account_name,
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.delete_account_with_options_async(
                delete_account_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            return False

    def modify_account_password(
        self,
        cluster_id: str,
        account_name: str,
        new_account_password: str,
    ) -> bool:
        """
        description:
            修改PolarDB账号密码
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            new_account_password(str): 新账号密码
        return:
            bool: 修改结果
        """
        modify_account_password_request = (
            polardb_20170801_models.ModifyAccountPasswordRequest(
                dbcluster_id=cluster_id,
                account_name=account_name,
                new_account_password=new_account_password,
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.modify_account_password_with_options(
                modify_account_password_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    async def modify_account_password_async(
        self,
        cluster_id: str,
        account_name: str,
        new_account_password: str,
    ) -> bool:
        """
        description:
            异步修改PolarDB账号密码
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            new_account_password(str): 新账号密码
        return:
            bool: 修改结果
        """
        modify_account_password_request = (
            polardb_20170801_models.ModifyAccountPasswordRequest(
                dbcluster_id=cluster_id,
                account_name=account_name,
                new_account_password=new_account_password,
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.modify_account_password_with_options_async(
                modify_account_password_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    def grant_account_privilege(
        self,
        cluster_id: str,
        account_name: str,
        database_name: str,
        account_privilege: str = "ReadWrite",
    ) -> bool:
        """
        description:
            授予PolarDB账号权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            database_name(str): 数据库名称
            account_privilege(str): 账号权限
        return:
            bool: 授予结果
        """
        grant_account_privilege_request = (
            polardb_20170801_models.GrantAccountPrivilegeRequest(
                account_privilege=account_privilege,
                dbname=database_name,
                account_name=account_name,
                dbcluster_id=cluster_id,
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.grant_account_privilege_with_options(
                grant_account_privilege_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    async def grant_account_privilege_async(
        self,
        cluster_id: str,
        account_name: str,
        database_name: str,
        account_privilege: str = "ReadWrite",
    ) -> bool:
        """
        description:
            异步授予PolarDB账号权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            database_name(str): 数据库名称
            account_privilege(str): 账号权限
        return:
            bool: 授予结果
        """
        grant_account_privilege_request = (
            polardb_20170801_models.GrantAccountPrivilegeRequest(
                account_privilege=account_privilege,
                dbname=database_name,
                account_name=account_name,
                dbcluster_id=cluster_id,
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.grant_account_privilege_with_options_async(
                grant_account_privilege_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    def revoke_account_privilege(
        self,
        cluster_id: str,
        account_name: str,
        database_name: str,
    ) -> bool:
        """
        description:
            撤销PolarDB账号权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            database_name(str): 数据库名称
        return:
            bool: 撤销结果
        """
        revoke_account_privilege_request = (
            polardb_20170801_models.RevokeAccountPrivilegeRequest(
                dbcluster_id=cluster_id,
                account_name=account_name,
                dbname=database_name,
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = self.client.revoke_account_privilege_with_options(
                revoke_account_privilege_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    async def revoke_account_privilege_async(
        self,
        cluster_id: str,
        account_name: str,
        database_name: str,
    ) -> bool:
        """
        description:
            异步撤销PolarDB账号权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            database_name(str): 数据库名称
        return:
            bool: 撤销结果
        """
        revoke_account_privilege_request = (
            polardb_20170801_models.RevokeAccountPrivilegeRequest(
                dbcluster_id=cluster_id,
                account_name=account_name,
                dbname=database_name,
            )
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await self.client.revoke_account_privilege_with_options_async(
                revoke_account_privilege_request, runtime
            )
            return True if resp.body.to_map().get("RequestId") else False
        except Exception as error:
            print("error", error)
            return False

    def list_account_privileges(
        self,
        cluster_id: str,
        account_name: str,
    ) -> tuple[list, bool]:
        """
        description:
            列出PolarDB账号权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
        return:
            list: 账号权限列表
            success: 操作是否成功
        """
        resp, success = self.list_accounts(cluster_id, account_name)
        if not success:
            return [], False

        database_privileges = resp.get("Accounts", [])[0].get("DatabasePrivileges", [])
        database_privileges = [
            {
                "database_name": privilege.get("DBName"),
                "account_privilege": privilege.get("AccountPrivilege"),
            }
            for privilege in database_privileges
        ]
        return database_privileges, True

    async def list_account_privileges_async(
        self,
        cluster_id: str,
        account_name: str,
    ) -> tuple[list, bool]:
        """
        description:
            异步列出PolarDB账号权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
        return:
            list: 账号权限列表
            success: 操作是否成功
        """
        resp, success = await self.list_accounts_async(cluster_id, account_name)
        if not success:
            return [], False

        database_privileges = resp.get("Accounts", [])[0].get("DatabasePrivileges", [])
        database_privileges = [
            {
                "database_name": privilege.get("DBName"),
                "account_privilege": privilege.get("AccountPrivilege"),
            }
            for privilege in database_privileges
        ]
        return database_privileges, True

    def create_account_and_grant_privilege(
        self,
        cluster_id: str,
        account_name: str,
        account_password: str,
        database_name: str,
        account_privilege: str = "ReadWrite",
    ) -> bool:
        """
        description:
            创建PolarDB账号并授予权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            account_password(str): 账号密码
            database_name(str): 数据库名称
            account_privilege(str): 账号权限
        return:
            bool: 创建结果
        """
        resp, success = self.create_account(cluster_id, account_name, account_password)
        if not success:
            return False
        success = self.grant_account_privilege(
            cluster_id, account_name, database_name, account_privilege
        )
        return success

    async def create_account_and_grant_privilege_async(
        self,
        cluster_id: str,
        account_name: str,
        account_password: str,
        database_name: str,
        account_privilege: str = "ReadWrite",
    ) -> bool:
        """
        description:
            异步创建PolarDB账号并授予权限
        parameters:
            cluster_id(str): 集群ID
            account_name(str): 账号名称
            account_password(str): 账号密码
            database_name(str): 数据库名称
            account_privilege(str): 账号权限
        return:
            bool: 创建结果
        """
        success = await self.create_account_async(
            cluster_id, account_name, account_password
        )
        if not success:
            return False
        success = await self.grant_account_privilege_async(
            cluster_id, account_name, database_name, account_privilege
        )
        return success
