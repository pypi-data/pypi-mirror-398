

import inspect
import importlib
import pkgutil
from pathlib import Path

import fire 
from fabric import Connection
from fabric import Task 
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from .client_config.client_config import ClientConfig

class Config:
    pass 

class ENTRY:
    
    def __init__(self):
        self.modules = self._scan_modules()
        self.hostvars = {}
        self.roles = self._scan_roles()
        self.tasks = self._scan_tasks()
        
    def _scan_roles(self) -> dict[str, dict]:
        """扫描 modules 目录下所有 roles 文件夹中定义的函数"""
        roles = {}
        modules_path = Path(__file__).parent / "modules"
        
        # region 遍历 modules 目录下的非下划线开头的文件夹
        for module_dir in modules_path.iterdir():
            if not module_dir.is_dir() or module_dir.name.startswith("_"):
                continue
            
            roles_dir = module_dir / "roles"
            if not roles_dir.exists() or not roles_dir.is_dir():
                continue
            
            # region 扫描 roles 目录下的所有 Python 文件
            for py_file in roles_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                # 构建模块导入路径
                relative_path = py_file.relative_to(Path(__file__).parent)
                module_name = ".".join(relative_path.with_suffix("").parts)
                
                try:
                    module = importlib.import_module(f".{module_name}", package="vboxinit")
                    # 查找在该模块中定义的函数（排除导入的函数）
                    for name, obj in vars(module).items():
                        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                            roles[name] = {
                                "func": obj,
                                "module": module_dir.name,
                                "source": py_file.name
                            }
                except ImportError as e:
                    print(f"警告: 无法导入模块 {module_name}: {e}")
            # endregion
        # endregion
        
        return roles
    
    def _scan_modules(self) -> list[str]:
        """扫描 modules 目录下的所有模块"""
        modules_path = Path(__file__).parent / "modules"
        return [
            d.name for d in modules_path.iterdir() 
            if d.is_dir() and not d.name.startswith("_")
        ]
    
    def list_modules(self):
        """列出所有可用模块"""
        console = Console()
        columns = Columns(self.modules, equal=True, expand=True, column_first=False)
        panel = Panel(columns, title="可用模块", border_style="blue")
        console.print(panel)
    
    def list_hostvars(self):
        console = Console()
        console.print(ClientConfig().hostvars)
    
    def _scan_tasks(self) -> dict[str, dict]:
        """扫描 linux_init 目录下的所有 task"""
        tasks = {}
        linux_init_path = Path(__file__).parent / "modules" / "linux_init"
        
        for module_info in pkgutil.iter_modules([str(linux_init_path)]):
            module = importlib.import_module(f".modules.linux_init.{module_info.name}", package="vboxinit")
            source_file = Path(getattr(module, "__file__", "")).name
            
            for name, obj in vars(module).items():
                if isinstance(obj, Task):
                    tasks[name] = {"task": obj, "source": source_file}
        
        return tasks
    
    def list_tasks(self):
        """列出所有任务"""
        print("可用任务:")
        for name, task_info in self.tasks.items():
            task_obj = task_info["task"]
            sig = inspect.signature(task_obj.body)
            params = [p for p in sig.parameters.keys() if p != 'ctx']
            params_str = f"({', '.join(params)})" if params else "()"
            doc = (task_obj.body.__doc__ or "").strip().split('\n')[0]
            print(f"  {name}{params_str}: {doc}")
    

    
    def run_task(self):
        """交互式选择并运行任务"""
        import questionary
        
        if not self.tasks:
            print("没有可用的任务")
            return
        
        # region 构建选项列表并让用户选择
        choices = []
        for name, task_info in self.tasks.items():
            task_obj = task_info["task"]
            source_file = task_info["source"]
            doc = (task_obj.body.__doc__ or "").strip().split('\n')[0]
            label = f"{name}: {doc}" if doc else name
            choices.append(questionary.Choice(
                title=label, 
                value=name,
                description=f"@ {source_file}" if source_file else None
            ))
        
        selected = questionary.select(
            "请选择要运行的任务:",
            choices=choices
        ).ask()
        # endregion
        
        if selected is None:
            print("已取消选择")
            return
        
        # region 执行选中的任务
        task_info = self.tasks[selected]
        task_obj = task_info["task"]
        config = ClientConfig()
        doc = (task_obj.body.__doc__ or "").strip()
        if doc:
            print(f"\n{doc}\n")
        try:
            task_obj(config.conn)
        except Exception as e:
            print(f"任务 '{selected}' 执行失败: {e}")
        # endregion
    
    
    def list_roles(self):
        """列出所有可用的 roles"""
        print("可用 roles:")
        for name, info in self.roles.items():
            print(f"  {name} @ {info['module']}/roles/{info['source']}")

    def run_roles(self):
        """交互式选择并运行 role"""
        import questionary
        
        if not self.roles:
            print("没有可用的 roles")
            return
        
        # region 构建选项列表并让用户选择
        choices = [
            questionary.Choice(
                title=name,
                value=name,
                description=f"@ {info['module']}/roles/{info['source']}"
            )
            for name, info in self.roles.items()
        ]
        
        selected = questionary.select(
            "请选择要运行的 role:",
            choices=choices
        ).ask()
        # endregion
        
        if selected is None:
            print("已取消选择")
            return
        
        # region 执行选中的 role
        role_func = self.roles[selected]["func"]
        try:
            role_func(ClientConfig().conn)
        except Exception as e:
            print(f"Role '{selected}' 执行失败: {e}")
        # endregion

def main() -> None:
    try:
        fire.Fire(ENTRY)
    except KeyboardInterrupt:
        print("\n操作已取消")
        exit(0)
    # except Exception as e:
    #     print(f"\n程序执行出错: {str(e)}")
    #     print("请检查您的输入参数或网络连接")
    #     exit(1)