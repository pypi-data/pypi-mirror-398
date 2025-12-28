# -*- coding: utf-8 -*-
from typing import Callable, Dict, Any, Optional, List

class PluginRegistry:
    """Plugin Registry Center"""
    _plugins: Dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator: Used to register function plugins"""
        def wrapper(func_or_class: Callable):
            cls._plugins[name] = func_or_class
            return func_or_class
        return wrapper

    @classmethod
    def get_plugin(cls, name: str) -> Optional[Callable]:
        """Get plugin by specified name"""
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> List[str]:
        """List all registered plugins"""
        return list(cls._plugins.keys())

