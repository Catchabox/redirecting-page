import subprocess
import fileinput
import os
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command):
    """执行 shell 命令并提供反馈"""
    logging.info(f"正在执行: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        logging.error(f"错误: 执行命令失败: {command}\n错误信息: {stderr.decode()}")
    else:
        logging.info(f"成功: {stdout.decode()}")
    return process.returncode, stdout.decode(), stderr.decode()

def is_installed(package):
    """检查软件包是否已安装"""
    logging.info(f"检查 {package} 是否已安装...")
    result = subprocess.run(f"dpkg -l | grep -w {package}", shell=True, stdout=subprocess.PIPE)
    return result.returncode == 0

def install_others():
    """安装 sudo、lsof 和 lsb-release"""
    # 安装 sudo
    if not is_installed("sudo"):
        logging.info("sudo 未安装，正在安装...")
        run_command("apt install -y sudo")
    else:
        logging.info("sudo 已安装，跳过安装步骤。")

    # 安装 lsof
    if not is_installed("lsof"):
        logging.info("lsof 未安装，正在安装...")
        run_command("apt install -y lsof")
    else:
        logging.info("lsof 已安装，跳过安装步骤。")

    # 安装 lsb-release
    if not is_installed("lsb-release"):
        logging.info("lsb-release 未安装，正在安装...")
        run_command("apt install -y lsb-release")
    else:
        logging.info("lsb-release 已安装，跳过安装步骤。")

    # 安装 curl
    if not is_installed("curl"):
        logging.info("curl 未安装，正在安装...")
        run_command("apt install -y curl")
    else:
        logging.info("curl 已安装，跳过安装步骤。")

def install_certbot():
    """
    安装 certbot 和 python3-certbot-nginx
    """
    # 安装 certbot
    if not is_installed("certbot"):
        logging.info("certbot 未安装，正在安装...")
        run_command("apt install -y certbot")
    else:
        logging.info("certbot 已安装，跳过安装步骤。")

    # 安装 python3-certbot-nginx
    if not is_installed("python3-certbot-nginx"):
        logging.info("python3-certbot-nginx 未安装，正在安装...")
        run_command("apt install -y python3-certbot-nginx")
    else:
        logging.info("python3-certbot-nginx 已安装，跳过安装步骤。")

def get_nginx_user():
    """获取 Nginx 配置文件中的用户设置"""
    try:
        result = subprocess.run("grep -E '^user ' /etc/nginx/nginx.conf", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            user_line = result.stdout.strip()
            user = user_line.split()[1].rstrip(';')
            return user
        else:
            logging.error("无法获取 Nginx 用户设置。")
            return None
    except Exception as e:
        logging.error(f"错误: {e}")
        return None

def modify_www_conf(file_path):
    """修改 www.conf 文件"""
    nginx_user = get_nginx_user()
    if nginx_user is None:
        return

    logging.info(f"正在修改 {file_path} 文件... 使用的 Nginx 用户是: {nginx_user}")
    if not os.path.exists(file_path):
        logging.error(f"错误: 文件 {file_path} 不存在。")
        return

    modified = False
    changes = []
    printed_lines = set()  # 初始化 printed_lines 集合

    for line in fileinput.input(file_path, inplace=True):
        line = line.strip()

        # 默认打印当前行
        if line.startswith("listen.owner ="):
            new_line = f"listen.owner = {nginx_user}"
            if new_line not in printed_lines:  # 检查是否已打印
                print(new_line)  # 打印新的行
                printed_lines.add(new_line)  # 添加到已打印集合
                changes.append(new_line)
                modified = True
        elif line.startswith("listen.group ="):
            new_line = f"listen.group = {nginx_user}"
            if new_line not in printed_lines:  # 检查是否已打印
                print(new_line)  # 打印新的行
                printed_lines.add(new_line)  # 添加到已打印集合
                changes.append(new_line)
                modified = True
        elif line.startswith("listen.mode ="):
            new_line = "listen.mode = 0660"
            if new_line not in printed_lines:  # 检查是否已打印
                print(new_line)  # 打印新的行
                printed_lines.add(new_line)  # 添加到已打印集合
                changes.append(new_line)
                modified = True
        else:
            if line not in printed_lines:  # 打印未修改的行
                print(line)  # 打印未修改的行
                printed_lines.add(line)  # 添加到已打印集合

    if modified:
        logging.info("成功: www.conf 文件已更新，修改内容如下：")
        for change in changes:
            logging.info(f"  - {change}")
    else:
        logging.warning("警告: www.conf 文件中找不到需要修改的行。")

def restart_services():
    """重启 Nginx 和 PHP-FPM 服务"""
    try:
        subprocess.run(["sudo", "systemctl", "restart", "nginx"], check=True)
        subprocess.run(["sudo", "systemctl", "restart", "php8.2-fpm"], check=True)
        logging.info("成功: Nginx 和 PHP-FPM 已重启。")
    except subprocess.CalledProcessError as e:
        logging.error(f"错误: 重启服务时发生问题: {e}")

def get_debian_version():
    """获取当前 Debian 版本"""
    result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
    return result.stdout.strip()

def test_repository_url(url):
    """测试仓库地址是否可以访问"""
    return_code, stdout, stderr = run_command(f"curl -Is {url} | head -n 1")
    if "200 OK" in stdout:
        return True
    logging.error(f"仓库地址无效: {url}")
    return False

def install_nginx(debian_version):
    """安装 Nginx"""
    nginx_repo_url = f"http://nginx.org/packages/debian/ {debian_version} nginx"
    if not test_repository_url(nginx_repo_url):
        logging.error("Nginx 仓库地址无效，无法继续安装。")
        return False

    commands = [
        "sudo apt update || true",
        "sudo apt install -y curl gnupg2",
        "curl -fsSL https://nginx.org/keys/nginx_signing.key | sudo gpg --dearmor -o /usr/share/keyrings/nginx-archive-keyring.gpg",
        "sudo rm -f /etc/apt/sources.list.d/nginx.list",  # 删除原有的 Nginx 源配置
        f"echo 'deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] {nginx_repo_url}' | sudo tee /etc/apt/sources.list.d/nginx.list",
        f"echo 'deb-src [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] {nginx_repo_url}' | sudo tee -a /etc/apt/sources.list.d/nginx.list",
        "sudo apt update || true",
        "sudo apt install -y nginx",
        "sudo systemctl start nginx",
        "sudo systemctl enable nginx"
    ]

    for command in commands:
        logging.info(f"执行命令: {command}")
        return_code, stdout, stderr = run_command(command)
        if return_code != 0:
            logging.error(f"安装 Nginx 时发生错误: {stderr}")
            return False  # 安装失败

    # 获取 Nginx 安装的版本
    return_code, nginx_version, stderr = run_command("nginx -v")
    if return_code == 0:
        logging.info(f"Nginx 安装成功，版本: {nginx_version.strip()}")
    else:
        logging.error(f"获取 Nginx 版本时发生错误: {stderr}")

    return True  # 安装成功

def install_php_fpm():
    """安装 PHP 8.2-FPM"""
    run_command("sudo apt install -y php8.2-fpm")

def main():
    # 安装 sudo、lsof 和 lsb-release
    install_others()

    # 首先更新软件包列表
    run_command("sudo apt update || true")
    logging.basicConfig(level=logging.INFO)  # 设置日志级别
    # 检查并安装 Nginx

    debian_version = get_debian_version()
    if install_nginx(debian_version):
        logging.info(f"当前系统版本: {debian_version}")
        # 安装 certbot 和 python3-certbot-nginx
        install_certbot()
    else:
        logging.error("Nginx 安装失败。")

    # 检查并安装 PHP 8.2-FPM
    if not is_installed("php8.2-fpm"):
        install_php_fpm()
    else:
        logging.info("PHP 8.2-FPM 已安装，跳过安装步骤。")

    # 修改 www.conf 文件
    www_conf_path = "/etc/php/8.2/fpm/pool.d/www.conf"
    modify_www_conf(www_conf_path)

    # 脚本结束时重启服务
    restart_services()

    logging.info("所有操作完成！请检查 Nginx 和 PHP 8.2-FPM 的状态。")

if __name__ == "__main__":
    main()
