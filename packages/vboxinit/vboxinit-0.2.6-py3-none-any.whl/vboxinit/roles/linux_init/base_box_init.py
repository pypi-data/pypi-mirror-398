import questionary
from fabric import Connection, task
from invoke import Config 

# 设置远程命令环境变量，使用英文输出避免中文乱码
ENV_LANG_C = {"LANG": "C", "LC_ALL": "C"}


# region Debian 初始化任务
@task
def setup_apt_sources(conn: Connection, source_list: str) -> None:
    """更换软件源"""
    print("\n[任务] 更换软件源")
    # 对 source_list 中的单引号进行转义处理
    # 将 ' 替换为 '\'' (先结束当前单引号，插入转义的单引号，再开启新单引号)
    # 这是 shell 中在单引号字符串内嵌入单引号的标准技巧
    # 例如: "it's" -> "it'\''s" 在 shell 中会被解析为 it's
    escaped = source_list.replace("'", "'\\''")
    # 使用 tee 解决 sudo 重定向权限问题
    conn.sudo(f"bash -c \"echo '{escaped}' | tee /etc/apt/sources.list > /dev/null\"", hide=True)


@task
def apt_update_upgrade(conn: Connection) -> None:
    """apt update 和 apt upgrade"""
    print("\n[任务] apt update & upgrade")
    conn.sudo("apt-get update -y", env=ENV_LANG_C)
    # conn.sudo("apt-get upgrade -y", env=ENV_LANG_C)


@task
def install_base_packages(conn: Connection) -> None:
    """安装必要的依赖"""
    print("\n[任务] 安装基础依赖软件包")
    conn.sudo("apt-get install -y vim sudo curl wget sshpass", env=ENV_LANG_C)


@task
def setup_vagrant_user(conn: Connection) -> None:
    """确保 vagrant 用户存在并配置"""
    print("\n[任务] 配置 vagrant 用户")

    # 创建用户
    conn.sudo("id vagrant || useradd -m -s /bin/bash vagrant", hide=True, warn=True)

    # 设置密码
    conn.sudo("bash -c \"echo 'vagrant:vagrant' | chpasswd\"", hide=True)

    # 无密码 sudo (使用 tee 解决重定向权限问题)
    conn.sudo(
        "bash -c \"echo 'vagrant ALL=(ALL) NOPASSWD:ALL' | tee /etc/sudoers.d/no-password-sudo > /dev/null\"",
        hide=True
    )

    # 配置 .ssh 目录
    conn.sudo("mkdir -p /home/vagrant/.ssh", hide=True)
    conn.sudo("chmod 700 /home/vagrant/.ssh", hide=True)
    conn.sudo("chown vagrant:vagrant /home/vagrant/.ssh", hide=True)

    # 添加 vagrant insecure key (使用 tee 解决重定向权限问题)
    insecure_keys = """ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN1YdxBpNlzxDqfJyw/QKow1F+wvG9hXGoqiysfJOn5Y vagrant insecure public key"""
    conn.sudo(f"bash -c \"echo '{insecure_keys}' | tee /home/vagrant/.ssh/authorized_keys > /dev/null\"", hide=True)
    conn.sudo("chmod 600 /home/vagrant/.ssh/authorized_keys", hide=True)
    conn.sudo("chown vagrant:vagrant /home/vagrant/.ssh/authorized_keys", hide=True)


@task
def install_kernel_dev_packages(conn: Connection) -> None:
    """安装内核开发相关包 (用于 VirtualBox Guest Additions)"""
    print("\n[任务] 安装内核开发包")
    # 获取当前内核版本
    result = conn.run("uname -r", hide=True)
    kernel_version = result.stdout.strip()

    conn.sudo("apt-get install -y build-essential dkms", env=ENV_LANG_C)
    conn.sudo(f"apt-get install -y linux-headers-{kernel_version}", warn=True, env=ENV_LANG_C)


@task
def install_vbox_guest_additions(conn: Connection, iso_path: str) -> None:
    """挂载并安装 VirtualBox Guest Additions"""
    print("\n[任务] 安装 VirtualBox Guest Additions")

    # 上传 ISO
    conn.put(iso_path, "/tmp/VBoxGuestAdditions.iso")

    # 挂载
    conn.sudo("mkdir -p /media/VBoxGuestAdditions", hide=True)
    conn.sudo("mount -o loop,ro /tmp/VBoxGuestAdditions.iso /media/VBoxGuestAdditions", warn=True)

    # 执行安装
    try:
        conn.sudo("sh /media/VBoxGuestAdditions/VBoxLinuxAdditions.run --nox11", warn=True)
    finally:
        # 卸载
        conn.sudo("umount /media/VBoxGuestAdditions", warn=True)

    # 验证安装
    result = conn.sudo("/sbin/rcvboxadd status", hide=True, warn=True)
    print(f"  Guest Additions 状态: {result.stdout.strip()}")


@task
def cleanup_debian_network_config(conn: Connection) -> None:
    """删除 Debian 系统的静态 IP 配置文件"""
    print("\n[任务] 清理网络配置")

    # 查找并删除网络配置文件
    result = conn.sudo("find /etc/network/interfaces.d/ -type f 2>/dev/null || true", hide=True)
    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    for f in files:
        conn.sudo(f"rm -f {f}", hide=True)
        print(f"  已删除: {f}")

    # 重启网络服务
    if files:
        conn.sudo("systemctl restart networking", warn=True)
# endregion



