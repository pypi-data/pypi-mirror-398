'''
Author: yasin l1y0l20@qq.com
Date: 2025-04-01 15:00:02
LastEditors: yasin l1y0l20@qq.com
LastEditTime: 2025-04-01 15:12:32
FilePath: /voice_service/app/models/adapters/plugin_loader.py
Description: 

Copyright (c) 2021-2025 by yasin, All Rights Reserved. 
'''
import importlib
import inspect
import pkgutil
import logging
from pathlib import Path
from typing import Dict, Type, List, Optional
import asyncio
from .base import BaseAdapter

logger = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self, package_paths: List[str]):
        """
        初始化插件加载器

        Args:
            package_paths: 要扫描的Python包路径列表，例如 ['app.plugins', 'third_party.adapters']
        """
        self.package_paths = package_paths
        self._lock = asyncio.Lock()
        self._adapters: Dict[str, Type[BaseAdapter]] = {}

    async def discover_plugins(self) -> Dict[str, Type[BaseAdapter]]:
        """发现所有适配器插件"""
        async with self._lock:
            for package_path in self.package_paths:
                await self._scan_package(package_path)
            return self._adapters

    async def _scan_package(self, package_path: str):
        """扫描Python包中的模块"""
        try:
            # 导入包
            # 获取包路径
            package = importlib.import_module(package_path)

            package_dir = Path(package.__file__).parent

            # 遍历包中的所有模块
            for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
                # 跳过子包（如果需要递归扫描，可以修改这里）
                if is_pkg:
                    continue

                # 构建完整模块路径
                full_module_name = f"{package_path}.{module_name}"

                try:
                    # 导入模块
                    module = importlib.import_module(full_module_name)
                    await self._register_adapters(module)
                    logger.info(f"成功加载模块 {full_module_name}")
                except Exception as e:
                    logger.warning(f"加载模块 {full_module_name} 失败: {e}")

        except ImportError as e:
            logger.warning(f"无法导入包 {package_path}: {e}")
        except Exception as e:
            logger.warning(f"扫描包 {package_path} 时发生错误: {e}")

    async def _register_adapters(self, module):
        """注册模块中的所有适配器类"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            # 检查是否是类、是BaseAdapter的子类、不是抽象类、有model_type属性
            if (inspect.isclass(attr) and
                    issubclass(attr, BaseAdapter) and
                    attr != BaseAdapter and  # 排除基类本身
                    not inspect.isabstract(attr) and
                    hasattr(attr, 'model_type')):

                model_type = attr.model_type

                if model_type in self._adapters:
                    logger.warning(f"模型类型 {model_type} 已注册，跳过 {attr.__name__}")
                    continue

                self._adapters[model_type] = attr
                logger.info(f"注册适配器: {model_type} -> {attr.__name__}")

    def get_adapter(self, model_type: str) -> Optional[Type[BaseAdapter]]:
        """获取指定模型类型的适配器类"""
        return self._adapters.get(model_type)

    def get_all_adapters(self) -> Dict[str, Type[BaseAdapter]]:
        """获取所有已注册的适配器"""
        return self._adapters.copy()