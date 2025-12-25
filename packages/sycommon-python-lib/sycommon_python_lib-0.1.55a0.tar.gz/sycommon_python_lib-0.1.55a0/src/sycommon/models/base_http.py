from typing import TypeVar, Any, Generic
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import status

# 支持任意类型的泛型约束
T = TypeVar('T')


class BaseResponseModel(BaseModel, Generic[T]):
    """基础响应模型，支持自定义状态码"""
    code: int = Field(default=0, description="业务响应码，默认0成功，1失败，支持自定义")
    message: str | None = Field(default=None, description="业务响应信息")
    success: bool = Field(default=True, description="请求是否成功")
    data: T | None = Field(default=None, description="业务响应数据，支持任意类型")
    traceId: str | None = Field(default=None, description="请求链路追踪ID")

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True


def build_response_content(
    data: T | Any = None,
    code: int = 0,
    message: str = None
) -> dict:
    """
    构建响应内容字典，自动根据code判断success

    规则：
    - code为0时success=True（默认成功）
    - 其他任何code值success=False（包括200等自定义状态码）
    """
    # 成功状态仅当code为0时成立，其他任何code都视为失败
    success = code == 0 or code == 200

    response = BaseResponseModel(
        code=code,
        message=message,
        success=success,
        data=data
    )

    if isinstance(response.data, BaseModel):
        return {
            "code": response.code,
            "message": response.message,
            "success": response.success,
            "data": response.data.model_dump()
        }
    else:
        return response.model_dump()


def create_response(
    data: T | Any = None,
    code: int = 0,
    message: str = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """创建完整响应，支持自定义业务状态码"""
    content = build_response_content(data=data, code=code, message=message)
    return JSONResponse(
        content=content,
        status_code=status_code
    )


def success_response(data: T | Any = None, code: int = 0, message: str = None) -> JSONResponse:
    """快捷创建成功响应（code=0, success=True）"""
    return create_response(data=data, code=code, message=message)


def error_response(
    message: str = None,
    code: int = 1,
    data: T | Any = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """快捷创建错误响应，支持自定义错误码（如200）"""
    return create_response(
        data=data,
        code=code,
        message=message,
        status_code=status_code
    )


def success_content(data: T | Any = None) -> dict:
    """构建成功响应内容字典"""
    return build_response_content(data=data)


def error_content(
    message: str = None,
    code: int = 1,
    data: T | Any = None
) -> dict:
    """构建错误响应内容字典，支持自定义错误码"""
    return build_response_content(data=data, code=code, message=message)
