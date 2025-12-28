import asyncio
import json
from typing import (
    Callable, Coroutine, Dict, List, Optional, Type, Union, Any
)
from pydantic import BaseModel
from aio_pika.abc import AbstractIncomingMessage, ConsumerTag

from sycommon.models.mqmsg_model import MQMsgModel
from sycommon.models.mqlistener_config import RabbitMQListenerConfig
from sycommon.models.mqsend_config import RabbitMQSendConfig
from sycommon.models.sso_user import SsoUser
from sycommon.logging.kafka_log import SYLogger
from sycommon.rabbitmq.rabbitmq_client import RabbitMQClient, RabbitMQConnectionPool

logger = SYLogger


class RabbitMQService:
    """
    RabbitMQ服务封装，管理多个客户端实例（适配单通道连接池）
    核心特性：基于单通道连接池复用资源，简化状态管理，依赖原生自动重连
    """

    # 保存多个客户端实例（共享单通道，仅维护配置差异）
    _clients: Dict[str, RabbitMQClient] = {}
    # 保存消息处理器
    _message_handlers: Dict[str, Callable[[
        MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]]] = {}
    # 保存消费者任务
    _consumer_tasks: Dict[str, asyncio.Task] = {}
    # 保存配置信息
    _config: Optional[dict] = None
    # 存储发送客户端的名称
    _sender_client_names: List[str] = []
    # 用于控制消费者任务退出的事件
    _consumer_events: Dict[str, asyncio.Event] = {}
    # 存储消费者标签
    _consumer_tags: Dict[str, ConsumerTag] = {}
    # 异步锁，确保初始化安全
    _init_locks: Dict[str, asyncio.Lock] = {}
    # 标记是否有监听器和发送器
    _has_listeners: bool = False
    _has_senders: bool = False
    # 消费启动超时设置
    CONSUMER_START_TIMEOUT = 30  # 30秒超时
    # 连接池实例（单通道）
    _connection_pool: Optional[RabbitMQConnectionPool] = None
    # 服务关闭标记
    _is_shutdown: bool = False
    # 服务关闭锁
    _shutdown_lock = asyncio.Lock()
    # 连接状态监控任务
    _connection_monitor_task: Optional[asyncio.Task] = None
    # 重连配置
    RECONNECT_INTERVAL = 15  # 重连基础间隔（秒）

    @classmethod
    def init(cls, config: dict, has_listeners: bool = False, has_senders: bool = False) -> Type['RabbitMQService']:
        """初始化RabbitMQ服务（支持集群配置），同时创建单通道连接池"""
        from sycommon.synacos.nacos_service import NacosService

        # 防止重复初始化
        if cls._config:
            logger.warning("RabbitMQService已初始化，无需重复调用")
            return cls

        # 获取MQ配置
        cls._config = NacosService(config).share_configs.get(
            "mq.yml", {}).get('spring', {}).get('rabbitmq', {})
        cls._config["APP_NAME"] = config.get("Name", "")

        # 打印关键配置信息（显示所有集群节点）
        logger.info(
            f"RabbitMQ服务初始化 - 集群节点: {cls._config.get('host')}, "
            f"端口: {cls._config.get('port')}, "
            f"虚拟主机: {cls._config.get('virtual-host')}, "
            f"应用名: {cls._config.get('APP_NAME')}, "
            f"心跳: {cls._config.get('heartbeat', 30)}s"
        )

        # 保存发送器和监听器存在状态
        cls._has_listeners = has_listeners
        cls._has_senders = has_senders
        cls._is_shutdown = False

        # 初始化连接池（在单独的异步方法中启动）
        asyncio.create_task(cls._init_connection_pool())

        # 启动连接监控任务（监听连接状态，自动重连）
        cls._connection_monitor_task = asyncio.create_task(
            cls._monitor_connections())

        return cls

    @classmethod
    async def _init_connection_pool(cls):
        """初始化单通道连接池（异步操作，带重试）"""
        if cls._connection_pool or not cls._config or cls._is_shutdown:
            return

        try:
            # 解析集群节点
            hosts_str = cls._config.get('host', "")
            hosts_list = [host.strip()
                          for host in hosts_str.split(',') if host.strip()]
            if not hosts_list:
                raise ValueError("RabbitMQ集群配置为空，请检查host参数")

            global_prefetch_count = cls._config.get('prefetch_count', 2)

            # 创建单通道连接池（已移除channel_pool_size参数）
            cls._connection_pool = RabbitMQConnectionPool(
                hosts=hosts_list,
                port=cls._config.get('port', 5672),
                username=cls._config.get('username', ""),
                password=cls._config.get('password', ""),
                virtualhost=cls._config.get('virtual-host', "/"),
                app_name=cls._config.get("APP_NAME", ""),
                prefetch_count=global_prefetch_count,
                heartbeat=cls._config.get('heartbeat', 30),
                connection_timeout=cls._config.get('connection_timeout', 30),
                reconnect_interval=cls._config.get('reconnect_interval', 5),
            )

            # 初始化连接池
            await asyncio.wait_for(cls._connection_pool.init_pools(), timeout=30)
            logger.info("RabbitMQ单通道连接池初始化成功")

        except Exception as e:
            logger.error(f"RabbitMQ连接池初始化失败: {str(e)}", exc_info=True)
            # 连接池初始化失败时重试（未关闭状态下）
            if not cls._is_shutdown:
                await asyncio.sleep(cls.RECONNECT_INTERVAL)
                asyncio.create_task(cls._init_connection_pool())

    @classmethod
    async def _monitor_connections(cls):
        """连接监控任务：定期检查所有客户端连接状态，依赖连接池原生重连"""
        logger.info("RabbitMQ连接监控任务启动")
        while not cls._is_shutdown:
            try:
                await asyncio.sleep(cls.RECONNECT_INTERVAL)  # 固定15秒间隔

                # 跳过未初始化的连接池
                if not cls._connection_pool or not cls._connection_pool._initialized:
                    continue

                # 检查连接池本身状态
                pool_alive = await cls._connection_pool.is_alive
                if not pool_alive:
                    logger.error("RabbitMQ连接池已断开，等待原生自动重连")
                    continue

                # 检查所有客户端连接（单通道场景下，客户端状态依赖通道有效性）
                for client_name, client in list(cls._clients.items()):
                    try:
                        client_connected = await client.is_connected
                        if not client_connected:
                            logger.warning(
                                f"客户端 '{client_name}' 连接异常，触发重连")
                            asyncio.create_task(
                                cls._reconnect_client(client_name, client))
                    except Exception as e:
                        logger.error(
                            f"监控客户端 '{client_name}' 连接状态失败: {str(e)}", exc_info=True)

            except Exception as e:
                logger.error("RabbitMQ连接监控任务异常", exc_info=True)
                await asyncio.sleep(cls.RECONNECT_INTERVAL)  # 异常后延迟重启监控

        logger.info("RabbitMQ连接监控任务停止")

    @classmethod
    async def _clean_client_resources(cls, client: RabbitMQClient):
        """清理客户端无效资源（单通道场景下仅重置状态，无需归还通道）"""
        try:
            # 先停止消费（避免消费中操作资源）
            if client._consumer_tag:
                await client.stop_consuming()
            logger.debug("客户端无效资源清理完成（单通道无需归还）")
        except Exception as e:
            logger.warning(f"释放客户端无效资源失败: {str(e)}")
        finally:
            # 强制重置客户端状态（通道由连接池自动恢复）
            client._channel = None
            client._channel_conn = None
            client._exchange = None
            client._queue = None
            client._consumer_tag = None

    @classmethod
    async def _reconnect_client(cls, client_name: str, client: RabbitMQClient) -> bool:
        """客户端重连（依赖连接池原生重连，仅重建客户端资源）"""
        if cls._is_shutdown or not await cls._connection_pool.is_alive:
            return False

        # 重连冷却
        await asyncio.sleep(cls.RECONNECT_INTERVAL)

        try:
            # 清理旧资源
            await cls._clean_client_resources(client)

            # 执行重连（客户端内部会从连接池获取新通道）
            await client.connect()

            # 验证重连结果
            if await client.is_connected:
                logger.info(f"客户端 '{client_name}' 重连成功")
                # 如果是消费者，重新启动消费
                if client_name in cls._message_handlers:
                    await cls.start_consumer(client_name)
                return True
            else:
                logger.warning(f"客户端 '{client_name}' 重连失败：资源未完全初始化")
                return False
        except Exception as e:
            logger.error(f"客户端 '{client_name}' 重连失败: {str(e)}", exc_info=True)
            # 重连失败后，由监控任务再次触发（避免死循环）
            return False

    @classmethod
    async def _create_client(cls, queue_name: str, **kwargs) -> RabbitMQClient:
        """创建客户端实例（适配单通道连接池的RabbitMQClient）"""
        if cls._is_shutdown:
            raise RuntimeError("RabbitMQService已关闭，无法创建客户端")

        if not cls._connection_pool or not cls._connection_pool._initialized:
            # 等待连接池初始化
            start_time = asyncio.get_event_loop().time()
            while not (cls._connection_pool and cls._connection_pool._initialized) and not cls._is_shutdown:
                if asyncio.get_event_loop().time() - start_time > 30:
                    raise TimeoutError("等待连接池初始化超时")
                await asyncio.sleep(1)
            if cls._is_shutdown:
                raise RuntimeError("服务关闭中，取消创建客户端")

        app_name = kwargs.get('app_name', cls._config.get(
            "APP_NAME", "")) if cls._config else ""
        is_sender = not cls._has_listeners

        # 根据组件类型决定是否允许创建队列
        create_if_not_exists = cls._has_listeners  # 只有监听器允许创建队列

        # 为监听器队列名称拼接应用名
        processed_queue_name = queue_name
        if create_if_not_exists and not is_sender and processed_queue_name and app_name:
            if not processed_queue_name.endswith(f".{app_name}"):
                processed_queue_name = f"{processed_queue_name}.{app_name}"
                logger.info(f"监听器队列名称自动拼接app-name: {processed_queue_name}")
            else:
                logger.info(f"监听器队列已包含app-name: {processed_queue_name}")

        logger.info(
            f"创建客户端 - 队列: {processed_queue_name}, 发送器: {is_sender}, "
            f"允许创建: {create_if_not_exists}"
        )

        # 创建客户端实例（适配精简版RabbitMQClient参数）
        client = RabbitMQClient(
            connection_pool=cls._connection_pool,
            exchange_name=cls._config.get(
                'exchange_name', "system.topic.exchange"),
            exchange_type=kwargs.get('exchange_type', "topic"),
            queue_name=processed_queue_name,
            routing_key=kwargs.get(
                'routing_key', f"{processed_queue_name.split('.')[0]}.#" if processed_queue_name else "#"),
            durable=kwargs.get('durable', True),
            auto_delete=kwargs.get('auto_delete', False),
            auto_parse_json=kwargs.get('auto_parse_json', True),
            create_if_not_exists=create_if_not_exists,
            prefetch_count=kwargs.get('prefetch_count', 2),
        )

        # 连接客户端（单通道场景下快速连接）
        await client.connect()

        return client

    @classmethod
    async def get_client(
        cls,
        client_name: str = "default", **kwargs
    ) -> RabbitMQClient:
        """获取或创建RabbitMQ客户端（单通道池，线程安全）"""
        if cls._is_shutdown:
            raise RuntimeError("RabbitMQService已关闭，无法获取客户端")

        if not cls._config:
            raise ValueError("RabbitMQService尚未初始化，请先调用init方法")

        # 等待连接池就绪
        if not cls._connection_pool or not cls._connection_pool._initialized:
            start_time = asyncio.get_event_loop().time()
            while not (cls._connection_pool and cls._connection_pool._initialized) and not cls._is_shutdown:
                if asyncio.get_event_loop().time() - start_time > 30:
                    raise TimeoutError("等待连接池初始化超时")
                await asyncio.sleep(1)
            if cls._is_shutdown:
                raise RuntimeError("服务关闭中，取消获取客户端")

        # 确保锁存在
        if client_name not in cls._init_locks:
            cls._init_locks[client_name] = asyncio.Lock()

        async with cls._init_locks[client_name]:
            # 如果客户端已存在且连接有效，直接返回
            if client_name in cls._clients:
                client = cls._clients[client_name]
                is_sender = not cls._has_listeners or (
                    not kwargs.get('create_if_not_exists', True))

                if await client.is_connected:
                    # 如果是监听器但队列未初始化，重新连接
                    if not is_sender and not client._queue:
                        logger.info(f"客户端 '{client_name}' 队列未初始化，重新连接")
                        client.create_if_not_exists = True
                        await client.connect()
                    return client
                else:
                    logger.info(f"客户端 '{client_name}' 连接已断开，重新连接")
                    if not is_sender:
                        client.create_if_not_exists = True
                    await client.connect()
                    return client

            # 创建新客户端
            initial_queue_name = kwargs.pop('queue_name', '')
            is_sender = not cls._has_listeners or (
                not kwargs.get('create_if_not_exists', True))

            # 发送器特殊处理
            if is_sender:
                kwargs['create_if_not_exists'] = False
                client = await cls._create_client(
                    initial_queue_name,
                    app_name=cls._config.get("APP_NAME", ""),
                    **kwargs
                )
                cls._clients[client_name] = client
                return client

            # 监听器逻辑（单通道支持多队列声明，无需跟踪已初始化队列）
            kwargs['create_if_not_exists'] = True

            # 创建并连接客户端
            client = await cls._create_client(
                initial_queue_name,
                app_name=cls._config.get("APP_NAME", ""),
                **kwargs
            )

            # 验证队列是否创建成功
            if not client._queue:
                logger.error(f"队列 '{initial_queue_name}' 创建失败，尝试重新创建")
                client.create_if_not_exists = True
                await client.connect()
                if not client._queue:
                    raise Exception(f"无法创建队列 '{initial_queue_name}'")

            cls._clients[client_name] = client
            return client

    @classmethod
    async def setup_senders(cls, senders: List[RabbitMQSendConfig], has_listeners: bool = False, **kwargs) -> None:
        """设置消息发送器（适配单通道客户端）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法设置发送器")
            return

        cls._has_senders = True
        cls._has_listeners = has_listeners
        logger.info(f"开始设置 {len(senders)} 个消息发送器")

        for idx, sender_config in enumerate(senders):
            try:
                if not sender_config.queue_name:
                    raise ValueError(f"发送器配置第{idx+1}项缺少queue_name")

                prefetch_count = sender_config.prefetch_count
                queue_name = sender_config.queue_name
                app_name = cls._config.get(
                    "APP_NAME", "") if cls._config else ""

                # 处理发送器队列名称，移除可能的app-name后缀
                normalized_name = queue_name
                if app_name and normalized_name.endswith(f".{app_name}"):
                    normalized_name = normalized_name[:-len(f".{app_name}")]
                    logger.info(f"发送器队列名称移除app-name后缀: {normalized_name}")

                # 检查是否已初始化
                if normalized_name in cls._sender_client_names:
                    logger.info(f"发送客户端 '{normalized_name}' 已存在，跳过")
                    continue

                # 获取或创建客户端
                if normalized_name in cls._clients:
                    client = cls._clients[normalized_name]
                    if not await client.is_connected:
                        await client.connect()
                else:
                    client = await cls.get_client(
                        client_name=normalized_name,
                        exchange_type=sender_config.exchange_type,
                        durable=sender_config.durable,
                        auto_delete=sender_config.auto_delete,
                        auto_parse_json=sender_config.auto_parse_json,
                        queue_name=queue_name,
                        create_if_not_exists=False,
                        prefetch_count=prefetch_count,
                        **kwargs
                    )

                # 记录客户端
                if normalized_name not in cls._clients:
                    cls._clients[normalized_name] = client
                    logger.info(f"发送客户端 '{normalized_name}' 已添加")

                if normalized_name not in cls._sender_client_names:
                    cls._sender_client_names.append(normalized_name)
                    logger.info(f"发送客户端 '{normalized_name}' 初始化成功")

            except Exception as e:
                logger.error(
                    f"初始化发送客户端第{idx+1}项失败: {str(e)}", exc_info=True)

        logger.info(f"消息发送器设置完成，共 {len(cls._sender_client_names)} 个发送器")

    @classmethod
    async def setup_listeners(cls, listeners: List[RabbitMQListenerConfig], has_senders: bool = False, **kwargs) -> None:
        """设置消息监听器（适配单通道客户端）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法设置监听器")
            return

        cls._has_listeners = True
        cls._has_senders = has_senders
        logger.info(f"开始设置 {len(listeners)} 个消息监听器")

        for idx, listener_config in enumerate(listeners):
            try:
                # 转换配置并强制设置create_if_not_exists为True
                listener_dict = listener_config.model_dump()
                listener_dict['create_if_not_exists'] = True
                listener_dict['prefetch_count'] = listener_config.prefetch_count
                queue_name = listener_dict['queue_name']

                logger.info(
                    f"设置监听器 {idx+1}/{len(listeners)}: {queue_name} (prefetch_count: {listener_config.prefetch_count})")

                # 添加监听器
                await cls.add_listener(**listener_dict)
            except Exception as e:
                logger.error(
                    f"设置监听器 {idx+1} 失败: {str(e)}", exc_info=True)
                logger.warning("继续处理其他监听器")

        # 启动所有消费者
        await cls.start_all_consumers()

        # 验证消费者启动结果
        await cls._verify_consumers_started()

        logger.info(f"消息监听器设置完成")

    @classmethod
    async def _verify_consumers_started(cls, timeout: int = 30) -> None:
        """验证消费者是否成功启动"""
        start_time = asyncio.get_event_loop().time()
        required_clients = list(cls._message_handlers.keys())
        running_clients = []

        while len(running_clients) < len(required_clients) and \
                (asyncio.get_event_loop().time() - start_time) < timeout and \
                not cls._is_shutdown:

            running_clients = [
                name for name, task in cls._consumer_tasks.items()
                if not task.done() and name in cls._consumer_tags
            ]

            logger.info(
                f"消费者启动验证: {len(running_clients)}/{len(required_clients)} 已启动")
            await asyncio.sleep(1)

        failed_clients = [
            name for name in required_clients if name not in running_clients and not cls._is_shutdown]
        if failed_clients:
            logger.error(f"以下消费者启动失败: {', '.join(failed_clients)}")
            for client_name in failed_clients:
                logger.info(f"尝试重新启动消费者: {client_name}")
                asyncio.create_task(cls.start_consumer(client_name))

    @classmethod
    async def add_listener(
        cls,
        queue_name: str,
        handler: Callable[[MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]], **kwargs
    ) -> None:
        """添加消息监听器（线程安全，单通道场景）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法添加监听器")
            return

        if not cls._config:
            raise ValueError("RabbitMQService尚未初始化，请先调用init方法")

        if queue_name in cls._message_handlers:
            logger.info(f"监听器 '{queue_name}' 已存在，跳过重复添加")
            return

        # 创建并初始化客户端
        await cls.get_client(
            client_name=queue_name,
            queue_name=queue_name,
            **kwargs
        )

        # 注册消息处理器
        cls._message_handlers[queue_name] = handler
        logger.info(f"监听器 '{queue_name}' 已添加")

    @classmethod
    async def start_all_consumers(cls) -> None:
        """启动所有已注册的消费者（单通道场景，避免阻塞）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法启动消费者")
            return

        for client_name in cls._message_handlers:
            await cls.start_consumer(client_name)

    @classmethod
    async def start_consumer(cls, client_name: str) -> None:
        """启动指定客户端的消费者（单通道消费，需确保回调非阻塞）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法启动消费者")
            return

        # 检查任务状态，避免重复创建
        if client_name in cls._consumer_tasks:
            existing_task = cls._consumer_tasks[client_name]
            if not existing_task.done():
                # 检查任务是否处于异常状态，仅在异常时重启
                if existing_task.exception() is not None:
                    logger.info(f"消费者 '{client_name}' 任务异常，重启")
                    existing_task.cancel()
                else:
                    logger.info(f"消费者 '{client_name}' 已在运行中，无需重复启动")
                    return
            else:
                logger.info(f"消费者 '{client_name}' 任务已完成，重新启动")

        if client_name not in cls._clients:
            raise ValueError(f"RabbitMQ客户端 '{client_name}' 未初始化")

        client = cls._clients[client_name]
        handler = cls._message_handlers.get(client_name)

        if not handler:
            logger.warning(f"未找到客户端 '{client_name}' 的处理器，使用默认处理器")
            handler = cls.default_message_handler

        # 设置消息处理器
        await client.set_message_handler(handler)

        # 确保客户端已连接
        start_time = asyncio.get_event_loop().time()
        while not await client.is_connected and not cls._is_shutdown:
            if asyncio.get_event_loop().time() - start_time > cls.CONSUMER_START_TIMEOUT:
                raise TimeoutError(f"等待客户端 '{client_name}' 连接超时")

            logger.info(f"等待客户端 '{client_name}' 连接就绪...")
            await asyncio.sleep(1)
        if cls._is_shutdown:
            return

        # 创建停止事件
        stop_event = asyncio.Event()
        cls._consumer_events[client_name] = stop_event

        # 定义消费任务（单通道场景下，消费回调需非阻塞）
        async def consume_task():
            try:
                # 启动消费，带重试机制
                max_attempts = 3
                attempt = 0
                consumer_tag = None

                while attempt < max_attempts and not stop_event.is_set() and not cls._is_shutdown:
                    try:
                        # 启动消费前再次校验连接和队列状态
                        if not await client.is_connected:
                            logger.info(f"消费者 '{client_name}' 连接断开，尝试重连")
                            await client.connect()

                        # 确保队列和处理器已就绪
                        if not client._queue:
                            raise Exception("队列未初始化完成")
                        if not client._message_handler:
                            raise Exception("消息处理器未设置")

                        consumer_tag = await client.start_consuming()
                        if consumer_tag:
                            break
                    except Exception as e:
                        attempt += 1
                        logger.warning(
                            f"启动消费者尝试 {attempt}/{max_attempts} 失败: {str(e)}")
                        if attempt < max_attempts:
                            await asyncio.sleep(2)

                if cls._is_shutdown:
                    return

                if not consumer_tag:
                    raise Exception(f"经过 {max_attempts} 次尝试仍无法启动消费者")

                # 记录消费者标签
                cls._consumer_tags[client_name] = consumer_tag
                logger.info(
                    f"消费者 '{client_name}' 开始消费（单通道），tag: {consumer_tag}，"
                    f"注意：消费回调需非阻塞，避免影响其他客户端"
                )

                # 等待停止事件
                await stop_event.wait()
                logger.info(f"收到停止信号，消费者 '{client_name}' 准备退出")

            except asyncio.CancelledError:
                logger.info(f"消费者 '{client_name}' 被取消")
            except Exception as e:
                logger.error(
                    f"消费者 '{client_name}' 错误: {str(e)}", exc_info=True)
                # 非主动停止时尝试重启
                if not stop_event.is_set() and not cls._is_shutdown:
                    logger.info(f"尝试重启消费者 '{client_name}'")
                    await asyncio.sleep(cls.RECONNECT_INTERVAL)
                    asyncio.create_task(cls.start_consumer(client_name))
            finally:
                # 清理资源
                try:
                    await client.stop_consuming()
                except Exception as e:
                    logger.error(f"停止消费者 '{client_name}' 时出错: {str(e)}")

                # 移除状态记录
                if client_name in cls._consumer_tags:
                    del cls._consumer_tags[client_name]
                if client_name in cls._consumer_events:
                    del cls._consumer_events[client_name]

                logger.info(f"消费者 '{client_name}' 已停止")

        # 创建并跟踪消费任务
        task = asyncio.create_task(
            consume_task(), name=f"consumer-{client_name}")
        cls._consumer_tasks[client_name] = task

        # 添加任务完成回调
        def task_done_callback(t: asyncio.Task) -> None:
            try:
                if t.done():
                    t.result()
            except Exception as e:
                logger.error(f"消费者任务 '{client_name}' 异常结束: {str(e)}")
                if client_name in cls._message_handlers and not cls._is_shutdown:
                    asyncio.create_task(cls.start_consumer(client_name))

        task.add_done_callback(task_done_callback)
        logger.info(f"消费者任务 '{client_name}' 已创建")

    @classmethod
    async def default_message_handler(cls, parsed_data: MQMsgModel, original_message: AbstractIncomingMessage) -> None:
        """默认消息处理器"""
        logger.info(f"\n===== 收到消息 [{original_message.routing_key}] =====")
        logger.info(f"关联ID: {parsed_data.correlationDataId}")
        logger.info(f"主题代码: {parsed_data.topicCode}")
        logger.info(f"消息内容: {parsed_data.msg}")
        logger.info("===================\n")

    @classmethod
    async def get_sender(cls, queue_name: str) -> Optional[RabbitMQClient]:
        """获取发送客户端（适配单通道池）"""
        if cls._is_shutdown:
            logger.warning("服务已关闭，无法获取发送器")
            return None

        if not queue_name:
            logger.warning("发送器名称不能为空")
            return None

        # 检查是否在已注册的发送器中
        if queue_name in cls._sender_client_names and queue_name in cls._clients:
            client = cls._clients[queue_name]
            if await client.is_connected:
                return client
            else:
                logger.info(f"发送器 '{queue_name}' 连接已断开，尝试重连")
                try:
                    await client.connect()
                    if await client.is_connected:
                        return client
                except Exception as e:
                    logger.error(f"发送器 '{queue_name}' 重连失败: {str(e)}")
            return None

        # 检查是否带有app-name后缀
        app_name = cls._config.get("APP_NAME", "") if cls._config else ""
        if app_name:
            suffixed_name = f"{queue_name}.{app_name}"
            if suffixed_name in cls._sender_client_names and suffixed_name in cls._clients:
                client = cls._clients[suffixed_name]
                if await client.is_connected:
                    return client
                else:
                    logger.info(f"发送器 '{suffixed_name}' 连接已断开，尝试重连")
                    try:
                        await client.connect()
                        if await client.is_connected:
                            return client
                    except Exception as e:
                        logger.error(f"发送器 '{suffixed_name}' 重连失败: {str(e)}")

        logger.info(f"未找到可用的发送器 '{queue_name}'")
        return None

    @classmethod
    async def send_message(
        cls,
        data: Union[BaseModel, str, Dict[str, Any], None],
        queue_name: str, **kwargs
    ) -> None:
        """发送消息到指定队列（单通道场景下快速发送）"""
        if cls._is_shutdown:
            raise RuntimeError("RabbitMQService已关闭，无法发送消息")

        # 获取发送客户端
        sender = await cls.get_sender(queue_name)
        if not sender:
            error_msg = f"未找到可用的RabbitMQ发送器 (queue_name: {queue_name})"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 确保连接有效
        if not await sender.is_connected:
            logger.info(f"发送器 '{queue_name}' 连接已关闭，尝试重新连接")
            max_retry = 3
            retry_count = 0
            last_exception = None

            while retry_count < max_retry and not cls._is_shutdown:
                try:
                    await sender.connect()
                    if await sender.is_connected:
                        logger.info(
                            f"发送器 '{queue_name}' 第 {retry_count + 1} 次重连成功")
                        break
                except Exception as e:
                    last_exception = e
                    retry_count += 1
                    logger.warning(
                        f"发送器 '{queue_name}' 第 {retry_count} 次重连失败: {str(e)}")
                    await asyncio.sleep(cls.RECONNECT_INTERVAL)

            if retry_count >= max_retry and not await sender.is_connected:
                error_msg = f"发送器 '{queue_name}' 经过 {max_retry} 次重连仍失败"
                logger.error(f"{error_msg}: {str(last_exception)}")
                raise Exception(error_msg) from last_exception

        try:
            # 处理消息数据
            msg_content = ""
            if isinstance(data, str):
                msg_content = data
            elif isinstance(data, BaseModel):
                msg_content = data.model_dump_json()
            elif isinstance(data, dict):
                msg_content = json.dumps(data, ensure_ascii=False)

            # 创建标准消息模型
            mq_message = MQMsgModel(
                topicCode=queue_name.split('.')[0] if queue_name else "",
                msg=msg_content,
                correlationDataId=kwargs.get(
                    'correlationDataId', logger.get_trace_id()),
                groupId=kwargs.get('groupId', ''),
                dataKey=kwargs.get('dataKey', ""),
                manualFlag=kwargs.get('manualFlag', False),
                traceId=logger.get_trace_id()
            )

            # 构建消息头
            mq_header = {
                "context": SsoUser(
                    tenant_id="T000002",
                    customer_id="SYSTEM",
                    user_id="SYSTEM",
                    user_name="SYSTEM",
                    request_path="",
                    req_type="SYSTEM",
                    trace_id=logger.get_trace_id(),
                ).model_dump_json()
            }

            # 发送消息（单通道场景下依赖原生异步确认）
            await sender.publish(
                message_body=mq_message.model_dump_json(),
                headers=mq_header,
                content_type="application/json"
            )
            logger.info(f"消息发送成功 (队列: {queue_name})")
        except Exception as e:
            logger.error(f"消息发送失败: {str(e)}", exc_info=True)
            raise

    @classmethod
    async def shutdown(cls, timeout: float = 15.0) -> None:
        """优雅关闭所有资源（单通道场景下简化关闭流程）"""
        async with cls._shutdown_lock:
            if cls._is_shutdown:
                logger.info("RabbitMQService已关闭，无需重复操作")
                return

            cls._is_shutdown = True
            logger.info("开始关闭RabbitMQ服务...")

            # 1. 停止连接监控任务
            if cls._connection_monitor_task and not cls._connection_monitor_task.done():
                cls._connection_monitor_task.cancel()
                try:
                    await asyncio.wait_for(cls._connection_monitor_task, timeout=timeout)
                except asyncio.TimeoutError:
                    logger.warning("连接监控任务关闭超时")
                except Exception as e:
                    logger.error(f"关闭连接监控任务失败: {str(e)}")

            # 2. 停止所有消费者任务
            for client_name, task in cls._consumer_tasks.items():
                if not task.done():
                    # 触发停止事件
                    if client_name in cls._consumer_events:
                        cls._consumer_events[client_name].set()
                    # 取消任务
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=timeout)
                    except Exception as e:
                        logger.error(f"关闭消费者 '{client_name}' 失败: {str(e)}")

            # 3. 关闭所有客户端（单通道场景下客户端关闭仅清理状态）
            for client in cls._clients.values():
                try:
                    await client.close()
                except Exception as e:
                    logger.error(f"关闭客户端失败: {str(e)}")

            # 4. 关闭连接池（单通道池关闭会释放所有资源）
            if cls._connection_pool and cls._connection_pool._initialized:
                try:
                    await cls._connection_pool.close()
                    logger.info("RabbitMQ单通道连接池已关闭")
                except Exception as e:
                    logger.error(f"关闭连接池失败: {str(e)}")

            # 5. 清理状态
            cls._clients.clear()
            cls._message_handlers.clear()
            cls._consumer_tasks.clear()
            cls._consumer_events.clear()
            cls._consumer_tags.clear()
            cls._sender_client_names.clear()
            cls._init_locks.clear()
            cls._config = None

            logger.info("RabbitMQService已完全关闭")
