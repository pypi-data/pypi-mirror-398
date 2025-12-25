import asyncio
import random
from typing import Optional, List, Dict, Callable, Tuple
from aio_pika import connect_robust, RobustChannel, Message
from aio_pika.abc import (
    AbstractRobustConnection, AbstractQueue, AbstractExchange, AbstractMessage
)
from aio_pika.exceptions import ChannelClosed
import aiormq.exceptions

from sycommon.logging.kafka_log import SYLogger

logger = SYLogger


class RabbitMQConnectionPool:
    """单连接单通道RabbitMQ客户端（核心特性：依赖connect_robust原生自动重连/恢复 + 仅关闭时释放资源）"""

    def __init__(
        self,
        hosts: List[str],
        port: int,
        username: str,
        password: str,
        virtualhost: str = "/",
        heartbeat: int = 30,
        app_name: str = "",
        connection_timeout: int = 30,
        reconnect_interval: int = 5,
        prefetch_count: int = 2,
    ):
        # 基础配置校验与初始化
        self.hosts = [host.strip() for host in hosts if host.strip()]
        if not self.hosts:
            raise ValueError("至少需要提供一个RabbitMQ主机地址")

        self.port = port
        self.username = username
        self.password = password
        self.virtualhost = virtualhost
        self.app_name = app_name or "rabbitmq-client"
        self.heartbeat = heartbeat
        self.connection_timeout = connection_timeout
        self.reconnect_interval = reconnect_interval
        self.prefetch_count = prefetch_count

        # 初始化时随机选择一个主机地址（固定使用，依赖原生重连）
        self._current_host: str = random.choice(self.hosts)
        logger.info(
            f"随机选择RabbitMQ主机: {self._current_host}（依赖connect_robust原生自动重连/恢复）")

        # 核心资源（单连接+单通道，基于原生自动重连）
        self._connection: Optional[AbstractRobustConnection] = None  # 原生自动重连连接
        self._channel: Optional[RobustChannel] = None  # 单通道（原生自动恢复）
        # 消费者通道跟踪（独立于主通道）
        self._consumer_channels: Dict[str,
                                      Tuple[RobustChannel, Callable, bool, dict]] = {}

        # 状态控制（并发安全+生命周期管理）
        self._lock = asyncio.Lock()
        self._initialized = False
        self._is_shutdown = False

    async def _is_connection_valid(self) -> bool:
        """原子化检查连接有效性（所有状态判断均加锁，确保原子性）"""
        async with self._lock:
            # 优先级：先判断是否关闭，再判断是否初始化，最后判断连接状态
            return not self._is_shutdown and self._initialized and self._connection is not None and not self._connection.is_closed

    @property
    async def is_alive(self) -> bool:
        """对外暴露的连接存活状态（原子化判断）"""
        async with self._lock:
            if self._is_shutdown:
                return False
            # 存活条件：未关闭 + 已初始化 + 连接有效 + 主通道有效
            return self._initialized and self._connection is not None and not self._connection.is_closed and self._channel is not None and not self._channel.is_closed

    async def _create_connection(self) -> AbstractRobustConnection:
        """创建原生自动重连连接（仅创建一次，内部自动重试）"""
        async with self._lock:
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭，无法创建连接")

        conn_url = f"amqp://{self.username}:{self.password}@{self._current_host}:{self.port}/{self.virtualhost}?name={self.app_name}&heartbeat={self.heartbeat}&reconnect_interval={self.reconnect_interval}&fail_fast=1"
        logger.info(f"尝试创建原生自动重连连接: {self._current_host}:{self.port}")

        try:
            conn = await connect_robust(
                conn_url,
                timeout=self.connection_timeout,
            )
            logger.info(f"连接创建成功: {self._current_host}:{self.port}（原生自动重连已启用）")
            return conn
        except Exception as e:
            logger.error(f"连接创建失败: {str(e)}", exc_info=True)
            raise ConnectionError(
                f"无法连接RabbitMQ主机 {self._current_host}:{self.port}") from e

    async def _init_single_channel(self):
        """初始化单通道（通道自带原生自动恢复）"""
        async with self._lock:
            # 先判断是否关闭（优先级最高）
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭，无法初始化通道")
            # 再判断连接是否有效
            if not self._connection or self._connection.is_closed:
                raise RuntimeError("无有效连接，无法初始化通道")

            # 清理旧通道（如果存在）
            if self._channel and not self._channel.is_closed:
                await self._channel.close()

            # 创建单通道并设置QOS
            try:
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=self.prefetch_count)
                logger.info(f"单通道初始化完成（带原生自动恢复）")
            except Exception as e:
                logger.error(f"创建单通道失败: {str(e)}", exc_info=True)
                raise

    async def _check_and_recover_channel(self) -> RobustChannel:
        """检查并恢复通道（确保通道有效，所有状态判断加锁）"""
        async with self._lock:
            # 1. 先判断是否关闭（优先级最高）
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭，无法获取通道")
            # 2. 检查连接状态
            if not self._connection or self._connection.is_closed:
                raise RuntimeError("连接已关闭（等待原生重连）")
            # 3. 通道失效时重新创建
            if not self._channel or self._channel.is_closed:
                logger.warning("通道失效，重新创建（依赖原生自动恢复）")
                await self._init_single_channel()

            return self._channel

    async def init_pools(self):
        """初始化客户端（仅执行一次）"""
        async with self._lock:
            # 原子化判断：是否已关闭/已初始化
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭，无法初始化")
            if self._initialized:
                logger.warning("客户端已初始化，无需重复调用")
                return

        try:
            # 1. 创建原生自动重连连接
            self._connection = await self._create_connection()

            # 2. 初始化单通道
            await self._init_single_channel()

            # 3. 标记为已初始化（加锁保护）
            async with self._lock:
                self._initialized = True

            logger.info("RabbitMQ单通道客户端初始化完成（原生自动重连/恢复已启用）")
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            await self.close()  # 初始化失败直接关闭
            raise

    async def acquire_channel(self) -> Tuple[RobustChannel, AbstractRobustConnection]:
        """获取单通道（返回 (通道, 连接) 元组，保持API兼容）"""
        async with self._lock:
            # 原子化状态校验
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭，无法获取通道")
            if not self._initialized:
                raise RuntimeError("客户端未初始化，请先调用init_pools()")

        # 检查并恢复通道
        channel = await self._check_and_recover_channel()
        return channel, self._connection  # 单通道无需管理"使用中/空闲"状态

    async def declare_queue(self, queue_name: str, **kwargs) -> AbstractQueue:
        """声明队列（使用单通道）"""
        channel, _ = await self.acquire_channel()
        return await channel.declare_queue(queue_name, **kwargs)

    async def declare_exchange(self, exchange_name: str, exchange_type: str = "direct", **kwargs) -> AbstractExchange:
        """声明交换机（使用单通道）"""
        channel, _ = await self.acquire_channel()
        return await channel.declare_exchange(exchange_name, exchange_type, **kwargs)

    async def publish_message(self, routing_key: str, message_body: bytes, exchange_name: str = "", **kwargs):
        """发布消息（依赖原生自动重连/恢复）"""
        channel, _ = await self.acquire_channel()
        try:
            exchange = channel.default_exchange if not exchange_name else await channel.get_exchange(exchange_name)
            message = Message(body=message_body, **kwargs)
            await exchange.publish(message, routing_key=routing_key)
            logger.debug(
                f"消息发布成功 - 交换机: {exchange.name}, 路由键: {routing_key}"
            )
        except Exception as e:
            logger.error(f"发布消息失败: {str(e)}", exc_info=True)
            raise  # 原生会自动重连，无需手动处理

    async def consume_queue(self, queue_name: str, callback: Callable[[AbstractMessage], asyncio.Future], auto_ack: bool = False, **kwargs):
        """消费队列（独立通道，带原生自动恢复）"""
        async with self._lock:
            # 原子化状态校验
            if self._is_shutdown:
                raise RuntimeError("客户端已关闭，无法启动消费")
            if not self._initialized:
                raise RuntimeError("客户端未初始化，请先调用init_pools()")
            if queue_name in self._consumer_channels:
                logger.warning(f"队列 {queue_name} 已在消费中，无需重复启动")
                return

        # 先声明队列（确保队列存在）
        await self.declare_queue(queue_name, **kwargs)

        # 创建独立的消费者通道（不使用主单通道，避免消费阻塞发布）
        async with self._lock:
            if self._is_shutdown:  # 二次校验：防止创建通道前客户端被关闭
                raise RuntimeError("客户端已关闭，无法创建消费者通道")
            if not self._connection or self._connection.is_closed:
                raise RuntimeError("无有效连接，无法创建消费者通道")
            channel = await self._connection.channel()
            await channel.set_qos(prefetch_count=self.prefetch_count)

            # 注册消费者通道
            self._consumer_channels[queue_name] = (
                channel, callback, auto_ack, kwargs)

        async def consume_callback_wrapper(message: AbstractMessage):
            """消费回调包装（处理通道失效，依赖原生恢复）"""
            try:
                async with self._lock:
                    # 原子化校验状态：客户端是否关闭 + 通道是否有效 + 连接是否有效
                    if self._is_shutdown:
                        logger.warning(f"客户端已关闭，拒绝处理消息（队列: {queue_name}）")
                        if not auto_ack:
                            await message.nack(requeue=True)
                        return
                    channel_valid = not channel.is_closed
                    conn_valid = self._connection and not self._connection.is_closed

                if not channel_valid or not conn_valid:
                    logger.warning(f"消费者通道 {queue_name} 失效（等待原生自动恢复）")
                    if not auto_ack:
                        await message.nack(requeue=True)
                    return

                # 执行业务回调
                await callback(message)
                if not auto_ack:
                    await message.ack()
            except ChannelClosed as e:
                logger.error(f"消费者通道 {queue_name} 关闭: {str(e)}", exc_info=True)
                if not auto_ack:
                    await message.nack(requeue=True)
            except aiormq.exceptions.ChannelInvalidStateError as e:
                logger.error(
                    f"消费者通道 {queue_name} 状态异常: {str(e)}", exc_info=True)
                if not auto_ack:
                    await message.nack(requeue=True)
            except Exception as e:
                logger.error(
                    f"消费消息失败（队列: {queue_name}）: {str(e)}", exc_info=True)
                if not auto_ack:
                    await message.nack(requeue=True)

        logger.info(f"开始消费队列: {queue_name}（通道带原生自动恢复）")

        try:
            await channel.basic_consume(
                queue_name,
                consumer_callback=consume_callback_wrapper,
                auto_ack=auto_ack,
                **kwargs
            )
        except Exception as e:
            logger.error(f"启动消费失败（队列: {queue_name}）: {str(e)}", exc_info=True)
            # 清理异常资源
            try:
                async with self._lock:
                    if not channel.is_closed:
                        await channel.close()
                    # 移除无效的消费者通道注册
                    if queue_name in self._consumer_channels:
                        del self._consumer_channels[queue_name]
            except Exception as close_e:
                logger.warning(f"关闭消费者通道失败: {str(close_e)}")
            raise

    async def close(self):
        """关闭客户端（释放所有资源，原子化状态管理）"""
        async with self._lock:
            if self._is_shutdown:
                logger.warning("客户端已关闭，无需重复操作")
                return
            # 先标记为关闭，阻止后续所有操作（原子化修改）
            self._is_shutdown = True
            self._initialized = False

        logger.info("开始关闭RabbitMQ单通道客户端（释放所有资源）...")

        # 1. 关闭所有消费者通道
        consumer_channels = []
        async with self._lock:
            consumer_channels = list(self._consumer_channels.values())
            self._consumer_channels.clear()
        for channel, _, _, _ in consumer_channels:
            try:
                if not channel.is_closed:
                    await channel.close()
            except Exception as e:
                logger.warning(f"关闭消费者通道失败: {str(e)}")

        # 2. 关闭主单通道
        if self._channel:
            try:
                async with self._lock:
                    if not self._channel.is_closed:
                        await self._channel.close()
            except Exception as e:
                logger.warning(f"关闭主通道失败: {str(e)}")
            self._channel = None

        # 3. 关闭连接（终止原生自动重连）
        if self._connection:
            try:
                async with self._lock:
                    if not self._connection.is_closed:
                        await self._connection.close()
                logger.info(
                    f"已关闭连接: {self._current_host}:{self.port}（终止原生自动重连）")
            except Exception as e:
                logger.warning(f"关闭连接失败: {str(e)}")
            self._connection = None

        logger.info("RabbitMQ单通道客户端已完全关闭")
