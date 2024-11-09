import os
import shutil
import subprocess

def delete_certificate(domain):
    """删除 Let's Encrypt 的证书"""
    try:
        # 使用 certbot 删除证书
        subprocess.run(['certbot', 'delete', '--cert-name', domain], check=True)
        print(f"已删除 {domain} 的证书。")
    except subprocess.CalledProcessError as e:
        print(f"删除证书失败: {e}")

def delete_nginx_config(domain):
    """删除 Nginx 配置文件"""
    config_path = f"/etc/nginx/conf.d/{domain}.conf"
    if os.path.exists(config_path):
        os.remove(config_path)
        print(f"已删除 Nginx 配置文件: {config_path}")
    else:
        print(f"Nginx 配置文件 {config_path} 不存在，跳过删除。")

def delete_domain_directory(domain_with_suffix):
    """删除域名目录下的文件"""
    target_directory = f"/var/www/{domain_with_suffix}"
    if os.path.exists(target_directory):
        shutil.rmtree(target_directory)
        print(f"已删除域名目录及其内容: {target_directory}")
    else:
        print(f"域名目录 {target_directory} 不存在，跳过删除。")

def main():
    # 获取域名信息
    domain = input("请输入要删除的域名: ").strip()
    domain_with_suffix = f"{domain}_file"

    # 删除 Let's Encrypt 证书
    delete_certificate(domain)

    # 删除 Nginx 配置文件
    delete_nginx_config(domain)

    # 删除域名目录
    delete_domain_directory(domain_with_suffix)

    # 重启 Nginx 服务以应用更改
    try:
        subprocess.run(["systemctl", "restart", "nginx"], check=True)
        print("Nginx 已成功重启。")
    except subprocess.CalledProcessError as e:
        print(f"重启 Nginx 失败: {e}")

    print("所有删除操作已完成！")

if __name__ == "__main__":
    main()
