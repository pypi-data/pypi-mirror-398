import questionary
from fabric import Connection, task
from invoke import Config
from .._utils.setup_apt_sources import setup_apt_sources
from .._utils.cleanup_network_config import cleanup_network_config  

# 设置远程命令环境变量，使用英文输出避免中文乱码
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}


# region Debian 初始化任务



@task
def apt_update_and_install_base_package(conn: Connection) -> None:
    """apt update 和 安装依赖包 """
    conn.sudo("apt-get update -y", env=ENV_LANG_C)
    # conn.sudo("apt-get upgrade -y", env=ENV_LANG_C)
    conn.sudo("apt-get install -y vim sudo curl wget sshpass", env=ENV_LANG_C)


@task
def setup_vagrant_user(conn: Connection) -> None:
    """确保 vagrant 用户存在并配置SSH"""

    # 创建用户
    conn.sudo("id vagrant || useradd -m -s /bin/bash vagrant", warn=True, env=ENV_LANG_C)

    # 设置密码
    conn.sudo("bash -c \"echo 'vagrant:vagrant' | chpasswd\"")

    # 无密码 sudo (使用 tee 解决重定向权限问题)
    conn.sudo(
        "bash -c \"echo 'vagrant ALL=(ALL) NOPASSWD:ALL' | tee /etc/sudoers.d/no-password-sudo > /dev/null\""
    )

    # 配置 .ssh 目录
    conn.sudo("mkdir -p /home/vagrant/.ssh")
    conn.sudo("chmod 700 /home/vagrant/.ssh")
    conn.sudo("chown vagrant:vagrant /home/vagrant/.ssh")

    # 添加 vagrant insecure key (使用 tee 解决重定向权限问题)
    insecure_keys = """ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN1YdxBpNlzxDqfJyw/QKow1F+wvG9hXGoqiysfJOn5Y vagrant insecure public key"""
    conn.sudo(f"bash -c \"echo '{insecure_keys}' | tee /home/vagrant/.ssh/authorized_keys > /dev/null\"")
    conn.sudo("chmod 600 /home/vagrant/.ssh/authorized_keys")
    conn.sudo("chown vagrant:vagrant /home/vagrant/.ssh/authorized_keys")


@task
def install_kernel_dev_packages(conn: Connection) -> None:
    """安装内核开发相关包 (用于 VirtualBox Guest Additions)"""
    # 获取当前内核版本
    result = conn.run("uname -r", hide=True)
    kernel_version = result.stdout.strip()

    conn.sudo("apt-get install -y build-essential dkms", env=ENV_LANG_C)
    conn.sudo(f"apt-get install -y linux-headers-{kernel_version}", warn=True, env=ENV_LANG_C)


def download_vbox_guest_additions(version: str, dest_dir: str = ".") -> str:
    """下载 VirtualBox Guest Additions ISO 到本地主机
    
    Args:
        version: VirtualBox 版本号 (如 "7.0.14")
        dest_dir: 下载目标目录，默认为当前目录
        
    Returns:
        下载后的 ISO 文件路径
    """
    import urllib.request
    import os
    
    print(f"\n[任务] 下载 VirtualBox Guest Additions {version}")
    
    iso_filename = f"VBoxGuestAdditions_{version}.iso"
    iso_path = os.path.join(dest_dir, iso_filename)
    download_url = f"https://download.virtualbox.org/virtualbox/{version}/{iso_filename}"
    
    # 检查文件是否已存在
    if os.path.exists(iso_path):
        print(f"  ISO 文件已存在: {iso_path}")
        return iso_path
    
    # 下载 ISO 并显示进度
    print(f"  正在下载: {download_url}")
    
    def progress_hook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            print(f"\r  下载进度: {percent}%", end="", flush=True)
    
    urllib.request.urlretrieve(download_url, iso_path, progress_hook)
    print(f"\n  下载完成: {iso_path}")
    
    return iso_path


@task
def install_vbox_guest_additions(conn: Connection) -> None:
    """下载 上传 挂载并安装 VirtualBox Guest Additions"""
    iso_path=download_vbox_guest_additions(version="7.2.4")
    # 上传 ISO
    conn.put(iso_path, "/tmp/VBoxGuestAdditions.iso")

    # 挂载
    conn.sudo("mkdir -p /media/VBoxGuestAdditions")
    conn.sudo("mount -o loop,ro /tmp/VBoxGuestAdditions.iso /media/VBoxGuestAdditions", warn=True)

    # 执行安装
    try:
        conn.sudo("sh /media/VBoxGuestAdditions/VBoxLinuxAdditions.run --nox11", warn=True)
    finally:
        # 卸载
        conn.sudo("umount /media/VBoxGuestAdditions", warn=True)

    # 验证安装
    result = conn.sudo("/sbin/rcvboxadd status", warn=True)
    print(f"  Guest Additions 状态: {result.stdout.strip()}")

@task
def testssh(conn: Connection):
    """SSH 连通测试"""
    result = conn.run("echo 'SSH connection OK'", hide=True)
    print(f"✓ {result.stdout.strip()}")


# endregion



 