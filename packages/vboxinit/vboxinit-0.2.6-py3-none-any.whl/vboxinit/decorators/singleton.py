"""
单例模式装饰器实现
提供线程安全的单例模式装饰器，确保类只能创建一个实例。
"""

import threading
from functools import wraps
from typing import Dict, Type, Any, Optional


class Singleton:
    """
    单例模式装饰器类
    使用@Singleton装饰器方式实现单例模式，线程安全。
    
    Example:
        @Singleton
        class ConfigManager:
            def __init__(self):
                if hasattr(self, '_initialized'):
                    return
                self._initialized = True
                self.config = {}
                
        # 使用
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2  # True
    """
    
    def __init__(self, cls: Type):
        """
        初始化单例装饰器
        Args:
            cls: 要应用单例模式的类
        """
        self._cls = cls
        self._instance: Optional[Any] = None
        self._lock = threading.Lock()
        
        # 保持原类的属性
        self.__name__ = cls.__name__
        self.__doc__ = cls.__doc__
        self.__module__ = cls.__module__
        self.__qualname__ = cls.__qualname__
    
    def __call__(self, *args, **kwargs):
        """
        实现单例逻辑的调用方法
        使用双重检查锁定确保线程安全
        """
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self._cls(*args, **kwargs)
        return self._instance
    
    def reset_instance(self):
        """重置单例实例（主要用于测试）"""
        with self._lock:
            self._instance = None
    
    def get_instance_count(self):
        """获取实例数量"""
        return 1 if self._instance is not None else 0
    
    def get_original_class(self):
        """获取原始类"""
        return self._cls
    
    @property
    def instance(self):
        """获取当前实例（如果存在）"""
        return self._instance

# 一旦一个类被 Sginleton 装饰 这个类就会变成一个Singleton实例 
# 被装饰类初始化的时候 其实会嗲用 Singleton的 call 方法 直接从Singleton实例当中返回 被装饰类的实例  





class SingletonMeta(type):
    """
    线程安全的单例元类实现
    
    使用方式:
        class MyClass(metaclass=SingletonMeta):
            def __init__(self):
                self.value = "singleton"
    
    特点:
    - 线程安全的双重检查锁定
    - 支持继承
    - 支持多重继承
    - 每个类维护独立的单例实例
    
    Example:
        class DatabaseManager(metaclass=SingletonMeta):
            def __init__(self):
                self.connections = {}
        
        class CacheService(DatabaseManager):  # 继承也是单例
            def __init__(self):
                super().__init__()
                self.cache = {}
        
        # 使用
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2  # True
        
        cache1 = CacheService()
        cache2 = CacheService()
        assert cache1 is cache2  # True
        assert cache1 is not db1  # True (不同类有不同实例)
    """
    _instances: Dict[Type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                # 双重检查锁定模式
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
    
    @classmethod
    def reset_all_instances(mcs):
        """重置所有单例实例（主要用于测试）"""
        with mcs._lock:
            mcs._instances.clear()
    
    @classmethod
    def get_instance_info(mcs):
        """获取所有单例实例信息"""
        return {cls.__name__: id(instance) for cls, instance in mcs._instances.items()}


def singleton(cls: Type) -> Type:
    """
    单例模式装饰器
    使用装饰器方式实现单例模式，线程安全。
    Args:
        cls: 要应用单例模式的类
    Returns:
        应用了单例模式的类
    """
    instances: Dict[Type, Any] = {}
    lock = threading.Lock()
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def thread_safe_singleton(cls: Type) -> Type:
    """
    线程安全的单例装饰器（增强版）
    提供更强的线程安全保证和实例管理功能。
    
    Args:
        cls: 要应用单例模式的类
        
    Returns:
        应用了单例模式的类
    """
    instances: Dict[Type, Any] = {}
    locks: Dict[Type, threading.Lock] = {}
    main_lock = threading.Lock()
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            # 为每个类创建独立的锁
            if cls not in locks:
                with main_lock:
                    if cls not in locks:
                        locks[cls] = threading.Lock()
            
            with locks[cls]:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    # 保持原类的属性
    get_instance.__name__ = cls.__name__
    get_instance.__doc__ = cls.__doc__
    get_instance.__module__ = cls.__module__
    get_instance.__qualname__ = cls.__qualname__
    
    # 添加实用方法
    def reset_instance():
        """重置单例实例（主要用于测试）"""
        if cls in instances:
            with locks.get(cls, threading.Lock()):
                if cls in instances:
                    del instances[cls]
    
    def get_instance_count():
        """获取实例数量"""
        return 1 if cls in instances else 0
    
    get_instance.reset_instance = reset_instance
    get_instance.get_instance_count = get_instance_count
    get_instance._original_class = cls
    
    return get_instance


# 导出的公共接口
__all__ = [
    'singleton',
    'Singleton', 
    'SingletonMeta',
    'thread_safe_singleton'
]