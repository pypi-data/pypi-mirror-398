
from ..decorators.singleton import Singleton
from fabric import Connection, Config
from pathlib import Path
import questionary
import yaml


CONFIG_FILE = Path.cwd() / "fabric.yaml"


@Singleton
class ClientConfig():
    
    def __init__(self):
        if not CONFIG_FILE.exists():
            info = self.collect_server_info()
            if info is None:
                print("用户取消，退出")
                return
            if not info["host"]:
                print("未提供服务器地址，退出")
                return
        self.conn = self.create_connection()
        
    # region 用户输入收集
    def collect_server_info(self) -> dict[str, str] | None:
        """通过交互式问答收集服务器连接信息并写入 fabric.yaml，用户取消时返回 None"""
        ip = questionary.text("请输入服务器IP地址:").ask()
        if ip is None:
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
            "user": username,
            "password": password,
            "sudo_password": sudo_password or password,
        }
        config_data = {"hosts": [host_entry]}
        CONFIG_FILE.write_text(yaml.dump(config_data, allow_unicode=True), encoding="utf-8")
        return host_entry
    # endregion
    
    # region 服务器连接
    def create_connection(self) -> Connection:
        """从 fabric.yaml 读取配置并创建 Fabric 连接（使用 hosts 列表中的第一个）"""
        config_data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
        host_info = config_data["hosts"][0]
        config = Config(overrides={"sudo": {"password": host_info["sudo_password"]}})
        return Connection(
            host=host_info["host"],
            user=host_info["user"],
            connect_kwargs={"password": host_info["password"]},
            config=config,
        )
    # endregion