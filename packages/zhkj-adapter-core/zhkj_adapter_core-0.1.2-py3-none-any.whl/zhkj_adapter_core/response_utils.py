"""
统一响应格式工具
提供标准化的API响应格式
"""

from flask import jsonify
from typing import Any, Optional, Dict


class ResponseBuilder:
    """响应构建器"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = 200) -> tuple:
        """
        成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            code: HTTP状态码
            
        Returns:
            tuple: (json响应, 状态码)
        """
        response = {
            "success": True,
            "code": code,
            "message": message,
            "data": data,
            "error": None
        }
        return jsonify(response), code
    
    @staticmethod
    def error(message: str = "操作失败", code: int = 400, error: Optional[str] = None) -> tuple:
        """
        错误响应
        
        Args:
            message: 响应消息
            code: HTTP状态码
            error: 错误详情
            
        Returns:
            tuple: (json响应, 状态码)
        """
        response = {
            "success": False,
            "code": code,
            "message": message,
            "data": None,
            "error": error or message
        }
        return jsonify(response), code
    
    @staticmethod
    def not_found(message: str = "资源不存在") -> tuple:
        """404响应"""
        return ResponseBuilder.error(message=message, code=404)
    
    @staticmethod
    def internal_error(message: str = "服务器内部错误") -> tuple:
        """500响应"""
        return ResponseBuilder.error(message=message, code=500)
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> tuple:
        """401响应"""
        return ResponseBuilder.error(message=message, code=401)
    
    @staticmethod
    def forbidden(message: str = "禁止访问") -> tuple:
        """403响应"""
        return ResponseBuilder.error(message=message, code=403)


# 创建全局实例
response = ResponseBuilder()
