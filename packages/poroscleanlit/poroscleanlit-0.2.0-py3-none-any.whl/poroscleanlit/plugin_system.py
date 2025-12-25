# -*- coding: utf-8 -*-
from typing import Callable, Dict, Any, Optional, List

class PluginRegistry:
    """插件注册中心"""
    _plugins: Dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str):
        """装饰器：用于注册功能插件"""
        def wrapper(func_or_class: Callable):
            cls._plugins[name] = func_or_class
            return func_or_class
        return wrapper

    @classmethod
    def get_plugin(cls, name: str) -> Optional[Callable]:
        """获取指定名称的插件"""
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> List[str]:
        """列出所有已注册的插件"""
        return list(cls._plugins.keys())

