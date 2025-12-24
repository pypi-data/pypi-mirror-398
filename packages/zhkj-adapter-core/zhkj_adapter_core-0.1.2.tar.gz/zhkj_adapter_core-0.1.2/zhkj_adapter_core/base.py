'''
Author: yasin l1y0l20@qq.com
Date: 2025-01-24 16:53:59
LastEditors: yasin l1y0l20@qq.com
LastEditTime: 2025-05-15 16:54:35
FilePath: /voice_service/app/models/adapters/base.py
Description: 

Copyright (c) 2021-2025 by yasin, All Rights Reserved. 
'''
import inspect
from abc import ABC, abstractmethod
from typing import Any
from zhkj_core.timing_instrumentation import TimingInstrumentation

class BaseAdapter(ABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'model_type') and not inspect.isabstract(cls):
            raise TypeError(f"子类 {cls.__name__} 必须定义 'model_type' 类属性")

    def __init__(self, **kwargs):
        super().__init__()
        self.timer = TimingInstrumentation()
    @abstractmethod
    async def infer(self, input_data: Any, **kwargs) -> Any:
        """模型推理抽象方法"""
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    async def reload(self, **kwargs) -> bool:
        """
        重新加载模型
        :param kwargs: 加载参数（模型路径、版本等）
        :return: 是否重载成功
        """
        pass
