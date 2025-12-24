# models/registry.py
import asyncio
import threading
from typing import Dict, Type, Optional, Callable, List
from .base import BaseAdapter
from .plugin_loader import PluginLoader
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    _registry: Dict[str, Type[BaseAdapter]] = {}
    _instances: Dict[str, BaseAdapter] = {}
    _lock = threading.Lock()  # 线程安全锁

    @classmethod
    def register(cls, model_type: Optional[str] = None) -> Callable:
        """安全的装饰器实现"""

        def decorator(adapter_cls: Type[BaseAdapter]) -> Type[BaseAdapter]:
            # 确定注册的模型类型
            if model_type is not None:
                # 使用装饰器参数
                reg_key = model_type
            else:
                # 从类属性获取
                if not hasattr(adapter_cls, "model_type"):
                    raise AttributeError(f"Adapter class {adapter_cls.__name__} must have 'model_type' attribute")
                reg_key = adapter_cls.model_type

            # 执行注册
            if reg_key in cls._registry:
                raise KeyError(f"Model {reg_key} already registered")

            cls._registry[reg_key] = adapter_cls
            print(f"✅ 成功注册适配器: {reg_key} -> {adapter_cls.__name__}")

            # 确保返回原始的类对象
            return adapter_cls

        return decorator

    @classmethod
    def get_adapter(cls, model_type: str, auto_load: bool = False) -> Optional[BaseAdapter]:
        """获取模型实例（单例模式）"""
        if model_type not in cls._registry:
            raise ValueError(f"Unregistered model type: {model_type}")

        if model_type in cls._instances:
            return cls._instances[model_type]

        if auto_load:
            adapter_cls = cls._registry[model_type]
            cls._instances[model_type] = adapter_cls()
            return cls._instances[model_type]
        else:
            return None

    @classmethod
    def reload_adapter(cls, model_type: str, **kwargs) -> bool:
        """
        触发指定模型的重载
        :param kwargs: 传递给适配器的reload参数
        """
        with cls._lock:
            if adapter := cls.get_adapter(model_type):
                return asyncio.run(adapter.reload(**kwargs))

    @classmethod
    def list_models(cls) -> Dict[str, dict]:
        """获取所有模型元数据"""
        return {
            model_type: {
                "class": adapter_cls,
                "description": getattr(adapter_cls, "description", ""),
                "languages": getattr(adapter_cls, "supported_languages", [])
            }
            for model_type, adapter_cls in cls._registry.items()
        }

    @classmethod
    async def load_from_plugins(cls, search_paths: List[str], activate_models: List[str], preload_adapters: List[str],
                                auto_load=False):
        """从插件动态加载模型适配器"""
        with cls._lock:
            # 初始化插件加载器
            loader = PluginLoader(search_paths)
            adapters = await loader.discover_plugins()
            logger.info(adapters)

            logger.info(preload_adapters)

            # 注册发现的适配器
            for model_type, adapter_cls in adapters.items():
                if model_type in cls._registry or model_type not in activate_models:
                    continue  # 避免覆盖手动注册的适配器
                cls._registry[model_type] = adapter_cls
                if preload_adapters is not None and model_type in preload_adapters:
                    # 需要预加载
                    if adapter := cls.get_adapter(model_type, auto_load=auto_load):
                        await adapter.initialize()
                        logger.info(f"成功安装模型 {model_type}")
