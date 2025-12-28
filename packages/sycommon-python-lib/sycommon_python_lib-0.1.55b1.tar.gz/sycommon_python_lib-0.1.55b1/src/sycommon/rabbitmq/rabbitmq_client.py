from aio_pika import Channel
from typing import Optional
import asyncio
import json
from typing import Callable, Coroutine, Dict, Any, Union
from aio_pika import Message, DeliveryMode, ExchangeType
from aio_pika.abc import (
    AbstractExchange,
    AbstractQueue,
    AbstractIncomingMessage,
    ConsumerTag,
    AbstractRobustConnection,
)
from sycommon.rabbitmq.rabbitmq_pool import RabbitMQConnectionPool
from sycommon.logging.kafka_log import SYLogger
from sycommon.models.mqmsg_model import MQMsgModel

logger = SYLogger


class RabbitMQClient:
    """
    RabbitMQ 客户端（支持消息发布、消费、自动重连、异常重试）
    核心特性：
    1. 基于单通道连接池复用资源，性能优化
    2. 依赖连接池原生自动重连，客户端仅重建自身资源
    3. 消息发布支持重试+mandatory机制+超时控制，确保路由有效
    4. 消费支持手动ACK/NACK
    5. 兼容JSON/字符串/字典消息格式
    """

    def __init__(
        self,
        connection_pool: RabbitMQConnectionPool,
        exchange_name: str = "system.topic.exchange",
        exchange_type: str = "topic",
        queue_name: Optional[str] = None,
        routing_key: str = "#",
        durable: bool = True,
        auto_delete: bool = False,
        auto_parse_json: bool = True,
        create_if_not_exists: bool = True,
        **kwargs,
    ):
        # 依赖注入：连接池（必须已初始化）
        self.connection_pool = connection_pool
        if not self.connection_pool._initialized:
            raise RuntimeError("连接池未初始化，请先调用 connection_pool.init_pools()")

        # 交换机配置
        self.exchange_name = exchange_name.strip()
        try:
            self.exchange_type = ExchangeType(exchange_type.lower())
        except ValueError:
            logger.warning(f"无效的exchange_type: {exchange_type}，默认使用'topic'")
            self.exchange_type = ExchangeType.TOPIC

        # 队列配置
        self.queue_name = queue_name.strip() if queue_name else None
        self.routing_key = routing_key.strip() if routing_key else "#"
        self.durable = durable  # 消息/队列持久化
        self.auto_delete = auto_delete  # 无消费者时自动删除队列/交换机
        self.auto_parse_json = auto_parse_json  # 自动解析JSON消息体
        self.create_if_not_exists = create_if_not_exists  # 不存在则创建交换机/队列

        # 内部状态（资源+连接）
        self._channel: Optional[Channel] = None
        self._channel_conn: Optional[AbstractRobustConnection] = None  # 通道所属连接
        self._exchange: Optional[AbstractExchange] = None
        self._queue: Optional[AbstractQueue] = None
        self._consumer_tag: Optional[ConsumerTag] = None
        self._message_handler: Optional[Callable[[
            MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]]] = None
        self._closed = False

        # 线程安全锁
        self._consume_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        # 跟踪连接关闭回调（用于后续移除）
        self._conn_close_callback: Optional[Callable] = None
        # 控制重连频率的信号量（限制并发重连数）
        self._reconnect_semaphore = asyncio.Semaphore(1)
        # 固定重连间隔15秒（全局统一）
        self._RECONNECT_INTERVAL = 15
        # 跟踪当前重连任务（避免重复创建）
        self._current_reconnect_task: Optional[asyncio.Task] = None
        # 连接失败计数器（用于告警）
        self._reconnect_fail_count = 0
        # 连接失败告警阈值
        self._reconnect_alert_threshold = 5

    @property
    async def is_connected(self) -> bool:
        """异步检查客户端连接状态（属性，不可调用）"""
        if self._closed:
            return False
        try:
            # 单通道场景：校验通道+连接+核心资源都有效
            return (
                self._channel and not self._channel.is_closed
                and self._channel_conn and not self._channel_conn.is_closed
                and self._exchange is not None
                and (not self.queue_name or self._queue is not None)
            )
        except Exception as e:
            logger.warning(f"检查连接状态失败: {str(e)}")
            return False

    async def _rebuild_resources(self) -> None:
        """重建交换机/队列等资源（依赖已有的通道）"""
        if not self._channel or self._channel.is_closed:
            raise RuntimeError("无有效通道，无法重建资源")

        # 1. 声明交换机
        self._exchange = await self._channel.declare_exchange(
            name=self.exchange_name,
            type=self.exchange_type,
            durable=self.durable,
            auto_delete=self.auto_delete,
            passive=not self.create_if_not_exists,
        )
        logger.info(
            f"交换机重建成功: {self.exchange_name}（类型: {self.exchange_type.value}）")

        # 2. 声明队列（如果配置了队列名）
        if self.queue_name:
            self._queue = await self._channel.declare_queue(
                name=self.queue_name,
                durable=self.durable,
                auto_delete=self.auto_delete,
                passive=not self.create_if_not_exists,
            )
            # 绑定队列到交换机
            await self._queue.bind(
                exchange=self._exchange,
                routing_key=self.routing_key,
            )
            logger.info(
                f"队列重建成功: {self.queue_name} "
                f"（绑定交换机: {self.exchange_name}, routing_key: {self.routing_key}）"
            )

    async def connect(self) -> None:
        if self._closed:
            raise RuntimeError("客户端已关闭，无法重新连接")

        async with self._connect_lock:
            # 释放旧资源（回调+通道，单通道无需归还，仅清理状态）
            if self._conn_close_callback and self._channel_conn:
                self._channel_conn.close_callbacks.discard(
                    self._conn_close_callback)
            self._channel = None
            self._channel_conn = None
            self._exchange = None
            self._queue = None
            self._conn_close_callback = None

            try:
                # 从单通道池获取通道+连接（连接池自动确保通道有效）
                self._channel, self._channel_conn = await self.connection_pool.acquire_channel()

                def on_conn_closed(conn: AbstractRobustConnection, exc: Optional[BaseException]):
                    """连接关闭回调：触发固定间隔重连"""
                    logger.warning(
                        f"客户端连接关闭: {conn!r}，原因: {exc}", exc_info=exc)
                    self._reconnect_fail_count += 1
                    # 超过阈值告警
                    if self._reconnect_fail_count >= self._reconnect_alert_threshold:
                        logger.error(
                            f"连接失败次数已达阈值({self._reconnect_alert_threshold})，请检查MQ服务状态")
                    if not self._closed:
                        asyncio.create_task(self._safe_reconnect())

                self._conn_close_callback = on_conn_closed
                if self._channel_conn:
                    self._channel_conn.close_callbacks.add(
                        self._conn_close_callback)

                # 重建交换机/队列资源
                await self._rebuild_resources()

                # 重连成功，重置失败计数器
                self._reconnect_fail_count = 0
                logger.info("客户端连接初始化完成")
            except Exception as e:
                logger.error(f"客户端连接失败: {str(e)}", exc_info=True)
                # 清理异常状态
                if self._conn_close_callback and self._channel_conn:
                    self._channel_conn.close_callbacks.discard(
                        self._conn_close_callback)
                self._channel = None
                self._channel_conn = None
                # 触发重连
                if not self._closed:
                    asyncio.create_task(self._safe_reconnect())
                raise

    async def _safe_reconnect(self):
        """安全重连：信号量控制并发+固定15秒间隔"""
        async with self._reconnect_semaphore:
            # 检查是否已有重连任务在运行
            if self._current_reconnect_task and not self._current_reconnect_task.done():
                logger.debug("已有重连任务在运行，跳过重复触发")
                return

            if self._closed or await self.is_connected:
                logger.debug("客户端已关闭或已连接，取消重连")
                return

            # 固定15秒重连间隔
            logger.info(f"将在{self._RECONNECT_INTERVAL}秒后尝试重连...")
            await asyncio.sleep(self._RECONNECT_INTERVAL)

            if self._closed or await self.is_connected:
                logger.debug("重连等待期间客户端状态变化，取消重连")
                return

            try:
                logger.info("开始重连RabbitMQ客户端...")
                self._current_reconnect_task = asyncio.create_task(
                    self.connect())
                await self._current_reconnect_task
            except Exception as e:
                logger.warning(f"重连失败: {str(e)}")
            finally:
                self._current_reconnect_task = None

    async def set_message_handler(
        self,
        handler: Callable[[MQMsgModel, AbstractIncomingMessage], Coroutine[Any, Any, None]],
    ) -> None:
        """设置消息处理器（必须是协程函数）"""
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError("消息处理器必须是协程函数（使用 async def 定义）")

        async with self._consume_lock:
            self._message_handler = handler
            logger.info("消息处理器设置成功")

    async def start_consuming(self) -> Optional[ConsumerTag]:
        """启动消息消费（支持自动重连）"""
        if self._closed:
            raise RuntimeError("客户端已关闭，无法启动消费")

        async with self._consume_lock:
            # 1. 校验前置条件
            if not self._message_handler:
                raise RuntimeError("未设置消息处理器，请先调用 set_message_handler()")
            if not await self.is_connected:
                await self.connect()
            if not self._queue:
                raise RuntimeError("未配置队列名或队列未创建，无法启动消费")

            # 2. 定义消费回调（包含异常处理和重连逻辑）
            async def consume_callback(message: AbstractIncomingMessage):
                try:
                    # 解析消息体
                    if self.auto_parse_json:
                        try:
                            body_dict = json.loads(
                                message.body.decode("utf-8"))
                            msg_obj = MQMsgModel(**body_dict)
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"JSON消息解析失败: {str(e)}，消息体: {message.body[:100]}...")
                            await message.nack(requeue=False)  # 解析失败，不重入队
                            return
                    else:
                        msg_obj = MQMsgModel(
                            body=message.body.decode("utf-8"),
                            routing_key=message.routing_key,
                            delivery_tag=message.delivery_tag,
                        )

                    # 调用消息处理器
                    await self._message_handler(msg_obj, message)

                    # 手动ACK
                    await message.ack()
                    logger.debug(
                        f"消息处理成功，delivery_tag: {message.delivery_tag}")

                except Exception as e:
                    logger.error(
                        f"消息处理失败，delivery_tag: {message.delivery_tag}",
                        exc_info=True
                    )
                    # 处理失败逻辑：首次失败重入队，再次失败丢弃
                    if message.redelivered:
                        logger.warning(
                            f"消息已重入队过，本次拒绝入队: {message.delivery_tag}")
                        await message.reject(requeue=False)
                    else:
                        logger.warning(f"消息重入队: {message.delivery_tag}")
                        await message.nack(requeue=True)

                    # 连接失效则触发重连
                    if not await self.is_connected:
                        logger.warning("连接已失效，触发客户端重连")
                        asyncio.create_task(self._safe_reconnect())

            # 3. 启动消费（单通道消费，避免阻塞发布需确保业务回调非阻塞）
            self._consumer_tag = await self._queue.consume(consume_callback)
            logger.info(
                f"开始消费队列: {self._queue.name}，consumer_tag: {self._consumer_tag}"
            )
            return self._consumer_tag

    async def stop_consuming(self) -> None:
        """停止消息消费（适配 RobustChannel）"""
        async with self._consume_lock:
            try:
                # 校验核心条件：消费标签、队列、通道均有效
                if self._consumer_tag and self._queue and self._channel and not self._channel.is_closed:
                    # 使用队列的 cancel 方法（适配 RobustChannel）
                    await self._queue.cancel(self._consumer_tag)
                    logger.info(
                        f"停止消费成功，consumer_tag: {self._consumer_tag}，队列: {self._queue.name}"
                    )
                elif self._consumer_tag:
                    # 部分资源无效时的日志提示
                    if not self._queue:
                        logger.warning(
                            f"消费标签存在但队列为空，无法取消消费（consumer_tag: {self._consumer_tag}）")
                    elif not self._channel or self._channel.is_closed:
                        logger.warning(
                            f"通道已关闭，消费已自动停止（consumer_tag: {self._consumer_tag}，队列: {self._queue.name if self._queue else '未知'}）"
                        )
            except Exception as e:
                logger.error(
                    f"停止消费者 '{self._queue.name if self._queue else '未知队列'}' 时出错: {str(e)}", exc_info=True
                )
            finally:
                self._consumer_tag = None  # 无论成败，清理消费标签

    async def publish(
        self,
        message_body: Union[str, Dict[str, Any], MQMsgModel],
        headers: Optional[Dict[str, Any]] = None,
        content_type: str = "application/json",
        delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT,
        retry_count: int = 3,
    ) -> None:
        """
        发布消息（支持自动重试、mandatory路由校验、5秒超时控制）
        :param message_body: 消息体（字符串/字典/MQMsgModel）
        :param headers: 消息头（可选）
        :param content_type: 内容类型（默认application/json）
        :param delivery_mode: 投递模式（PERSISTENT=持久化，TRANSIENT=非持久化）
        :param retry_count: 重试次数（默认3次）
        """
        if self._closed:
            raise RuntimeError("客户端已关闭，无法发布消息")

        # 处理消息体序列化
        try:
            if isinstance(message_body, MQMsgModel):
                body = json.dumps(message_body.to_dict(),
                                  ensure_ascii=False).encode("utf-8")
            elif isinstance(message_body, dict):
                body = json.dumps(
                    message_body, ensure_ascii=False).encode("utf-8")
            elif isinstance(message_body, str):
                body = message_body.encode("utf-8")
            else:
                raise TypeError(f"不支持的消息体类型: {type(message_body)}")
        except Exception as e:
            logger.error(f"消息体序列化失败: {str(e)}", exc_info=True)
            raise

        # 构建消息对象
        message = Message(
            body=body,
            headers=headers or {},
            content_type=content_type,
            delivery_mode=delivery_mode,
        )

        # 发布重试逻辑
        for retry in range(retry_count):
            try:
                # 确保连接有效
                if not await self.is_connected:
                    logger.warning(f"发布消息前连接失效，触发重连（retry: {retry}）")
                    await self.connect()

                # 核心：发布消息（mandatory=True 确保路由有效，timeout=5s 避免阻塞）
                publish_result = await self._exchange.publish(
                    message=message,
                    routing_key=self.routing_key or self.queue_name or "#",
                    mandatory=True,
                    timeout=5.0
                )

                # 处理 mandatory 未路由场景
                if publish_result is None:
                    raise RuntimeError(
                        f"消息未找到匹配的队列（routing_key: {self.routing_key}），mandatory=True 触发失败"
                    )

                logger.info(
                    f"消息发布成功（retry: {retry}），routing_key: {self.routing_key}，"
                    f"delivery_mode: {delivery_mode.value}，mandatory: True，timeout: 5.0s"
                )
                return
            except asyncio.TimeoutError:
                logger.error(
                    f"消息发布超时（retry: {retry}/{retry_count-1}），超时时间: 5.0s"
                )
            except RuntimeError as e:
                logger.error(
                    f"消息发布业务失败（retry: {retry}/{retry_count-1}）: {str(e)}"
                )
            except Exception as e:
                logger.error(
                    f"消息发布失败（retry: {retry}/{retry_count-1}）: {str(e)}",
                    exc_info=True
                )
                # 清理失效状态，下次重试重连
                self._exchange = None
            # 指数退避重试间隔
            await asyncio.sleep(0.5 * (2 ** retry))

        # 所有重试失败
        raise RuntimeError(
            f"消息发布失败（已重试{retry_count}次），routing_key: {self.routing_key}，"
            f"mandatory: True，timeout: 5.0s"
        )

    async def close(self) -> None:
        """关闭客户端（移除回调+释放资源）"""
        self._closed = True
        logger.info("开始关闭RabbitMQ客户端...")

        # 停止重连任务
        if self._current_reconnect_task and not self._current_reconnect_task.done():
            self._current_reconnect_task.cancel()
            try:
                await self._current_reconnect_task
            except asyncio.CancelledError:
                logger.debug("重连任务已取消")

        # 1. 停止消费
        await self.stop_consuming()

        # 2. 清理回调+状态（单通道无需归还，连接池统一管理）
        async with self._connect_lock:
            if self._conn_close_callback and self._channel_conn:
                self._channel_conn.close_callbacks.discard(
                    self._conn_close_callback)
            self._channel = None
            self._channel_conn = None
            self._exchange = None
            self._queue = None
            self._message_handler = None

        logger.info("RabbitMQ客户端已完全关闭")
