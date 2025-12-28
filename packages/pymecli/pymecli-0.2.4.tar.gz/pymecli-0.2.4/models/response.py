from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """标准API响应模型"""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "error": None,
            }
        }


# 定义常用的具体响应类型
class SuccessResponse(StandardResponse[T]):
    """成功响应"""

    success: bool = True


class ErrorResponse(StandardResponse):
    """错误响应"""

    success: bool = False
    error: Optional[str] = None
    data: Optional[Any] = None
