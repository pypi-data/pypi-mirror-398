import io
import os
import time
import inspect
from typing import Any, Dict, Optional, Literal, Type, TypeVar
from urllib.parse import urljoin

from sycommon.tools.snowflake import Snowflake

import aiohttp
from pydantic import BaseModel
from sycommon.synacos.param import Body, Cookie, File, Form, Header, Param, Path, Query
from sycommon.logging.kafka_log import SYLogger
from sycommon.synacos.nacos_service import NacosService

# 定义 Pydantic 模型泛型（用于响应解析）
T = TypeVar('T', bound=BaseModel)

# ------------------------------
# Feign客户端装饰器（支持Pydantic）
# ------------------------------


def feign_client(
    service_name: str,
    path_prefix: str = "",
    default_timeout: Optional[float] = None,
    default_headers: Optional[Dict[str, str]] = None
):
    default_headers = default_headers or {}
    default_headers["x-traceId-header"] = SYLogger.get_trace_id() or Snowflake.next_id()

    def decorator(cls):
        class FeignClient:
            def __init__(self):
                self.service_name = service_name
                self.path_prefix = path_prefix
                self.default_timeout = default_timeout
                self.default_headers = default_headers.copy()
                self.nacos_manager: Optional[NacosService] = None
                self.session: Optional[aiohttp.ClientSession] = None

            def __getattr__(self, name: str):
                if not hasattr(cls, name):
                    raise AttributeError(f"类 {cls.__name__} 不存在方法 {name}")

                func = getattr(cls, name)
                sig = inspect.signature(func)
                param_meta = self._parse_param_meta(sig)
                # 获取响应模型（从返回类型注解中提取 Pydantic 模型）
                resp_model = self._get_response_model(sig)

                async def wrapper(*args, **kwargs) -> Any:
                    if not self.session:
                        self.session = aiohttp.ClientSession()
                    if not self.nacos_manager:
                        self.nacos_manager = NacosService(None)

                    try:
                        bound_args = self._bind_arguments(
                            func, sig, args, kwargs)
                        self._validate_required_params(param_meta, bound_args)

                        request_meta = getattr(func, "_feign_meta", {})
                        method = request_meta.get("method", "GET").upper()
                        path = request_meta.get("path", "")
                        is_upload = request_meta.get("is_upload", False)
                        method_headers = request_meta.get("headers", {})
                        timeout = request_meta.get(
                            "timeout", self.default_timeout)

                        headers = self._build_headers(
                            param_meta, bound_args, method_headers)
                        full_path = f"{self.path_prefix}{path}"
                        full_path = self._replace_path_params(
                            full_path, param_meta, bound_args)

                        base_url = await self._get_service_base_url(headers)
                        url = urljoin(base_url, full_path)
                        SYLogger.info(f"请求: {method} {url}")

                        query_params = self._get_query_params(
                            param_meta, bound_args)
                        cookies = self._get_cookies(param_meta, bound_args)
                        # 处理请求数据（支持 Pydantic 模型转字典）
                        request_data = await self._get_request_data(
                            method, param_meta, bound_args, is_upload, method_headers
                        )

                        async with self.session.request(
                            method=method,
                            url=url,
                            headers=headers,
                            params=query_params,
                            cookies=cookies,
                            json=request_data if not (is_upload or isinstance(
                                request_data, aiohttp.FormData)) else None,
                            data=request_data if is_upload or isinstance(
                                request_data, aiohttp.FormData) else None,
                            timeout=timeout
                        ) as response:
                            # 处理响应（支持 Pydantic 模型解析）
                            return await self._handle_response(response, resp_model)

                    finally:
                        if self.session:
                            await self.session.close()
                            self.session = None

                return wrapper

            def _parse_param_meta(self, sig: inspect.Signature) -> Dict[str, Param]:
                param_meta = {}
                for param in sig.parameters.values():
                    if param.name == "self":
                        continue
                    if isinstance(param.default, Param):
                        param_meta[param.name] = param.default
                    else:
                        if param.default == inspect.Parameter.empty:
                            param_meta[param.name] = Query(..., description="")
                        else:
                            param_meta[param.name] = Query(
                                param.default, description="")
                return param_meta

            def _get_response_model(self, sig: inspect.Signature) -> Optional[Type[BaseModel]]:
                """从函数返回类型注解中提取 Pydantic 模型"""
                return_annotation = sig.return_annotation
                # 支持直接注解（如 -> ProductResp）或 Optional（如 -> Optional[ProductResp]）
                if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ is Optional:
                    return_annotation = return_annotation.__args__[0]
                # 检查是否为 Pydantic 模型
                if inspect.isclass(return_annotation) and issubclass(return_annotation, BaseModel):
                    return return_annotation
                return None

            def _bind_arguments(self, func, sig: inspect.Signature, args, kwargs) -> Dict[str, Any]:
                try:
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    return {k: v for k, v in bound_args.arguments.items() if k != "self"}
                except TypeError as e:
                    SYLogger.error(f"参数绑定失败 [{func.__name__}]: {str(e)}")
                    raise

            def _validate_required_params(self, param_meta: Dict[str, Param], bound_args: Dict[str, Any]):
                missing = [
                    meta.get_key(name) for name, meta in param_meta.items()
                    if meta.is_required() and name not in bound_args
                ]
                if missing:
                    raise ValueError(f"缺少必填参数: {', '.join(missing)}")

            def _build_headers(self, param_meta: Dict[str, Param], bound_args: Dict[str, Any], method_headers: Dict[str, str]) -> Dict[str, str]:
                headers = self.default_headers.copy()
                headers.update(method_headers)
                headers["x-traceId-header"] = SYLogger.get_trace_id() or Snowflake.next_id()
                for name, meta in param_meta.items():
                    if isinstance(meta, Header) and name in bound_args:
                        value = bound_args[name]
                        if value is not None:
                            headers[meta.get_key(name)] = str(value)
                return headers

            def _replace_path_params(self, path: str, param_meta: Dict[str, Param], bound_args: Dict[str, Any]) -> str:
                for name, meta in param_meta.items():
                    if isinstance(meta, Path) and name in bound_args:
                        path = path.replace(
                            f"{{{meta.get_key(name)}}}", str(bound_args[name]))
                return path

            def _get_query_params(self, param_meta: Dict[str, Param], bound_args: Dict[str, Any]) -> Dict[str, str]:
                return {
                    param_meta[name].get_key(name): str(value)
                    for name, value in bound_args.items()
                    if isinstance(param_meta.get(name), Query) and value is not None
                }

            def _get_cookies(self, param_meta: Dict[str, Param], bound_args: Dict[str, Any]) -> Dict[str, str]:
                return {
                    param_meta[name].get_key(name): str(value)
                    for name, value in bound_args.items()
                    if isinstance(param_meta.get(name), Cookie) and value is not None
                }

            async def _get_request_data(
                self,
                method: str,
                param_meta: Dict[str, Param],
                bound_args: Dict[str, Any],
                is_upload: bool,
                method_headers: Dict[str, str]
            ) -> Any:
                """处理请求数据（支持 Pydantic 模型转字典）"""
                if is_upload:
                    form_data = aiohttp.FormData()
                    # 处理文件
                    file_params = {
                        n: m for n, m in param_meta.items() if isinstance(m, File)}
                    for name, meta in file_params.items():
                        if name not in bound_args:
                            continue
                        file_paths = bound_args[name]
                        file_paths = [file_paths] if isinstance(
                            file_paths, str) else file_paths
                        for path in file_paths:
                            if not os.path.exists(path):
                                raise FileNotFoundError(f"文件不存在: {path}")
                            with open(path, "rb") as f:
                                form_data.add_field(
                                    meta.field_name, f.read(), filename=os.path.basename(path)
                                )
                    # 处理表单字段（支持 Pydantic 模型）
                    form_params = {
                        n: m for n, m in param_meta.items() if isinstance(m, Form)}
                    for name, meta in form_params.items():
                        if name not in bound_args or bound_args[name] is None:
                            continue
                        value = bound_args[name]
                        # 若为 Pydantic 模型，转为字典
                        if isinstance(value, BaseModel):
                            value = value.dict()
                        form_data.add_field(meta.get_key(name), str(
                            value) if not isinstance(value, dict) else value)
                    return form_data

                # 处理表单提交（x-www-form-urlencoded）
                content_type = self.default_headers.get(
                    "Content-Type") or method_headers.get("Content-Type", "")
                if "application/x-www-form-urlencoded" in content_type:
                    form_data = {}
                    for name, value in bound_args.items():
                        meta = param_meta.get(name)
                        if isinstance(meta, Form) and value is not None:
                            # Pydantic 模型转字典
                            if isinstance(value, BaseModel):
                                value = value.dict()
                            form_data[meta.get_key(name)] = str(
                                value) if not isinstance(value, dict) else value
                    return form_data

                # 处理 JSON 请求体（支持 Pydantic 模型）
                if method in ["POST", "PUT", "PATCH", "DELETE"]:
                    body_params = [
                        name for name, meta in param_meta.items() if isinstance(meta, Body)]
                    if body_params:
                        body_data = {}
                        for name in body_params:
                            meta = param_meta[name]
                            value = bound_args.get(name)
                            if value is None:
                                continue
                            # 若为 Pydantic 模型，转为字典
                            if isinstance(value, BaseModel):
                                value = value.dict()
                            if meta.embed:
                                body_data[meta.get_key(name)] = value
                            else:
                                body_data = value if not isinstance(value, dict) else {
                                    ** body_data, **value}
                        return body_data
                return None

            async def _get_service_base_url(self, headers: Dict[str, str]) -> str:
                version = headers.get("s-y-version")
                instances = self.nacos_manager.get_service_instances(
                    self.service_name, target_version=version)
                if not instances:
                    raise RuntimeError(f"服务 [{self.service_name}] 无可用实例")
                return f"http://{instances[int(time.time()) % len(instances)]['ip']}:{instances[0]['port']}"

            async def _handle_response(self, response: aiohttp.ClientResponse, resp_model: Optional[Type[BaseModel]]) -> Any:
                """处理响应（支持 Pydantic 模型解析）"""
                status = response.status
                if 200 <= status < 300:
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        json_data = await response.json()
                        # 若指定了 Pydantic 响应模型，自动解析
                        if resp_model is not None:
                            return resp_model(** json_data)  # 用响应数据初始化模型
                        return json_data
                    else:
                        return io.BytesIO(await response.read())
                else:
                    error_msg = await response.text()
                    SYLogger.error(f"请求失败 [{status}]: {error_msg}")
                    raise RuntimeError(f"HTTP {status}: {error_msg}")

        return FeignClient

    return decorator


def feign_request(
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
    path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None
):
    def decorator(func):
        func._feign_meta = {
            "method": method.upper(),
            "path": path,
            "headers": headers.copy() if headers else {},
            "is_upload": False,
            "timeout": timeout
        }
        return func
    return decorator


def feign_upload(field_name: str = "file"):
    def decorator(func):
        if not hasattr(func, "_feign_meta"):
            raise ValueError("feign_upload必须与feign_request一起使用")
        func._feign_meta["is_upload"] = True
        func._feign_meta["upload_field"] = field_name
        return func
    return decorator
