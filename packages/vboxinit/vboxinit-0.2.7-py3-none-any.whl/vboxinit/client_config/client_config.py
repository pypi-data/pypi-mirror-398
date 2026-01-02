
from ..decorators.singleton import Singleton
from fabric import Connection, Config
from pathlib import Path
import questionary
import yaml


CONFIG_FILE = Path.cwd() / "vbi.yaml"


@Singleton
class ClientConfig():
    
    def __init__(self):
        if CONFIG_FILE.exists():
            self.conn = self.create_connection()
        else:
            info = self.collect_server_info()
            if info is None:
                print("用户取消，退出")
                return
            if not info["host"]:
                print("未提供服务器地址，退出")
                return
            self.conn = self.create_connection(info)
        
        if self.conn is None:
            return
        
        self.hostvars = self._gather_facts()
        self.conn.hostvars = self.hostvars 
                
        
        
    # region 用户输入收集
    def collect_server_info(self) -> dict[str, str] | None:
        """通过交互式问答收集服务器连接信息并写入 vbi.yaml，用户取消时返回 None"""
        ip = questionary.text("请输入服务器IP地址:").ask()
        if ip is None:
            return None

        port = questionary.text("请输入SSH端口:", default="22").ask()
        if port is None:
            return None

        username = questionary.text("请输入用户名:", default="vagrant").ask()
        if username is None:
            return None

        password = questionary.password("请输入密码:", default="vagrant").ask()
        if password is None:
            return None

        sudo_password = questionary.password("请输入SUDO密码 (留空则与登录密码相同):").ask()
        if sudo_password is None:
            return None

        host_entry = {
            "host": ip,
            "port": port,
            "user": username,
            "password": password,
            "sudo_password": sudo_password or password,
        }
        config_data = {"hosts": [host_entry]}
        
        confirm = questionary.confirm(f"是否将配置写入 {CONFIG_FILE}?", default=True).ask()
        if confirm is None or not confirm:
            print("用户取消写入配置文件")
            return host_entry
        
        CONFIG_FILE.write_text(yaml.dump(config_data, allow_unicode=True), encoding="utf-8")
        return host_entry
    # endregion
    
    # region 服务器连接
    def create_connection(self, host_info: dict[str, str] | None = None) -> Connection | None:
        """创建 Fabric 连接，优先使用传入的 host_info，否则从 vbi.yaml 读取。连接失败返回 None"""
        if host_info is None:
            config_data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
            host_info = config_data["hosts"][0]
        config = Config(overrides={"sudo": {"password": host_info["sudo_password"]}})
        try:
            conn = Connection(
                host=host_info["host"],
                port=int(host_info.get("port", 22)),
                user=host_info["user"],
                connect_kwargs={"password": host_info["password"]},
                config=config,
            )
            conn.open()
            return conn
        except Exception as e:
            print(f"连接服务器失败: {e}")
            return None
    # endregion
    
    # region 主机信息收集
    def _gather_facts(self) -> dict:
        """收集主机基础信息，类似 Ansible setup 模块"""
        facts = {}
        
        # 发行版信息
        os_release = self._run_cmd("cat /etc/os-release 2>/dev/null || cat /etc/*-release 2>/dev/null | head -20")
        facts["distribution"] = self._parse_os_release(os_release)
        
        # 主机名
        facts["hostname"] = self._run_cmd("hostname").strip()
        facts["fqdn"] = self._run_cmd("hostname -f 2>/dev/null || hostname").strip()
        
        # 内核信息
        facts["kernel"] = self._run_cmd("uname -r").strip()
        facts["architecture"] = self._run_cmd("uname -m").strip()
        
        # 内存信息 (KB)
        meminfo = self._run_cmd("cat /proc/meminfo")
        facts["memory"] = self._parse_meminfo(meminfo)
        
        # CPU 信息
        facts["processor_count"] = int(self._run_cmd("nproc").strip() or "1")
        
        # 网络接口
        facts["default_ipv4"] = self._get_default_ipv4()
        
        # 用户信息
        facts["user"] = self._run_cmd("whoami").strip()
        facts["user_home"] = self._run_cmd("echo $HOME").strip()
        
        return facts
    
    def _run_cmd(self, cmd: str) -> str:
        """执行命令并返回输出，失败时返回空字符串"""
        try:
            result = self.conn.run(cmd, hide=True, warn=True)
            return result.stdout if result.ok else ""
        except Exception:
            return ""
    
    def _parse_os_release(self, content: str) -> dict:
        """解析 /etc/os-release 内容"""
        info = {"name": "", "version": "", "version_id": "", "codename": "", "id": "", "id_like": ""}
        for line in content.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                value = value.strip('"\'')
                key_lower = key.lower()
                if key_lower == "name":
                    info["name"] = value
                elif key_lower == "version":
                    info["version"] = value
                elif key_lower == "version_id":
                    info["version_id"] = value
                elif key_lower == "version_codename":
                    info["codename"] = value
                elif key_lower == "id":
                    info["id"] = value
                elif key_lower == "id_like":
                    info["id_like"] = value
        # 如果 id_like 为空，使用 id 作为回退
        if not info["id_like"]:
            info["id_like"] = info["id"]
        return info
    
    def _parse_meminfo(self, content: str) -> dict:
        """解析 /proc/meminfo 内容，返回 MB 单位"""
        mem = {"total_mb": 0, "free_mb": 0, "available_mb": 0}
        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                key, value = parts[0].rstrip(":"), parts[1]
                if key == "MemTotal":
                    mem["total_mb"] = int(value) // 1024
                elif key == "MemFree":
                    mem["free_mb"] = int(value) // 1024
                elif key == "MemAvailable":
                    mem["available_mb"] = int(value) // 1024
        return mem
    
    def _get_default_ipv4(self) -> dict:
        """获取默认 IPv4 地址和网关"""
        info = {"address": "", "gateway": "", "interface": ""}
        route = self._run_cmd("ip route get 1.1.1.1 2>/dev/null | head -1")
        if route:
            parts = route.split()
            for i, p in enumerate(parts):
                if p == "src" and i + 1 < len(parts):
                    info["address"] = parts[i + 1]
                elif p == "via" and i + 1 < len(parts):
                    info["gateway"] = parts[i + 1]
                elif p == "dev" and i + 1 < len(parts):
                    info["interface"] = parts[i + 1]
        return info
    # endregion