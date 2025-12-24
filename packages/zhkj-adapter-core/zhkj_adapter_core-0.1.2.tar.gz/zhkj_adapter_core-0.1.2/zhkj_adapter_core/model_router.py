'''
Author: yasin l1y0l20@qq.com
Date: 2025-01-24 14:47:44
LastEditors: yasin l1y0l20@qq.com
LastEditTime: 2025-05-22 16:00:11
FilePath: /voice_service/app/core/model_router.py
Description: 

Copyright (c) 2021-2025 by yasin, All Rights Reserved. 
'''
import logging
from typing import Any

from .exception import ModelNotRegisteredError
from .registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRouter:
    _instance = None

    def __new__(cls):
        """单例模式实现"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def dispatch(self, model_type: str, *args, auto_load=False, **kwargs) -> Any:
        """统一任务分发入口"""
        if adapter := ModelRegistry.get_adapter(model_type, auto_load=auto_load):
            try:
                adapter.timer.start_timer("infer")
                return await adapter.infer(*args, *kwargs)
            finally:
                adapter.timer.stop_timer("infer")
                logger.info(adapter.timer.get_summary())

        raise ModelNotRegisteredError(f"Model {model_type} not found")
