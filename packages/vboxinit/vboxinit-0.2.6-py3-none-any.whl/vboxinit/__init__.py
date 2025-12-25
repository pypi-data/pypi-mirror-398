

import inspect
import importlib
import pkgutil
from pathlib import Path

import fire 
from fabric import Connection
from fabric import Task 

from .client_config.client_config import ClientConfig

class Config:
    pass 

class ENTRY:
    
    def __init__(self):
        self.tasks = {}
        pass
    
    def register(self, task_obj, name=None):
        """注册一个任务"""
        task_name = name or task_obj.name
        self.tasks[task_name] = task_obj
    
    def register_from_module(self, module):
        """从模块注册所有任务"""
        for name, obj in vars(module).items():
            if isinstance(obj, Task):
                self.register(obj, name)
    
    def list_tasks(self):
        """列出所有任务"""
        # region 注册 linux_init 目录下的所有 task
        linux_init_path = Path(__file__).parent / "roles" / "linux_init"
        for module_info in pkgutil.iter_modules([str(linux_init_path)]):
            module = importlib.import_module(f".roles.linux_init.{module_info.name}", package="vboxinit")
            self.register_from_module(module)
        # endregion
        
        print("可用任务:")
        for name, task_obj in self.tasks.items():
            # 获取参数信息
            sig = inspect.signature(task_obj.body)
            params = [p for p in sig.parameters.keys() if p != 'ctx']
            params_str = f"({', '.join(params)})" if params else "()"
            
            doc = (task_obj.body.__doc__ or "").strip().split('\n')[0]
            print(f"  {name}{params_str}: {doc}")
    

    
    def run_task(self):
        """交互式选择并运行任务"""
        import questionary
        
        # region 加载所有任务
        linux_init_path = Path(__file__).parent / "roles" / "linux_init"
        for module_info in pkgutil.iter_modules([str(linux_init_path)]):
            module = importlib.import_module(f".roles.linux_init.{module_info.name}", package="vboxinit")
            self.register_from_module(module)
        # endregion
        
        if not self.tasks:
            print("没有可用的任务")
            return
        
        # region 构建选项列表并让用户选择
        choices = []
        for name, task_obj in self.tasks.items():
            doc = (task_obj.body.__doc__ or "").strip().split('\n')[0]
            label = f"{name}: {doc}" if doc else name
            choices.append(questionary.Choice(title=label, value=name))
        
        selected = questionary.select(
            "请选择要运行的任务:",
            choices=choices
        ).ask()
        # endregion
        
        if selected is None:
            print("已取消选择")
            return
        
        # region 执行选中的任务
        task_obj = self.tasks[selected]
        config = ClientConfig()
        task_obj(config.conn)
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