from dataclasses import dataclass
from typing import Optional, Any, Dict, Generic, TypeVar
import json
from datetime import datetime

T = TypeVar('T')

@dataclass
class DarrenRet(Generic[T]):
    success: bool = False           # 执行结果：True=成功，False=失败
    message: str = ""              # 提示信息
    data: Optional[T] = None       # 业务数据
    error_code: Optional[str] = None  # 错误码
    timestamp: int = 0             # 时间戳
    extra: Optional[Dict[str, Any]] = None  # 扩展信息

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = int(datetime.now().timestamp())

    @classmethod
    def success(
        cls,
        message: str = "操作成功",
        data: Optional[T] = None,
        **kwargs
    ) -> "DarrenRet[T]":
        """创建成功返回实例"""
        return cls(
            success=True,
            message=message,
            data=data,
            **kwargs
        )

    @classmethod
    def error(
        cls,
        message: str = "操作失败",
        error_code: Optional[str] = None,
        data: Optional[T] = None,
        **kwargs
    ) -> "DarrenRet[T]":
        """创建失败返回实例"""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            data=data,
            **kwargs
        )
    def get_error_code(self) -> Optional[str]:
        """获取错误码"""
        return self.error_code

    def get_message(self) -> str:
        """获取提示信息"""
        return self.message
    def is_success(self) -> bool:
        """判断是否成功"""
        return self.success
    def get_data(self) -> Optional[T]:
        """获取业务数据"""
        return self.data
    def get_data_json(self) ->Dict[str, Any] :
        """获取业务数据并转换为JSON格式"""
        try:
            if isinstance(self.data, str):
                return json.loads(self.data)
            return self.data if isinstance(self.data, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    def is_error(self) -> bool:
        """判断是否失败"""
        return not self.success

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error_code": self.error_code,
            "timestamp": self.timestamp,
            "extra": self.extra
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
