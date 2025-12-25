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
            Tuple[Callable[[dict, str], None], str],
            List[Tuple[Callable[[dict, str], None], str]]
        ]] = None,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None
    ) -> FastAPI:
        load_dotenv()
        # 保存应用实例和配置
        cls._app = app
        cls._config = config
        cls._user_lifespan = app.router.lifespan_context
        # 设置文档
        applications.get_swagger_ui_html = custom_swagger_ui_html
        applications.get_redoc_html = custom_redoc_html
        # 设置app.state host, port
        if not cls._config:
            config = yaml.safe_load(open('app.yaml', 'r', encoding='utf-8'))
            cls._config = config
        # 使用config
        app.state.config = {
            "host": cls._config.get('Host', '0.0.0.0'),
            "port": cls._config.get('Port', 8080),
            "workers": cls._config.get('Workers', 1),
            "h11_max_incomplete_event_size": cls._config.get('H11MaxIncompleteEventSize', 1024 * 1024 * 10)
        }

        # 立即配置非异步服务（在应用启动前）
        if middleware:
            middleware(app, config)

        if nacos_service:
            nacos_service(config)

        if logging_service:
            logging_service(config)

        if database_service:
            cls._setup_database_static(database_service, config)

        # 创建组合生命周期管理器
        @asynccontextmanager
        async def combined_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            # 1. 执行Services自身的初始化
            instance = cls(config, app)

            # 明确判断是否有有效的监听器/发送器配置
            has_valid_listeners = bool(
                rabbitmq_listeners and len(rabbitmq_listeners) > 0)
            has_valid_senders = bool(
                rabbitmq_senders and len(rabbitmq_senders) > 0)

            try:
                # 只有存在监听器或发送器时才初始化RabbitMQService
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
                    yield  # 应用运行阶段
            else:
                yield  # 没有用户生命周期时直接 yield

            # 3. 执行Services的关闭逻辑
            await cls.shutdown()
            logging.info("Services已关闭")

        # 设置组合生命周期
        app.router.lifespan_context = combined_lifespan

        return app

    @staticmethod
    def _setup_database_static(database_service, config):
        """静态方法：设置数据库服务"""
        if isinstance(database_service, tuple):
            db_setup, db_name = database_service
            db_setup(config, db_name)
        elif isinstance(database_service, list):
            for db_setup, db_name in database_service:
                db_setup(config, db_name)

    async def _setup_mq_async(
        self,
        rabbitmq_listeners: Optional[List[RabbitMQListenerConfig]] = None,
        rabbitmq_senders: Optional[List[RabbitMQSendConfig]] = None,
        has_listeners: bool = False,
        has_senders: bool = False,
    ):
        """异步设置MQ相关服务（适配单通道RabbitMQService）"""
        # ========== 只有需要使用MQ时才初始化 ==========
        if not (has_listeners or has_senders):
            logging.info("无RabbitMQ监听器/发送器配置，跳过RabbitMQService初始化")
            return

        # 仅当有监听器或发送器时，才执行RabbitMQService初始化
        RabbitMQService.init(self._config, has_listeners, has_senders)

        # 优化：等待连接池“存在且初始化完成”（避免提前执行后续逻辑）
        start_time = asyncio.get_event_loop().time()
        while not (RabbitMQService._connection_pool and RabbitMQService._connection_pool._initialized) and not RabbitMQService._is_shutdown:
            if asyncio.get_event_loop().time() - start_time > 30:
                raise TimeoutError("RabbitMQ连接池初始化超时（30秒）")
            logging.info("等待RabbitMQ连接池初始化...")
            await asyncio.sleep(0.5)

        # ========== 保留原有严格的发送器/监听器初始化判断 ==========
        # 只有配置了发送器才执行发送器初始化
        if has_senders and rabbitmq_senders:
            # 判断是否有监听器，如果有遍历监听器列表，队列名一样将prefetch_count属性设置到发送器对象中
            if has_listeners and rabbitmq_listeners:
                for sender in rabbitmq_senders:
                    for listener in rabbitmq_listeners:
                        if sender.queue_name == listener.queue_name:
                            sender.prefetch_count = listener.prefetch_count
            await self._setup_senders_async(rabbitmq_senders, has_listeners)

        # 只有配置了监听器才执行监听器初始化
        if has_listeners and rabbitmq_listeners:
            await self._setup_listeners_async(rabbitmq_listeners, has_senders)

        # 验证初始化结果
        if has_listeners:
            # 异步获取客户端数量（适配新的RabbitMQService）
            listener_count = len(RabbitMQService._consumer_tasks)
            logging.info(f"监听器初始化完成，共启动 {listener_count} 个消费者")
            if listener_count == 0:
                logging.warning("未成功初始化任何监听器，请检查配置或MQ服务状态")

    async def _setup_senders_async(self, rabbitmq_senders, has_listeners: bool):
        """设置发送器（适配新的RabbitMQService异步方法）"""
        Services._registered_senders = [
            sender.queue_name for sender in rabbitmq_senders]

        # 将是否有监听器的信息传递给RabbitMQService（异步调用）
        await RabbitMQService.setup_senders(rabbitmq_senders, has_listeners)
        # 更新已注册的发送器（从RabbitMQService获取实际注册的名称）
        Services._registered_senders = RabbitMQService._sender_client_names
        logging.info(f"已注册的RabbitMQ发送器: {Services._registered_senders}")

    async def _setup_listeners_async(self, rabbitmq_listeners, has_senders: bool):
        """设置监听器（适配新的RabbitMQService异步方法）"""
        await RabbitMQService.setup_listeners(rabbitmq_listeners, has_senders)

    @classmethod
    async def send_message(
        cls,
        queue_name: str,
        data: Union[str, Dict[str, Any], BaseModel, None],
        max_retries: int = 3,
        retry_delay: float = 1.0, **kwargs
    ) -> None:
        """发送消息，添加重试机制（适配单通道RabbitMQService）"""
        if not cls._initialized or not cls._loop:
            logging.error("Services not properly initialized!")
            raise ValueError("服务未正确初始化")

        if RabbitMQService._is_shutdown:
            logging.error("RabbitMQService已关闭，无法发送消息")
            raise RuntimeError("RabbitMQ服务已关闭")

        for attempt in range(max_retries):
            try:
                # 验证发送器是否注册
                if queue_name not in cls._registered_senders:
                    cls._registered_senders = RabbitMQService._sender_client_names
                    if queue_name not in cls._registered_senders:
                        raise ValueError(f"发送器 {queue_name} 未注册")

                # 获取发送器（适配新的异步get_sender方法）
                sender = await RabbitMQService.get_sender(queue_name)
                if not sender:
                    raise ValueError(f"发送器 '{queue_name}' 不存在或连接无效")

                # 发送消息（调用RabbitMQService的异步send_message）
                await RabbitMQService.send_message(data, queue_name, **kwargs)
                logging.info(f"消息发送成功（尝试 {attempt+1}/{max_retries}）")
                return

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(
                        f"消息发送失败（已尝试 {max_retries} 次）: {str(e)}", exc_info=True)
                    raise

                logging.warning(
                    f"消息发送失败（尝试 {attempt+1}/{max_retries}）: {str(e)}，"
                    f"{retry_delay}秒后重试..."
                )
                await asyncio.sleep(retry_delay)

    @classmethod
    async def shutdown(cls):
        """关闭所有服务（适配单通道RabbitMQService关闭逻辑）"""
        async with cls._shutdown_lock:
            if RabbitMQService._is_shutdown:
                logging.info("RabbitMQService已关闭，无需重复操作")
                return

            # 关闭RabbitMQ服务（异步调用，内部会关闭所有客户端+消费任务）
            await RabbitMQService.shutdown()

            # 清理全局状态
            cls._initialized = False
            cls._registered_senders.clear()
            logging.info("所有服务已关闭")
