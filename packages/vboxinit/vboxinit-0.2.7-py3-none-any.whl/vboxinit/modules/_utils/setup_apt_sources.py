import questionary
from fabric import Connection, task


# 可用镜像源
MIRRORS: dict[str, str] = {
    "cernet": "https://mirrors.cernet.edu.cn",
    "tuna": "https://mirrors.tuna.tsinghua.edu.cn",
    "aliyun": "https://mirrors.aliyun.com",
    "ustc": "https://mirrors.ustc.edu.cn",
}

# Ubuntu sources.list 模板
UBUNTU_SOURCES_TEMPLATE = """deb {mirror}/ubuntu/ {codename} main restricted universe multiverse
deb {mirror}/ubuntu/ {codename}-updates main restricted universe multiverse
deb {mirror}/ubuntu/ {codename}-backports main restricted universe multiverse
deb {mirror}/ubuntu/ {codename}-security main restricted universe multiverse
"""

# Debian sources.list 模板
DEBIAN_SOURCES_TEMPLATE = """deb {mirror}/debian/ {codename} main contrib non-free non-free-firmware
deb {mirror}/debian/ {codename}-updates main contrib non-free non-free-firmware
deb {mirror}/debian/ {codename}-backports main contrib non-free non-free-firmware
deb {mirror}/debian-security/ {codename}-security main contrib non-free non-free-firmware
"""


@task
def setup_apt_sources(conn: Connection, mirror: str = "cernet", select: bool = False) -> None:
    """更换软件源
    
    Args:
        conn: Fabric 连接对象
        mirror: 镜像源名称或 URL，默认为 cernet
        select: 是否触发交互式选择，默认为 False
    """
    
    # region 获取系统信息
    dist_info: dict = conn.hostvars["distribution"]
    dist_id: str = dist_info.get("id", "").lower()
    codename: str = dist_info.get("codename", "")
    
    if dist_id not in ("ubuntu", "debian"):
        print(f"不支持的发行版: {dist_id}，仅支持 Ubuntu 和 Debian")
        return
    
    if not codename:
        print("无法获取系统代号 (codename)，请检查系统信息")
        return
    # endregion
    
    # region 选择镜像源
    if select:
        choices = [
            questionary.Choice(title=f"{name} ({url})", value=url)
            for name, url in MIRRORS.items()
        ]
        selected_mirror = questionary.select(
            "请选择镜像源:",
            choices=choices,
            default=MIRRORS["cernet"]
        ).ask()
        if selected_mirror is None:
            print("已取消选择")
            return
    else:
        selected_mirror = MIRRORS.get(mirror, mirror)
    # endregion
    
    # region 生成 sources.list 内容
    if dist_id == "ubuntu":
        sources_content = UBUNTU_SOURCES_TEMPLATE.format(mirror=selected_mirror, codename=codename)
    else:
        sources_content = DEBIAN_SOURCES_TEMPLATE.format(mirror=selected_mirror, codename=codename)
    # endregion
    
    # region 备份并写入新配置
    print(f"正在为 {dist_id.capitalize()} {codename} 配置镜像源: {selected_mirror}")
    
    # 备份原配置
    conn.sudo("cp /etc/apt/sources.list /etc/apt/sources.list.bak", hide=True, warn=True)
    
    # 写入新配置：先写入临时文件，再移动到目标位置
    escaped_content = sources_content.replace("'", "'\\''")
    conn.run(f"echo '{escaped_content}' > /tmp/sources.list.tmp")
    conn.sudo("mv /tmp/sources.list.tmp /etc/apt/sources.list")
    
    # 更新软件包索引
    print("正在更新软件包索引...")
    result = conn.sudo("apt-get update", hide=True, warn=True)
    if result.ok:
        print("软件源配置完成")
    else:
        print("软件包索引更新失败，请检查网络连接或镜像源可用性")
    # endregion
