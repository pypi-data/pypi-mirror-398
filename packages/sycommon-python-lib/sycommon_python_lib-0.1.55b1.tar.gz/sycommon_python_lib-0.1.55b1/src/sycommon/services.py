import asyncio
import logging
import yaml
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, applications
from pydantic import BaseModel
from typing import Any, Callable, Dict, List, Tuple, Union, Optional, AsyncGenerator
from sycommon.config.Config import SingletonMeta
from sycommon.models.mqlistener_config import RabbitMQListenerConfig
from sycommon.models.mqsend_config import RabbitMQSendConfig
from sycommon.rabbitmq.rabbitmq_service import RabbitMQService
from sycommon.tools.docs import custom_redoc_html, custom_swagger_ui_html


class Services(metaclass=SingletonMeta):
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _config: Optional[dict] = None
    _initialized: bool = False
    _registered_senders: List[str] = []
    _instance: Optional['Services'] = None
    _app: Optional[FastAPI] = None
    _user_lifespan: Optional[Callable] = None
    _shutdown_lock: asyncio.Lock = asyncio.Lock()

    # 用于存储待执行的异步数据库初始化任务
    _pending_async_db_setup: List[Tuple[Callable, str]] = []

    def __init__(self, config: dict, app: FastAPI):
        if not Services._config:
            Services._config = config
        Services._instance = self
        Services._app = app
        self._init_event_loop()

    def _init_event_loop(self):
        """初始化事件循环，确保全局只有一个循环实例"""
        if not Services._loop:
            try:
                Services._loop = asyncio.get_running_loop()
            except RuntimeError:
                Services._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(Services._loop)

    @classmethod
    def plugins(
        cls,
        app: FastAPI,
        config: Optional[dict] = None,
        middleware: Optional[Callable[[FastAPI, dict], None]] = None,
        nacos_service: Optional[Callable[[dict], None]] = None,
        logging_service: Optional[Callable[[dict], None]] = None,
        database_service: Optional[Union[
            Tuple[Callable, str],
            List[Tuple[Callable, str]]
        ]] = None,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None
    ) -> FastAPI:
        load_dotenv()
        cls._app = app
        cls._config = config
        cls._user_lifespan = app.router.lifespan_context

        applications.get_swagger_ui_html = custom_swagger_ui_html
        applications.get_redoc_html = custom_redoc_html

        if not cls._config:
            config = yaml.safe_load(open('app.yaml', 'r', encoding='utf-8'))
            cls._config = config

        app.state.config = {
            "host": cls._config.get('Host', '0.0.0.0'),
            "port": cls._config.get('Port', 8080),
            "workers": cls._config.get('Workers', 1),
            "h11_max_incomplete_event_size": cls._config.get('H11MaxIncompleteEventSize', 1024 * 1024 * 10)
        }

        if middleware:
            middleware(app, config)

        if nacos_service:
            nacos_service(config)

        if logging_service:
            logging_service(config)

        # ========== 处理数据库服务 ==========
        # 清空之前的待执行列表（防止热重载时重复）
        cls._pending_async_db_setup = []

        if database_service:
            # 解析配置并区分同步/异步
            items = [database_service] if isinstance(
                database_service, tuple) else database_service
            for item in items:
                db_setup_func, db_name = item
                if asyncio.iscoroutinefunction(db_setup_func):
                    # 如果是异步函数，加入待执行列表
                    logging.info(f"检测到异步数据库服务: {db_name}，将在应用启动时初始化")
                    cls._pending_async_db_setup.append(item)
                else:
                    # 如果是同步函数，立即执行
                    logging.info(f"执行同步数据库服务: {db_name}")
                    try:
                        db_setup_func(config, db_name)
                    except Exception as e:
                        logging.error(
                            f"同步数据库服务 {db_name} 初始化失败: {e}", exc_info=True)
                        raise

        # 创建组合生命周期管理器
        @asynccontextmanager
        async def combined_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            # 1. 执行Services自身的初始化
            instance = cls(config, app)

            # ========== 执行挂起的异步数据库初始化 ==========
            if cls._pending_async_db_setup:
                logging.info("开始执行异步数据库初始化...")
                for db_setup_func, db_name in cls._pending_async_db_setup:
                    try:
                        await db_setup_func(config, db_name)
                        logging.info(f"异步数据库服务 {db_name} 初始化成功")
                    except Exception as e:
                        logging.error(
                            f"异步数据库服务 {db_name} 初始化失败: {e}", exc_info=True)
                        raise

            # ========== 初始化 MQ ==========
            has_valid_listeners = bool(
                rabbitmq_listeners and len(rabbitmq_listeners) > 0)
            has_valid_senders = bool(
                rabbitmq_senders and len(rabbitmq_senders) > 0)

            try:
                if has_valid_listeners or has_valid_senders:
                    await instance._setup_mq_async(
                        rabbitmq_listeners=rabbitmq_listeners if has_valid_listeners else None,
                        rabbitmq_senders=rabbitmq_senders if has_valid_senders else None,
                        has_listeners=has_valid_listeners,
                        has_senders=has_valid_senders
                    )
                cls._initialized = True
                logging.info("Services初始化完成")
            except Exception as e:
                logging.error(f"Services初始化失败: {str(e)}", exc_info=True)
                raise

            app.state.services = instance

            # 2. 执行用户定义的生命周期
            if cls._user_lifespan:
                async with cls._user_lifespan(app):
                    yield
            else:
                yield

            # 3. 执行Services的关闭逻辑
            await cls.shutdown()
            logging.info("Services已关闭")

        app.router.lifespan_context = combined_lifespan
        return app

    # 移除了 _setup_database_static，因为逻辑已内联到 plugins 中

    async def _setup_mq_async(
        self,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None,
        has_listeners: bool = False,
        has_senders: bool = False,
    ):
        """异步设置MQ相关服务"""
        if not (has_listeners or has_senders):
            logging.info("无RabbitMQ监听器/发送器配置，跳过RabbitMQService初始化")
            return

        RabbitMQService.init(self._config, has_listeners, has_senders)

        start_time = asyncio.get_event_loop().time()
        while not (RabbitMQService._connection_pool and RabbitMQService._connection_pool._initialized) and not RabbitMQService._is_shutdown:
            if asyncio.get_event_loop().time() - start_time > 30:
                raise TimeoutError("RabbitMQ连接池初始化超时（30秒）")
            logging.info("等待RabbitMQ连接池初始化...")
            await asyncio.sleep(0.5)

        if has_senders and rabbitmq_senders:
            if has_listeners and rabbitmq_listeners:
                for sender in rabbitmq_senders:
                    for listener in rabbitmq_listeners:
                        if sender.queue_name == listener.queue_name:
                            sender.prefetch_count = listener.prefetch_count
            await self._setup_senders_async(rabbitmq_senders, has_listeners)

        if has_listeners and rabbitmq_listeners:
            await self._setup_listeners_async(rabbitmq_listeners, has_senders)

        if has_listeners:
            listener_count = len(RabbitMQService._consumer_tasks)
            logging.info(f"监听器初始化完成，共启动 {listener_count} 个消费者")
            if listener_count == 0:
                logging.warning("未成功初始化任何监听器，请检查配置或MQ服务状态")

    async def _setup_senders_async(self, rabbitmq_senders, has_listeners: bool):
        """设置发送器"""
        Services._registered_senders = [
            sender.queue_name for sender in rabbitmq_senders]
        await RabbitMQService.setup_senders(rabbitmq_senders, has_listeners)
        Services._registered_senders = RabbitMQService._sender_client_names
        logging.info(f"已注册的RabbitMQ发送器: {Services._registered_senders}")

    async def _setup_listeners_async(self, rabbitmq_listeners, has_senders: bool):
        """设置监听器"""
        await RabbitMQService.setup_listeners(rabbitmq_listeners, has_senders)

    @classmethod
    async def send_message(
        cls,
        queue_name: str,
        data: Union[str, Dict[str, Any], BaseModel, None],
        max_retries: int = 3,
        retry_delay: float = 1.0, **kwargs
    ) -> None:
        """发送消息"""
        if not cls._initialized or not cls._loop:
            logging.error("Services not properly initialized!")
            raise ValueError("服务未正确初始化")

        if RabbitMQService._is_shutdown:
            logging.error("RabbitMQService已关闭，无法发送消息")
            raise RuntimeError("RabbitMQ服务已关闭")

        for attempt in range(max_retries):
            try:
                if queue_name not in cls._registered_senders:
                    cls._registered_senders = RabbitMQService._sender_client_names
                    if queue_name not in cls._registered_senders:
                        raise ValueError(f"发送器 {queue_name} 未注册")

                sender = await RabbitMQService.get_sender(queue_name)
                if not sender:
                    raise ValueError(f"发送器 '{queue_name}' 不存在或连接无效")

                await RabbitMQService.send_message(data, queue_name, **kwargs)
                logging.info(f"消息发送成功（尝试 {attempt+1}/{max_retries}）")
                return

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(
                        f"消息发送失败（已尝试 {max_retries} 次）: {str(e)}", exc_info=True)
                    raise
                logging.warning(
                    f"消息发送失败（尝试 {attempt+1}/{max_retries}）: {str(e)}，{retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)

    @classmethod
    async def shutdown(cls):
        """关闭所有服务"""
        async with cls._shutdown_lock:
            if RabbitMQService._is_shutdown:
                logging.info("RabbitMQService已关闭，无需重复操作")
                return
            await RabbitMQService.shutdown()
            cls._initialized = False
            cls._registered_senders.clear()
            logging.info("所有服务已关闭")
