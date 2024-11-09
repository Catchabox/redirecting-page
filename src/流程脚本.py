import os
import subprocess
import shutil
import time
from tqdm import tqdm
import socket
import signal
import sys

def clear_certbot_cache():
    # 定义 Certbot 缓存目录
    cache_dirs = [
        '/var/lib/letsencrypt/',
        '/var/log/letsencrypt/'
    ]
    
    try:
        # 清空缓存目录
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)  # 递归删除缓存目录
                os.makedirs(cache_dir, exist_ok=True)  # 重新创建空目录
                print(f"已清除 Certbot 缓存目录: {cache_dir}")
        return True  # 清理成功，返回 True
    except Exception as e:
        print(f"清理缓存失败: {e}")
        return False  # 清理失败，返回 False

def get_domain():
    domain = input("请输入域名: ")
    domain_with_suffix = f"{domain}_file"  # 拼接后缀
    return domain, domain_with_suffix  # 返回域名和带后缀的字符串

def check_dns(domain):
    """检查域名的DNS解析是否成功"""
    try:
        socket.gethostbyname(domain)
        print(f"DNS解析成功: {domain}")
        return True
    except socket.gaierror:
        print(f"DNS解析失败: {domain}")
        return False

def certificate_exists(domain):
    """检查本地是否已有该域名的证书"""
    cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
    return os.path.isfile(cert_path)

def stop_port_80_process():
    """查找并终止占用端口 80 的所有进程"""
    try:
        result = subprocess.run(
            ["lsof", "-i", ":80", "-t"],
            check=True,
            stdout=subprocess.PIPE,
            text=True
        )
        pids = result.stdout.strip().splitlines()
        
        if pids:
            print(f"发现使用端口 80 的进程 PID: {', '.join(pids)}，正在终止...")
            terminated_pids = []
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    terminated_pids.append(pid)
                except ProcessLookupError:
                    print(f"进程 {pid} 未找到，可能已经终止")
                except Exception as e:
                    print(f"终止进程 {pid} 时发生错误: {e}")
            print(f"成功终止以下进程: {', '.join(terminated_pids)}")
            return terminated_pids  # 返回被终止的进程 ID 列表
        else:
            print("端口 80 没有被占用")
            return []  # 返回空列表
    except subprocess.CalledProcessError:
        print("无法获取占用端口 80 的进程信息")
        return []


def restart_web_server():
    print("正在重新启动 Web 服务器...")
    subprocess.run(["sudo", "systemctl", "start", "nginx"], check=True)
    print("Web 服务器已成功重启")


def request_certificate(domain, email):
    total_steps = 5  # 总共5个步骤，进度条更新到 100%

    with tqdm(total=100, desc=f"申请证书: {domain}", unit='%', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        # Step 1: 检查 DNS
        if not check_dns(domain):
            print(f"域名 {domain} 的 DNS 解析失败，无法继续申请证书。")
            return False
        pbar.update(100 / total_steps)  # DNS 检查完成，更新进度条

        # Step 2: 检查本地是否已有证书
        if certificate_exists(domain):
            print(f"本地已有 {domain} 的证书，跳过申请。")
            return True
        pbar.update(100 / total_steps)  # 本地证书检查完成，更新进度条

        # Step 3: 停止占用端口 80 的进程
        stopped_pid = stop_port_80_process()
        pbar.update(100 / total_steps)  # 停止进程完成，更新进度条

        try:
            # Step 4: 执行 Certbot 命令申请证书
            certbot_cmd = [
                "certbot", "certonly", "--standalone", "--non-interactive",
                "--agree-tos", "--email", email, "-d", domain
            ]
            print("执行 Certbot 命令:", certbot_cmd)

            result = subprocess.run(certbot_cmd,
                                    check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    timeout=300)  # 设置超时时间为5分钟
            print(f"成功申请证书: {domain}")
            print(f"输出信息: {result.stdout}")  # 输出标准输出
            pbar.update(100 / total_steps)  # 证书申请成功，更新进度条

        except subprocess.TimeoutExpired:
            print(f"申请证书超时: {domain}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"申请证书失败: {e}")
            print(f"错误代码: {e.returncode}")
            print(f"错误信息: {e.stderr}")
            return False
        finally:
            # Step 5: 如果之前有进程占用端口 80，则重新启动 Web 服务器
            if stopped_pid:
                restart_web_server()
            pbar.update(100 / total_steps)  # 重启 Web 服务器完成，更新进度条

    return True

def copy_and_replace_files(domain, domain_with_suffix):
    config_file = f"{domain}.conf"
    source_path = os.path.join(os.getcwd(), "domain_name.conf")
    target_path = f"/etc/nginx/conf.d/{domain}.conf"

    try:
        # 检查并删除目标文件（如果存在）
        if os.path.exists(target_path):
            os.remove(target_path)
            print(f"删除已存在的文件: {target_path}")

        # 复制文件
        shutil.copy(source_path, target_path)
        print(f"复制文件到: {target_path}")

        # 替换文件内容
        with open(target_path, 'r') as file:
            file_contents = file.read()

        # 替换域名
        updated_contents_domain = file_contents.replace('domain_name', f'{domain}')

        with open(target_path, 'w') as file:
            file.write(updated_contents_domain)
        print(f"已将 {target_path} 中的域名替换为: {domain}")

        # 替换 /var/www/ 名称
        updated_contents_webpage = updated_contents_domain.replace('welcome', f'{domain_with_suffix}')

        with open(target_path, 'w') as file:
            file.write(updated_contents_webpage)
        print(f"已将 {target_path} 中的目录替换为: {domain_with_suffix}")
    except Exception as e:
        print(f"复制和替换文件失败: {e}")
        return False  # 返回失败状态
    return True  # 返回成功状态



def copy_files_to_domain_directory(domain_with_suffix):
    # 目标目录
    target_directory = f"/var/www/{domain_with_suffix}"

    # 创建目标目录（如果不存在）
    os.makedirs(target_directory, exist_ok=True)

    # 要复制的文件列表
    files_to_copy = ['edit.html', 'index.html', 'update.php']

    for file_name in files_to_copy:
        target_file = os.path.join(target_directory, file_name)
        
        # 如果文件已存在，删除旧文件
        if os.path.isfile(target_file):
            os.remove(target_file)
            print(f"删除已存在的文件: {target_file}")

        # 复制文件到目标目录
        if os.path.isfile(file_name):
            shutil.copy(file_name, target_directory)
            print(f"已复制 {file_name} 到 {target_directory}")
        else:
            print(f"文件 {file_name} 不存在，无法复制。")
            return False  # 返回失败状态
    return True  # 返回成功状态

# 获取nginx用户
def get_nginx_user():
    try:
        # 执行命令并获取结果
        result = subprocess.run(
            ["grep", "user", "/etc/nginx/nginx.conf"],
            capture_output=True,
            text=True,
            check=True
        )
        # 提取用户信息
        user_line = result.stdout.strip()
        # 解析用户，假设格式为 "user nginx;"
        user = user_line.split()[1].strip(';')  # 去掉分号
        return user
    except subprocess.CalledProcessError:
        print("无法获取nginx用户")
        return None

def change_permissions_and_ownership():
    # 获取nginx用户
    nginx_user = get_nginx_user()
    if nginx_user is None:
        print("无法获取nginx用户，无法更改权限和所有权")
        return False

    # 打印将要执行的命令
    print(f"将要更改所有权为: {nginx_user}:{nginx_user}")

    chown_command = ["chown", "-R", f"{nginx_user}:{nginx_user}", "/var/www/"]
    chmod_command = ["chmod", "-R", "777", "/var/www/"]

    try:
        # 执行 chown 命令
        subprocess.run(chown_command, check=True)
        print(f"成功更改文件所有权为 {nginx_user}:{nginx_user}")

        # 执行 chmod 命令
        subprocess.run(chmod_command, check=True)
        print("成功更改权限为 777")
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False  # 返回失败状态
    return True  # 返回成功状态

def restart_nginx():
    # 要执行的命令
    command = ["systemctl", "restart", "nginx"]

    try:
        # 执行命令
        subprocess.run(command, check=True)
        print("Nginx 已成功重启。")
    except subprocess.CalledProcessError as e:
        print(f"重启 Nginx 失败: {e}")
        return False  # 返回失败状态
    return True  # 返回成功状态


def replace_url_in_file(domain_with_suffix):
    file_path = f"/var/www/{domain_with_suffix}/index.html"
    
    new_url = input("请输入跳转的URI:")

    try:
        # 读取文件内容
        with open(file_path, 'r') as file:
            file_contents = file.read()
        
        # 替换 URL
        updated_contents = file_contents.replace("https://tesla.com", new_url)
        
        # 写回文件
        with open(file_path, 'w') as file:
            file.write(updated_contents)
        
        print(f"已将 {file_path} 中的 URL 替换为:{new_url}")
    except FileNotFoundError:
        print(f"文件 {file_path} 不存在，无法进行替换。")
    except Exception as e:
        print(f"替换文件内容失败: {e}")


def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # 切换到脚本所在目录
    os.chdir(script_dir)

    print("当前目录已切换到脚本所在目录:", os.getcwd())
    while True:
        domain, domain_with_suffix = get_domain()
        email = input("请输入您的电子邮箱地址: ").strip()

        # 清理缓存
        if not clear_certbot_cache():
            print("清理CERT缓存失败，程序中止。")
            break

        # 申请证书
        if not request_certificate(domain, email):
            print("证书申请失败，程序中止。")
            break

        # 复制并替换配置文件
        if not copy_and_replace_files(domain, domain_with_suffix):
            print("配置文件复制和替换失败，程序中止。")
            break

        # 复制文件到域名目录
        if not copy_files_to_domain_directory(domain_with_suffix):
            print("文件复制到域名目录失败，程序中止。")
            break

        # 更改权限和所有权
        if not change_permissions_and_ownership():
            print("更改权限和所有权失败，程序中止。")
            break

        # 重启 Nginx
        if not restart_nginx():
            print("重启 Nginx 失败，程序中止。")
            break

        # 替换 URL
        replace_url_in_file(domain_with_suffix)
        print("所有步骤成功完成！")

        # 询问用户是否继续
        continue_choice = input("是否继续执行？(y/n): ").strip().lower()
        if continue_choice != 'y':
            print("程序结束。")
            break

if __name__ == "__main__":
    main()
