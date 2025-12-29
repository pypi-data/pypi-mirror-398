"""
一键构建网站

使用方法:
1. 作为命令行工具：
   pixelarraylib build_website --

2. 作为Python模块：
   from pixelarraylib.scripts.build_website import build_website
   build_website()
"""

import argparse
from datetime import datetime
from pixelarraylib.aliyun.acr import ACRUtils
from pixelarraylib.aliyun.eci import ECIUtils
from pixelarraylib.system.common import execute_command


def get_acr_instance_id(
    acr_utils: ACRUtils,
):
    """
    description:
        获取ACR实例ID
    parameters:
        acr_utils(ACRUtils): ACR工具类实例
    return:
        instance_id(str): 实例ID
        success(bool): 是否成功
    """
    response, success = acr_utils.list_instances()
    if not success:
        return "", False
    return response["Instances"][0]["InstanceId"], True


def find_or_create_cloud_repo(
    access_key_id: str,
    access_key_secret: str,
    region_id: str,
    acr_namespace: str,
    acr_repository: str,
):
    """
    description:
        查找或创建云镜像仓库
    parameters:
        access_key_id(str): 阿里云访问密钥ID
        access_key_secret(str): 阿里云访问密钥Secret
        region_id(str): 区域ID
        acr_namespace(str): ACR命名空间
        acr_repository(str): ACR仓库名称
    return:
        success(bool): 是否成功
    """
    acr_utils = ACRUtils(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region_id,
    )
    acr_instance_id, success = get_acr_instance_id(acr_utils)
    if not success:
        print("获取阿里云镜像仓库实例ID失败")
        return False
    print("获取阿里云镜像仓库实例ID", acr_instance_id)
    flag, success = acr_utils.exists_namespace(
        instance_id=acr_instance_id, namespace_name=acr_namespace
    )
    print("判断阿里云镜像仓库命名空间是否存在")
    if not success:
        print("判断阿里云镜像仓库命名空间是否存在失败")
        return False
    if not flag:
        response, success = acr_utils.create_namespace(
            instance_id=acr_instance_id, namespace_name=acr_namespace
        )
        print("命名空间不存在，创建阿里云镜像仓库命名空间", response)
        if not success:
            print("创建阿里云镜像仓库命名空间失败")
            return False
    flag, success = acr_utils.exists_repository(
        instance_id=acr_instance_id,
        namespace_name=acr_namespace,
        repository_name=acr_repository,
    )
    print("判断阿里云镜像仓库仓库是否存在")
    if not success:
        print("判断阿里云镜像仓库仓库是否存在失败")
        return False
    if not flag:
        response, success = acr_utils.create_repository(
            instance_id=acr_instance_id,
            namespace_name=acr_namespace,
            repository_name=acr_repository,
            repository_type="PRIVATE",
            summary=acr_repository,
        )
        print("仓库不存在，创建阿里云镜像仓库仓库", response)
        if not success:
            print("创建阿里云镜像仓库仓库失败")
            return False
    return True


def push_local_image_to_cloud_repo(
    access_key_id: str,
    access_key_secret: str,
    region_id: str,
    acr_namespace: str,
    acr_repository: str,
    image_name: str,
):
    """
    description:
        推送本地镜像到云仓库
    parameters:
        access_key_id(str): 阿里云访问密钥ID
        access_key_secret(str): 阿里云访问密钥Secret
        region_id(str): 区域ID
        acr_namespace(str): ACR命名空间
        acr_repository(str): ACR仓库名称
        image_name(str): 镜像名称
    return:
        success(bool): 是否成功
    """
    acr_utils = ACRUtils(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region_id,
    )
    result, success = execute_command(
        [
            "docker",
            "tag",
            image_name,
            f"pixelarrayai-registry.{region_id}.cr.aliyuncs.com/{acr_namespace}/{acr_repository}",
        ]
    )
    if not success:
        print("推送本地镜像到云端仓库失败", result)
        return False
    print("开始推送本地镜像到云端仓库")
    result, success = execute_command(
        [
            "docker",
            "push",
            f"pixelarrayai-registry.{region_id}.cr.aliyuncs.com/{acr_namespace}/{acr_repository}",
        ]
    )
    if not success:
        print("推送本地镜像到云端仓库失败", result)
        return False
    print(result)
    print("推送本地镜像到云端仓库完成，检查是否推送成功")
    acr_instance_id, success = get_acr_instance_id(acr_utils)
    if not success:
        print("获取阿里云镜像仓库实例ID失败")
        return False
    response, success = acr_utils.get_repository(
        instance_id=acr_instance_id,
        namespace_name=acr_namespace,
        repository_name=acr_repository,
    )
    if not success:
        print("获取阿里云镜像仓库仓库详情失败")
        return False
    now = datetime.now().timestamp()
    if now - response["ModifiedTime"] > 5:
        print("阿里云镜像仓库仓库详情修改时间超过5秒，推送失败")
        return False
    print(response)
    print("推送成功")
    return True


def start_eci_instance_and_allocate_public_address(
    access_key_id: str,
    access_key_secret: str,
    region_id: str,
    acr_namespace: str,
    acr_repository: str,
    acr_username: str,
    acr_password: str,
    cpu: float,
    memory: float,
):
    eci_utils = ECIUtils(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region_id,
    )
    response, success = eci_utils.create_container_group(
        container_group_name=acr_repository,
        acr_credentials={
            "username": acr_username,
            "password": acr_password,
        },
        images=[
            {
                "namespace_name": acr_namespace,
                "repository_name": acr_repository,
            }
        ],
        cpu=cpu,
        memory=memory,
    )
    if not success:
        print("创建ECI实例失败", response)
        return False
    print("创建ECI实例成功", response)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="一键构建网站",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--access_key_id", "-a", help="阿里云AccessKeyID")
    parser.add_argument("--access_key_secret", "-s", help="阿里云AccessKeySecret")
    parser.add_argument("--image_name", "-i", help="本地镜像名称")
    parser.add_argument("--region_id", "-l", help="阿里云镜像仓库区域ID")
    parser.add_argument("--acr_namespace", "-n", help="阿里云镜像仓库命名空间")
    parser.add_argument("--acr_repository", "-r", help="阿里云镜像仓库名称")
    parser.add_argument("--acr_username", "-u", help="阿里云镜像仓库用户名")
    parser.add_argument("--acr_password", "-p", help="阿里云镜像仓库密码")
    parser.add_argument("--cpu", "-c", help="ECI实例CPU")
    parser.add_argument("--memory", "-m", help="ECI实例内存")
    args = parser.parse_args()

    print("一键构建网站，开始")
    print("第一步，查找或创建云端仓库")
    success = find_or_create_cloud_repo(
        access_key_id=args.access_key_id,
        access_key_secret=args.access_key_secret,
        region_id=args.region_id,
        acr_namespace=args.acr_namespace,
        acr_repository=args.acr_repository,
    )
    if not success:
        print("查找或创建云端仓库失败")
        return
    print("第二步，将本地代码推送到云端仓库")
    success = push_local_image_to_cloud_repo(
        access_key_id=args.access_key_id,
        access_key_secret=args.access_key_secret,
        region_id=args.region_id,
        acr_namespace=args.acr_namespace,
        acr_repository=args.acr_repository,
        image_name=args.image_name,
    )
    if not success:
        print("将本地代码推送到云端仓库失败")
        return
    print("第三步，启动ECI实例并分配公网地址")
    success = start_eci_instance_and_allocate_public_address(
        access_key_id=args.access_key_id,
        access_key_secret=args.access_key_secret,
        region_id=args.region_id,
        acr_namespace=args.acr_namespace,
        acr_repository=args.acr_repository,
        acr_username=args.acr_username,
        acr_password=args.acr_password,
        cpu=args.cpu,
        memory=args.memory,
    )
    if not success:
        print("启动ECI实例并分配公网地址失败")
        return
    print("第四步，配置Nginx反向代理")
    print("第五步，添加域名解析记录")
    print("一键构建网站，完成")


# python -m pixelarraylib.scripts.build_website
if __name__ == "__main__":
    main()
