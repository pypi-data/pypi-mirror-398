import logging
import threading
import json
from typing import Callable, Dict, List, Optional
import nacos
import socket
import signal
import sys
import os
import yaml
import time
import atexit
import random

from sycommon.config.Config import SingletonMeta
from sycommon.logging.kafka_log import SYLogger

logging.getLogger("nacos.client").setLevel(logging.WARNING)


class NacosService(metaclass=SingletonMeta):
    def __init__(self, config):
        if config:
            self.config = config
            self.nacos_config = config['Nacos']
            self.service_name = config['Name']
            self.host = config['Host']
            self.port = config['Port']
            self.version = os.getenv('VERSION')
            self.enable_register_nacos = os.getenv(
                'REGISTER-NACOS', 'true').lower() == 'true'
            self.registered = False
            self._client_initialized = False  # 客户端初始化状态
            self._shutdown_event = threading.Event()

            # 添加可重入锁用于状态同步
            self._state_lock = threading.RLock()

            # 配置参数
            self.max_retries = self.nacos_config.get('maxRetries', 5)
            self.retry_delay = self.nacos_config.get('retryDelay', 5)
            self.max_retry_delay = self.nacos_config.get('maxRetryDelay', 30)
            # 心跳间隔：优先从配置读取，默认15秒（可通过配置修改）
            self.heartbeat_interval = self.nacos_config.get(
                'heartbeatInterval', 15)
            # 心跳超时：固定设置为10秒（需求指定）
            self.heartbeat_timeout = 15
            self.register_retry_interval = self.nacos_config.get(
                'registerRetryInterval', 15)  # 注册重试间隔

            # 长期重试配置
            self.long_term_retry_delay = self.nacos_config.get(
                'longTermRetryDelay', 30)
            self.max_long_term_retries = self.nacos_config.get(
                'maxLongTermRetries', -1)  # -1表示无限重试

            # 注册验证配置：优化默认值（增加次数+延长间隔）
            self.registration_verify_count = self.nacos_config.get(
                'registrationVerifyCount', 1)  # 验证次数
            self.registration_verify_interval = self.nacos_config.get(
                'registrationVerifyInterval', 1)  # 验证间隔
            self.registration_post_delay = self.nacos_config.get(
                'registrationPostDelay', 3)  # 注册后延迟3秒再开始验证

            self.real_ip = self.get_service_ip(self.host)
            self._long_term_retry_count = 0  # 长期重试计数器

            # 轮询索引，用于在所有实例中进行轮询选择
            self._round_robin_index = 0
            self._round_robin_lock = threading.Lock()  # 保护轮询索引的线程安全

            if self.enable_register_nacos:
                # 初始化客户端（仅在首次调用时执行）
                self._initialize_client()
                # 启动时清理残留实例
                self._cleanup_stale_instance()
            else:
                SYLogger.info("nacos:本地开发模式，不初始化Nacos客户端")

            self.share_configs = self.read_configs()

            # 配置监听器
            self._config_listeners = {}
            self._config_cache = {}

            # 心跳相关
            self._last_heartbeat_time = 0
            self._heartbeat_fail_count = 0
            self._heartbeat_lock = threading.Lock()
            self._heartbeat_thread = None

            self.max_heartbeat_timeout = self.nacos_config.get(
                'maxHeartbeatTimeout', 30)
            self._last_successful_heartbeat = time.time()
            # 连接监控检查间隔（新增配置，默认30秒，避免硬编码）
            self.connection_check_interval = self.nacos_config.get(
                'connectionCheckInterval', 30)
            # 配置监视线程检查间隔（默认30秒）
            self.config_watch_interval = self.nacos_config.get(
                'configWatchInterval', 30)

            # 启动配置监视线程
            self._watch_thread = threading.Thread(
                target=self._watch_configs, daemon=True)
            self._watch_thread.start()

            # 仅在需要注册时启动心跳和监控线程
            if self.enable_register_nacos:
                # 启动心跳线程
                self.start_heartbeat()
            else:
                SYLogger.info("nacos:本地开发模式，不启动心跳和监控线程")

    def _initialize_client(self):
        """初始化Nacos客户端（仅首次调用时执行）"""
        if self._client_initialized:
            return True

        for attempt in range(self.max_retries):
            try:
                register_ip = self.nacos_config['registerIp']
                namespace_id = self.nacos_config['namespaceId']
                self.nacos_client = nacos.NacosClient(
                    server_addresses=register_ip,
                    namespace=namespace_id
                )
                SYLogger.info("nacos:客户端初始化成功")
                self._client_initialized = True
                return True
            except Exception as e:
                delay = min(self.retry_delay, self.max_retry_delay)
                SYLogger.error(
                    f"nacos:客户端初始化失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                time.sleep(delay)

        SYLogger.warning("nacos:无法连接到 Nacos 服务器，已达到最大重试次数")
        return False

    def _cleanup_stale_instance(self):
        """清理可能存在的残留实例"""
        if not self._client_initialized:
            return

        try:
            self.nacos_client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.real_ip,
                port=int(self.port),
                cluster_name="DEFAULT"
            )
            SYLogger.warning(f"nacos:清理残留实例: {self.real_ip}:{self.port}")
        except Exception as e:
            SYLogger.error(f"nacos:清理残留实例异常: {e}")

    def ensure_client_connected(self, retry_once=False):
        """确保Nacos客户端已连接，返回连接状态"""
        # 使用线程锁保护客户端初始化状态
        with self._state_lock:
            if self._client_initialized:
                return True

            SYLogger.warning("nacos:客户端未初始化，尝试连接...")

            # 记录尝试次数，避免无限循环
            attempt = 0
            max_attempts = 2 if retry_once else self.max_retries

            while attempt < max_attempts:
                try:
                    register_ip = self.nacos_config['registerIp']
                    namespace_id = self.nacos_config['namespaceId']

                    # 创建新的Nacos客户端实例
                    self.nacos_client = nacos.NacosClient(
                        server_addresses=register_ip,
                        namespace=namespace_id
                    )

                    # 验证客户端是否真正可用
                    connection_valid = self._verify_client_connection()

                    if connection_valid:
                        self._client_initialized = True
                        SYLogger.info("nacos:客户端初始化成功")

                        # 客户端重新连接后，检查服务注册状态
                        self.registered = self.check_service_registered()
                        return True
                    else:
                        raise ConnectionError("nacos:客户端初始化后无法验证连接")

                except Exception as e:
                    attempt += 1
                    delay = min(self.retry_delay, self.max_retry_delay)

                    SYLogger.error(
                        f"nacos:客户端初始化失败 (尝试 {attempt}/{max_attempts}): {e}")
                    time.sleep(delay)

            SYLogger.error("nacos:无法连接到 Nacos 服务器，已达到最大重试次数")
            return False

    def _verify_client_connection(self):
        """验证客户端是否真正连接成功"""
        # 本地开发模式下直接返回True，不进行实际验证
        if not self.enable_register_nacos:
            return True

        try:
            # 使用当前服务的命名实例查询来验证连接
            namespace_id = self.nacos_config['namespaceId']
            self.nacos_client.list_naming_instance(
                service_name=self.service_name,
                namespace_id=namespace_id,
                group_name="DEFAULT_GROUP",
                healthy_only=True
            )
            return True
        except Exception as e:
            SYLogger.warning(f"nacos:客户端连接验证失败: {e}")
            return False

    def check_service_registered(self):
        """检查服务是否已注册（基于实例列表）"""
        # 本地开发模式下直接返回True，模拟已注册状态
        if not self.enable_register_nacos:
            return True

        if not self.ensure_client_connected():
            return False

        try:
            namespace_id = self.nacos_config['namespaceId']
            instances = self.nacos_client.list_naming_instance(
                service_name=self.service_name,
                namespace_id=namespace_id,
                group_name="DEFAULT_GROUP",
                healthy_only=True,
            )

            # 检查是否存在包含当前IP和端口的实例
            found = False
            for instance in instances.get('hosts', []):
                if (instance.get('ip') == self.real_ip and
                        instance.get('port') == int(self.port)):
                    SYLogger.info(f"nacos:找到已注册实例: {self.real_ip}:{self.port}")
                    found = True
                    break

            if not found:
                SYLogger.warning(f"nacos:未找到注册实例: {self.real_ip}:{self.port}")

            # 带锁更新注册状态
            with self._state_lock:
                self.registered = found

            return found
        except Exception as e:
            SYLogger.error(f"nacos:检查服务注册状态失败: {e}")
            return False

    def verify_registration(self):
        """多次验证服务是否成功注册"""
        success_count = 0
        SYLogger.info(
            f"nacos:开始验证服务注册状态，共验证 {self.registration_verify_count} 次")

        for i in range(self.registration_verify_count):
            if self.check_service_registered():
                success_count += 1
            else:
                SYLogger.warning(f"nacos:第 {i+1} 次验证未找到注册实例")

            if i < self.registration_verify_count - 1:
                time.sleep(self.registration_verify_interval)

        if success_count >= self.registration_verify_count / 2:
            SYLogger.info(
                f"nacos:服务注册验证成功，{success_count}/{self.registration_verify_count} 次验证通过")
            return True
        else:
            SYLogger.error(
                f"nacos:服务注册验证失败，仅 {success_count}/{self.registration_verify_count} 次验证通过")
            return False

    def register_with_retry(self):
        """带重试机制的服务注册（基于实例列表检查）"""
        retry_count = 0
        last_error = None

        # 带锁重置注册状态
        with self._state_lock:
            self.registered = False

        while (not self.registered) and (self.max_long_term_retries < 0 or retry_count < self.max_long_term_retries):
            # 增加状态检查点，防止重复注册
            with self._state_lock:
                if self.registered:
                    return True

            try:
                # 尝试注册服务
                register_success = self.register(force=True)

                if not register_success:
                    raise RuntimeError("nacos:服务注册请求失败")

                # 关键优化1：注册请求发送后，延迟一段时间再验证（默认3秒）
                SYLogger.info(
                    f"nacos:服务注册请求已发送，延迟 {self.registration_post_delay} 秒后开始验证（确保Nacos服务器完成实例写入）")
                time.sleep(self.registration_post_delay)

                # 关键优化2：多次验证服务是否真正注册成功（默认3次，每次间隔2秒）
                registered = self.verify_registration()

                # 带锁更新注册状态
                with self._state_lock:
                    self.registered = registered

                # 再次检查状态，防止其他线程修改
                with self._state_lock:
                    if self.registered:
                        # 注册成功后，更新客户端状态
                        self._client_initialized = True

                        # 注册成功后，通知心跳线程立即发送心跳
                        self._shutdown_event.set()
                        self._shutdown_event.clear()

                        # 注册成功后，更新监控线程的状态
                        self._long_term_retry_count = 0

                        SYLogger.info(
                            f"nacos:服务注册成功并通过验证: {self.service_name}")
                        return True
                    else:
                        raise RuntimeError("nacos:服务注册验证失败")

            except Exception as e:
                last_error = str(e)
                retry_count += 1
                delay = min(self.register_retry_interval, self.max_retry_delay)

                SYLogger.warning(
                    f"nacos:服务注册尝试 {retry_count} 失败: {last_error}，{delay}秒后重试")
                time.sleep(delay)

        # 最终检查，防止在最后一次重试后其他线程成功注册
        with self._state_lock:
            if self.registered:
                return True

        # 确实注册失败
        if last_error:
            SYLogger.error(f"nacos:服务注册失败，最终错误: {last_error}")
        else:
            SYLogger.error(f"nacos:服务注册失败，已达到最大重试次数: {self.service_name}")

        return False

    def register(self, force=False):
        """注册服务到Nacos"""
        # 使用状态锁保护注册状态
        with self._state_lock:
            if self.registered and not force and self.check_service_registered():
                return True

            if self.registered and not force:
                self.registered = False
                SYLogger.warning("nacos:本地状态显示已注册，但Nacos中未找到服务实例，准备重新注册")

            metadata = {
                "ignore-metrics": "true",
                # "preserved.heart.beat.interval": "3000",  # 心跳间隔 3 秒
                # "preserved.heart.beat.timeout": "15000",  # 心跳超时 15 秒
                # "preserved.ip.delete.timeout": "30000"    # 实例删除超时 30 秒
            }
            if self.version:
                metadata["version"] = self.version

            for attempt in range(self.max_retries):
                if not self.ensure_client_connected():
                    return False

                try:
                    # 注册服务
                    self.nacos_client.add_naming_instance(
                        service_name=self.service_name,
                        ip=self.real_ip,
                        port=int(self.port),
                        metadata=metadata,
                        cluster_name="DEFAULT",
                        healthy=True,
                        ephemeral=True,
                        heartbeat_interval=self.heartbeat_interval
                    )
                    SYLogger.info(
                        f"nacos:服务 {self.service_name} 注册请求已发送: {self.real_ip}:{self.port}")

                    # 注册退出时的清理函数
                    if not hasattr(self, '_atexit_registered') or not self._atexit_registered:
                        atexit.register(self.deregister_service)
                        self._atexit_registered = True

                    return True
                except Exception as e:
                    if "signal only works in main thread" in str(e):
                        return True
                    elif attempt < self.max_retries - 1:
                        SYLogger.warning(
                            f"nacos:服务注册失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        SYLogger.error(f"nacos:服务注册失败，已达到最大重试次数: {e}")
                        return False

    @staticmethod
    def setup_nacos(config: dict):
        """创建并初始化Nacos管理器"""
        instance = NacosService(config)

        # 仅在需要注册时执行注册逻辑
        if instance.enable_register_nacos:
            # 使用带超时的等待机制，而不是单次尝试
            timeout = 60  # 60秒超时
            start_time = time.time()

            # 启动注册线程，不阻塞主线程（替换原线程池）
            register_thread = threading.Thread(
                target=instance.register_with_retry,
                daemon=True,
                name="NacosRegisterThread"
            )
            register_thread.start()

            # 等待注册完成或超时
            while True:
                # 带锁检查状态
                with instance._state_lock:
                    if instance.registered:
                        break

                if time.time() - start_time >= timeout:
                    # 超时处理
                    break

                time.sleep(1)

            # 最终状态检查
            with instance._state_lock:
                if not instance.registered:
                    # 清理并抛出异常
                    try:
                        instance.deregister_service()
                    except Exception as e:
                        SYLogger.error(f"nacos:服务注册失败后，注销服务时发生错误: {e}")
                    raise RuntimeError("nacos:服务注册失败，应用启动终止")

            # 服务注册成功后再注册信号处理
            signal.signal(signal.SIGTERM, instance.handle_signal)
            signal.signal(signal.SIGINT, instance.handle_signal)

            # 启动连接监控线程
            threading.Thread(target=instance.monitor_connection,
                             daemon=True, name="NacosConnectionMonitorThread").start()
        else:
            SYLogger.info("nacos:本地开发模式，跳过服务注册流程")

        return instance

    def start_heartbeat(self):
        """启动心跳线程（确保单例）"""
        with self._heartbeat_lock:  # 加锁确保线程安全
            # 双重检查：先判断线程是否已存在且存活
            if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
                return

            # 彻底清理可能的残留线程引用
            self._heartbeat_thread = None

            # 创建新的心跳线程
            self._heartbeat_thread = threading.Thread(
                target=self._send_heartbeat_loop,
                name="NacosHeartbeatThread",
                daemon=True
            )
            self._heartbeat_thread.daemon = True
            self._heartbeat_thread.start()
            SYLogger.info(
                f"nacos:心跳线程启动，线程ID: {self._heartbeat_thread.ident}，"
                f"心跳间隔: {self.heartbeat_interval}秒，"
                f"心跳超时: {self.heartbeat_timeout}秒"
            )

    def _send_heartbeat_loop(self):
        """优化后的心跳发送循环，确保严格按间隔执行"""
        current_thread = threading.current_thread()
        thread_ident = current_thread.ident
        SYLogger.info(
            f"nacos:心跳循环启动 - 线程ID: {thread_ident}, "
            f"配置间隔: {self.heartbeat_interval}秒, "
            f"超时时间: {self.heartbeat_timeout}秒"
        )

        consecutive_fail = 0  # 连续失败计数器

        while not self._shutdown_event.is_set():
            # 记录当前时间，作为本次心跳的基准
            current_time = time.time()

            try:
                # 检查注册状态（带锁读取）
                with self._state_lock:
                    registered_status = self.registered

                if not registered_status:
                    SYLogger.warning(
                        f"nacos:服务未注册，跳过心跳 - 线程ID: {thread_ident}")
                    consecutive_fail = 0
                else:
                    # 发送心跳（10秒超时）
                    success = self.send_heartbeat()
                    if success:
                        consecutive_fail = 0
                        self._last_successful_heartbeat = current_time
                        SYLogger.info(
                            f"nacos:心跳发送成功 - 时间: {current_time:.3f}, "
                            f"间隔: {self.heartbeat_interval}秒"
                        )
                    else:
                        consecutive_fail += 1
                        SYLogger.warning(
                            f"nacos:心跳发送失败 - 连续失败: {consecutive_fail}次"
                        )
                        if consecutive_fail >= 5:
                            SYLogger.error("nacos:心跳连续失败5次，尝试重连")
                            self.reconnect_nacos_client()
                            consecutive_fail = 0

            except Exception as e:
                consecutive_fail += 1
                SYLogger.error(
                    f"nacos:心跳异常: {str(e)}, 连续失败: {consecutive_fail}次")

            # 计算下次执行时间（当前时间 + 配置间隔），确保间隔稳定
            next_run_time = current_time + self.heartbeat_interval
            sleep_time = max(0, next_run_time - time.time()
                             )  # 避免负数（处理耗时超过间隔的情况）
            self._shutdown_event.wait(sleep_time)  # 精准休眠至下次执行时间

        SYLogger.info(f"nacos:心跳循环已停止 - 线程ID: {thread_ident}")

    def send_heartbeat(self):
        """发送心跳并添加10秒超时控制（替换线程池实现）"""
        if not self.ensure_client_connected():
            SYLogger.warning("nacos:客户端未连接，心跳发送失败")
            return False

        # 用线程+join实现10秒超时控制
        result_list = []  # 用于线程间传递结果

        def heartbeat_task():
            """心跳实际执行任务"""
            try:
                result = self._send_heartbeat_internal()
                result_list.append(result)
            except Exception as e:
                SYLogger.error(f"nacos:心跳任务执行异常: {e}")
                result_list.append(False)

        # 启动心跳任务线程
        task_thread = threading.Thread(
            target=heartbeat_task,
            daemon=True,
            name="NacosHeartbeatTaskThread"
        )
        task_thread.start()

        # 等待线程完成，最多等待10秒
        task_thread.join(timeout=self.heartbeat_timeout)

        # 处理结果
        if not result_list:
            # 超时未返回
            SYLogger.error(f"nacos:心跳发送超时（{self.heartbeat_timeout}秒）")
            self._client_initialized = False  # 强制重连
            return False

        # 检查心跳结果
        if result_list[0]:
            self._last_successful_heartbeat = time.time()
        return result_list[0]

    def _send_heartbeat_internal(self):
        """实际的心跳发送逻辑"""
        result = self.nacos_client.send_heartbeat(
            service_name=self.service_name,
            ip=self.real_ip,
            port=int(self.port),
            cluster_name="DEFAULT",
            weight=1.0,
            metadata={"version": self.version} if self.version else None
        )

        # 处理返回结果
        if result and isinstance(result, dict) and result.get('lightBeatEnabled', False):
            SYLogger.info(f"nacos:心跳发送成功，Nacos返回: {result}")
            return True
        else:
            SYLogger.warning(f"nacos:心跳发送失败，Nacos返回: {result}")
            return False

    def reconnect_nacos_client(self):
        """重新连接Nacos客户端"""
        SYLogger.warning("nacos:尝试重新连接Nacos客户端")
        self._client_initialized = False
        return self.ensure_client_connected()

    def monitor_connection(self):
        """优化的连接监控线程，缩短检查间隔"""
        check_interval = self.connection_check_interval
        thread_start_time = time.time()
        check_counter = 0

        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()

                SYLogger.info(
                    f"nacos:连接监控线程运行中，检查间隔: {check_interval}s")

                # 检查客户端连接状态
                if not self.ensure_client_connected():
                    SYLogger.warning("nacos:检测到Nacos客户端连接丢失，尝试重新初始化")
                    self._initialize_client()  # 尝试重新初始化客户端

                # 检查服务注册状态
                current_registered = self.check_service_registered()

                # 带锁更新注册状态
                with self._state_lock:
                    if current_registered != self.registered:
                        if current_registered:
                            self.registered = True
                            SYLogger.info(f"nacos:服务实例已重新注册")
                        else:
                            self.registered = False
                            SYLogger.warning(f"nacos:服务实例未注册，尝试重新注册")
                            # 启动临时线程执行重新注册（替换原线程池）
                            retry_thread = threading.Thread(
                                target=self.register_with_retry,
                                daemon=True,
                                name="NacosRetryRegisterThread"
                            )
                            retry_thread.start()

                # 20%的概率执行深度检查
                if random.random() < 0.2:
                    self.verify_registration()

                # 每小时重置一次内部状态
                if current_time - thread_start_time > 3600:
                    SYLogger.info("nacos:连接监控线程已运行1小时，重置内部状态")
                    thread_start_time = current_time
                    check_counter = 0

                check_counter += 1
                # 休眠指定时间
                self._shutdown_event.wait(check_interval)
            except Exception as e:
                SYLogger.error(f"nacos:连接监控异常: {e}")
                time.sleep(self.retry_delay)

    def get_service_ip(self, config_ip):
        """获取服务实际IP地址"""
        if config_ip in ['127.0.0.1', '0.0.0.0']:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(('8.8.8.8', 80))
                    return s.getsockname()[0]
            except Exception:
                return '127.0.0.1'
        return config_ip

    def deregister_service(self):
        """从Nacos注销服务"""
        with self._state_lock:
            if not self.registered or not self._client_initialized:
                return

        SYLogger.info("nacos:正在注销服务...")
        try:
            self.nacos_client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.real_ip,
                port=int(self.port),
                cluster_name="DEFAULT"
            )
            with self._state_lock:
                self.registered = False
            SYLogger.info(f"nacos:服务 {self.service_name} 已注销")
        except Exception as e:
            SYLogger.error(f"nacos:注销服务时发生错误: {e}")
        finally:
            self._shutdown_event.set()

    def handle_signal(self, signum, frame):
        """处理退出信号"""
        SYLogger.info(f"nacos:收到信号 {signum}，正在关闭服务...")
        self.deregister_service()
        sys.exit(0)

    def read_configs(self) -> dict:
        """读取共享配置"""
        configs = {}
        shared_configs = self.nacos_config.get('sharedConfigs', [])

        for config in shared_configs:
            data_id = config['dataId']
            group = config['group']

            for attempt in range(self.max_retries):
                try:
                    # 检查客户端连接
                    if not self.ensure_client_connected():
                        self.reconnect_nacos_client()

                    # 获取配置
                    content = self.nacos_client.get_config(data_id, group)

                    try:
                        configs[data_id] = json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            configs[data_id] = yaml.safe_load(content)
                        except yaml.YAMLError:
                            SYLogger.error(f"nacos:无法解析 {data_id} 的内容")
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        SYLogger.warning(
                            f"nacos:读取配置 {data_id} 失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        SYLogger.error(
                            f"nacos:读取配置 {data_id} 失败，已达到最大重试次数: {e}")

        return configs

    def add_config_listener(self, data_id: str, callback: Callable[[str], None]):
        """添加配置变更监听器"""
        self._config_listeners[data_id] = callback
        # 初始获取一次配置
        if config := self.get_config(data_id):
            callback(config)

    def get_config(self, data_id: str, group: str = "DEFAULT_GROUP") -> Optional[str]:
        """获取配置内容"""
        if not self.ensure_client_connected():
            return None

        try:
            return self.nacos_client.get_config(data_id, group=group)
        except Exception as e:
            SYLogger.error(f"nacos:获取配置 {data_id} 失败: {str(e)}")
            return None

    def _watch_configs(self):
        """配置监听线程"""
        check_interval = self.config_watch_interval

        while not self._shutdown_event.is_set():
            try:
                for data_id, callback in list(self._config_listeners.items()):
                    new_config = self.get_config(data_id)
                    if new_config and new_config != self._config_cache.get(data_id):
                        # 直接执行回调（替换原线程池，配置回调通常为轻量操作）
                        callback(new_config)
                        self._config_cache[data_id] = new_config
            except Exception as e:
                SYLogger.error(f"nacos:配置监视线程异常: {str(e)}")
            self._shutdown_event.wait(check_interval)

    def discover_services(self, service_name: str, group: str = "DEFAULT_GROUP", version: str = None) -> List[Dict]:
        """发现服务实例列表 (与Java格式兼容)"""
        if not self.ensure_client_connected():
            return []

        return self.get_service_instances(service_name, group, version)

    def get_service_instances(self, service_name: str, group: str = "DEFAULT_GROUP", target_version: str = None) -> List[Dict]:
        """
        获取服务实例列表，并按照以下优先级规则筛选：
        1. 相同版本号的实例
        2. 无版本号的实例
        3. 所有实例中轮询
        """
        try:
            namespace_id = self.nacos_config['namespaceId']
            instances = self.nacos_client.list_naming_instance(
                service_name,
                namespace_id=namespace_id,
                group_name=group,
                healthy_only=True,
            )

            if not instances or 'hosts' not in instances:
                SYLogger.info(f"nacos:未发现 {service_name} 的服务实例")
                return []

            all_instances = instances.get('hosts', [])
            SYLogger.info(
                f"nacos:共发现 {len(all_instances)} 个 {service_name} 服务实例")

            # 确定要使用的目标版本，如果未指定则使用当前服务的版本
            version_to_use = target_version or self.version

            # 按规则筛选实例
            if version_to_use:
                # 1. 筛选相同版本号的实例
                same_version_instances = [
                    instance for instance in all_instances
                    if instance.get('metadata', {}).get('version') == version_to_use
                ]

                if same_version_instances:
                    SYLogger.info(
                        f"nacos:筛选出 {len(same_version_instances)} 个与当前版本({version_to_use})匹配的实例")
                    return same_version_instances

                # 2. 如果没有相同版本的实例，筛选无版本号的实例
                no_version_instances = [
                    instance for instance in all_instances
                    if 'version' not in instance.get('metadata', {})
                ]

                if no_version_instances:
                    SYLogger.info(
                        f"nacos:未找到相同版本({version_to_use})的实例，筛选出 {len(no_version_instances)} 个无版本号的实例")
                    return no_version_instances

            # 3. 如果没有指定版本或前两个规则都不满足，使用轮询方式选择所有健康实例
            SYLogger.info(
                f"nacos:使用轮询方式从 {len(all_instances)} 个实例中选择")

            # 线程安全地获取下一个轮询索引
            with self._round_robin_lock:
                selected_index = self._round_robin_index % len(all_instances)
                # 更新轮询索引，为下一次请求做准备
                self._round_robin_index = (
                    selected_index + 1) % len(all_instances)

            # 返回包含当前选中实例的列表
            return [all_instances[selected_index]]

        except Exception as e:
            SYLogger.error(f"nacos:服务发现失败: {service_name}: {str(e)}")
            return []
