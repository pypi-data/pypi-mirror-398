import argparse
import base64
from pixelarraylib.system.common import execute_command_through_ssh, execute_command
from pixelarraylib.aliyun.domain import DomainUtils


def nginx_proxy_file_template(
    domain_name: str, port_of_service: str, ssl_cert_path: str, ssl_key_path: str
) -> str:
    """
    description:
        生成Nginx反向代理配置文件模板
    parameters:
        domain_name(str): 域名
        port_of_service(str): 服务端口
        ssl_cert_path(str): SSL证书路径
        ssl_key_path(str): SSL密钥路径
    return:
        nginx_config(str): Nginx配置文件内容
    """
    return f"""
server {{
    listen 80;
    server_name {domain_name}.pixelarrayai.com;

    # 将所有HTTP请求重定向到HTTPS
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    server_name {domain_name}.pixelarrayai.com;

    ssl_certificate {ssl_cert_path};
    ssl_certificate_key {ssl_key_path};

    location / {{
        proxy_pass http://localhost:{port_of_service};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
    """


def add_a_record_to_dns(
    domain_name: str, ecs_ip: str, access_key_id: str, access_key_secret: str
) -> None:
    """
    description:
        添加DNS A记录
    parameters:
        domain_name(str): 域名
        ecs_ip(str): ECS IP地址
        access_key_id(str): 阿里云访问密钥ID
        access_key_secret(str): 阿里云访问密钥Secret
    """
    domain_utils = DomainUtils(
        access_key_id, access_key_secret, domain_name="pixelarrayai.com"
    )
    
    # 先检查是否存在相同的主机记录
    existing_record = domain_utils.find_record_by_rr_and_type(rr=domain_name, type="A")
    if existing_record:
        print(f"发现已存在的主机记录 {domain_name}，正在删除...")
        success = domain_utils.delete_record_by_rr_and_type(rr=domain_name, type="A")
        if success:
            print(f"已删除旧的主机记录 {domain_name}")
        else:
            print(f"删除旧记录失败，但继续添加新记录")
    
    # 添加新的解析记录
    success, record_id = domain_utils.add_domain_record(
        rr=domain_name,
        type="A",
        value=ecs_ip,
    )
    
    if success:
        print(f"域名解析记录添加成功，记录ID: {record_id}")
    else:
        print("域名解析记录添加失败")


def deploy(
    domain_name: str,
    port_of_service: str,
    ssl_cert_path: str,
    ssl_key_path: str,
    access_key_id: str,
    access_key_secret: str,
    mode: str,
    ecs_ip: str,
) -> None:
    """
    description:
        部署Nginx反向代理配置到ECS
    parameters:
        domain_name(str): 域名
        port_of_service(str): 服务端口
        ssl_cert_path(str): SSL证书路径
        ssl_key_path(str): SSL密钥路径
        access_key_id(str): 阿里云访问密钥ID
        access_key_secret(str): 阿里云访问密钥Secret
        mode(str): 部署模式（remote或local）
        ecs_ip(str): ECS IP地址
    """
    if mode == "remote":
        execute_command_through_ssh(
            ecs_ip,
            f"sudo rm -f /etc/nginx/sites-available/{domain_name} && sudo rm -f /etc/nginx/sites-enabled/{domain_name}",
        )
        print("删除原有配置成功")
        execute_command_through_ssh(
            ecs_ip,
            f"sudo touch /etc/nginx/sites-available/{domain_name}",
        )
        print("文件创建成功")
        nginx_proxy_file_content = nginx_proxy_file_template(
            domain_name, port_of_service, ssl_cert_path, ssl_key_path
        )
        # 使用 base64 编码来避免特殊字符问题
        encoded_content = base64.b64encode(nginx_proxy_file_content.encode('utf-8')).decode('utf-8')
        execute_command_through_ssh(
            ecs_ip,
            f"echo '{encoded_content}' | base64 -d | sudo tee /etc/nginx/sites-available/{domain_name} > /dev/null",
        )
        print("内容写入成功")
        execute_command_through_ssh(
            ecs_ip,
            f"sudo ln -s /etc/nginx/sites-available/{domain_name} /etc/nginx/sites-enabled/{domain_name}",
        )
        print("nginx配置添加成功，准备重启")
        execute_command_through_ssh(
            ecs_ip, f"sudo nginx -t && sudo systemctl restart nginx"
        )
        print("重启成功，请检查配置是否生效")
    else:
        execute_command(
            f"sudo rm -f /etc/nginx/sites-available/{domain_name} && sudo rm -f /etc/nginx/sites-enabled/{domain_name}"
        )
        print("删除原有配置成功")
        execute_command(
            f"sudo touch /etc/nginx/sites-available/{domain_name}"
        )
        print("文件创建成功")
        nginx_proxy_file_content = nginx_proxy_file_template(
            domain_name, port_of_service, ssl_cert_path, ssl_key_path
        )
        execute_command(
            f"sudo echo {nginx_proxy_file_content} | base64 -d | sudo tee /etc/nginx/sites-available/{domain_name} > /dev/null"
        )
        print("内容写入成功")
        execute_command(
            f"sudo ln -s /etc/nginx/sites-available/{domain_name} /etc/nginx/sites-enabled/{domain_name}"
        )
        print("nginx配置添加成功，准备重启")
        execute_command(
            "sudo nginx -t && sudo systemctl restart nginx"
        )
        print("重启成功，请检查配置是否生效")
    add_a_record_to_dns(domain_name, ecs_ip, access_key_id, access_key_secret)


def main():
    parser = argparse.ArgumentParser(
        description="Nginx反向代理配置到ECS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--domain_name", "-d", help="需要代理的域名")
    parser.add_argument("--port_of_service", "-p", help="端口或服务")
    parser.add_argument("--access_key_id", "-a", help="阿里云AccessKeyID")
    parser.add_argument("--access_key_secret", "-s", help="阿里云AccessKeySecret")
    parser.add_argument("--mode", "-m", help="本地执行还是远程执行，local或remote，默认是remote")
    parser.add_argument("--ecs_ip", "-e", help="服务器的IP地址")

    args = parser.parse_args()

    deploy(
        args.domain_name,
        args.port_of_service,
        "/var/pixelarray/ssl_auth/pixelarrayai.com.pem",
        "/var/pixelarray/ssl_auth/pixelarrayai.com.key",
        args.access_key_id,
        args.access_key_secret,
        args.mode,
        args.ecs_ip,
    )


if __name__ == "__main__":
    main()
