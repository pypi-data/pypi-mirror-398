from typing import Any, Optional

# ------------------------------
# 参数类型标记类（兼容 Pydantic）
# ------------------------------


class Param:
    """基础参数元信息类"""

    def __init__(
        self,
        default: Any = ...,
        description: str = "",
        alias: Optional[str] = None,
        deprecated: bool = False
    ):
        self.default = default  # ... 表示必填
        self.description = description
        self.alias = alias
        self.deprecated = deprecated

    def is_required(self) -> bool:
        return self.default is ...

    def get_key(self, param_name: str) -> str:
        return self.alias if self.alias is not None else param_name


class Path(Param):
    """路径参数"""
    pass


class Query(Param):
    """查询参数"""
    pass


class Header(Param):
    """请求头参数"""

    def __init__(self, *args, convert_underscores: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.convert_underscores = convert_underscores

    def get_key(self, param_name: str) -> str:
        key = super().get_key(param_name)
        return key.replace("_", "-") if self.convert_underscores else key


class Cookie(Param):
    """Cookie参数"""
    pass


class Body(Param):
    """JSON请求体参数（支持Pydantic模型）"""

    def __init__(self, *args, embed: bool = False, ** kwargs):
        super().__init__(*args, **kwargs)
        self.embed = embed  # 是否包装在键中


class Form(Param):
    """表单参数（支持Pydantic模型）"""
    pass


class File(Param):
    """文件上传参数"""

    def __init__(self, *args, field_name: str = "file", ** kwargs):
        super().__init__(*args, **kwargs)
        self.field_name = field_name
