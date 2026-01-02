from fabric import Connection, task


@task
def cleanup_network_config(conn: Connection) -> None:
    """根据系统类型清理静态 IP 配置"""
    distro_id = conn.hostvars.get("distribution", {}).get("id", "").lower()
    
    if distro_id == "ubuntu":
        _cleanup_ubuntu_netplan(conn)
    else:
        _cleanup_debian_interfaces(conn)


# region Ubuntu (netplan)
def _cleanup_ubuntu_netplan(conn: Connection) -> None:
    """清理 Ubuntu netplan 配置，恢复 DHCP"""
    print("  检测到 Ubuntu，清理 netplan 配置...")
    
    # 查找非默认的 netplan 配置文件
    result = conn.sudo("find /etc/netplan/ -name '*.yaml' -type f 2>/dev/null || true")
    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    
    # 删除自定义配置文件（保留系统默认的 00-installer-config.yaml 或 01-netcfg.yaml）
    default_files = {"01-network-manager-all.yaml","00-installer-config.yaml", "01-netcfg.yaml", "50-cloud-init.yaml"}
    for f in files:
        filename = f.split("/")[-1]
        if filename not in default_files:
            conn.sudo(f"rm -f {f}")
            print(f"  已删除: {f}")
    
#     # 生成默认 DHCP 配置
#     dhcp_config = """
# network:
#   version: 2
#   ethernets:
#     enp0s8:
#       dhcp4: true
# """
#     conn.sudo(f"bash -c \"echo '{dhcp_config}' > /etc/netplan/50-dhcp.yaml\"")
#     conn.sudo("chmod 600 /etc/netplan/50-dhcp.yaml")
#     print("  已创建 DHCP 配置: /etc/netplan/50-dhcp.yaml")
    
    # 应用 netplan 配置（执行后网络会变更，连接将断开）
    conn.sudo("netplan apply", warn=True)
    print("  已应用 netplan 配置，正在断开连接...")
    conn.close()
# endregion


# region Debian (interfaces)
def _cleanup_debian_interfaces(conn: Connection) -> None:
    """清理 Debian 传统 interfaces 配置"""
    print("  检测到 Debian，清理 interfaces 配置...")
    
    # 查找并删除 interfaces.d 下的配置文件
    result = conn.sudo("find /etc/network/interfaces.d/ -type f 2>/dev/null || true")
    files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    
    for f in files:
        conn.sudo(f"rm -f {f}")
        print(f"  已删除: {f}")
    
    # 重启网络服务
    if files:
        conn.sudo("systemctl restart networking", warn=True)
        print("  已重启网络服务")
# endregion
