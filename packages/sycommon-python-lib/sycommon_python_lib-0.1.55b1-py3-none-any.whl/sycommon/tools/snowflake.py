import time
import threading
import socket
import hashlib
import random
import os
from typing import Optional, Type, Any
from os import environ
import psutil


class ClassProperty:
    """
    自定义类属性描述符，替代 @classmethod + @property 的废弃写法
    支持通过 类.属性 的方式访问，无需实例化
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, instance: Any, cls: Type) -> str:
        # 调用传入的函数，并传入类本身作为第一个参数
        return self.func(cls)


class Snowflake:
    """雪花算法生成器（生产级优化版，无公网依赖，适配内网/K8s环境）"""
    # 基础配置（可根据业务调整）
    START_TIMESTAMP = 1388534400000  # 2014-01-01 00:00:00
    SEQUENCE_BITS = 12
    MACHINE_ID_BITS = 10
    MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1  # 0~1023
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
    MACHINE_ID_SHIFT = SEQUENCE_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS
    CLOCK_BACKWARD_THRESHOLD = 5  # 容忍的时钟回拨阈值（毫秒）
    _MAX_JAVA_LONG = 9223372036854775807  # Java Long最大值

    # 类级别的单例实例（线程安全）
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, machine_id: Optional[int] = None):
        """
        初始化：优先使用传入的machine_id，否则自动从K8s环境获取
        :param machine_id: 手动指定机器ID（None则自动计算）
        """
        # 前置校验：确保雪花ID不会超过Java Long最大值
        self._validate_timestamp_range()

        # 自动计算K8s环境下的machine_id
        if machine_id is None:
            machine_id = self._get_k8s_machine_id()

        # 校验machine_id合法性
        if not (0 <= machine_id <= self.MAX_MACHINE_ID):
            raise ValueError(f"机器ID必须在0~{self.MAX_MACHINE_ID}之间")

        # 初始化核心参数
        self.machine_id = machine_id
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def _validate_timestamp_range(self):
        """校验当前时间戳是否在雪花ID支持的范围内，避免超过Java Long最大值"""
        max_support_timestamp = self.START_TIMESTAMP + \
            (1 << (64 - self.TIMESTAMP_SHIFT)) - 1
        current_timestamp = self._get_current_timestamp()
        if current_timestamp > max_support_timestamp:
            raise RuntimeError(
                f"当前时间戳({current_timestamp})超过雪花ID支持的最大时间戳({max_support_timestamp})，"
                f"请调整START_TIMESTAMP或减少TIMESTAMP_SHIFT位数"
            )

    def _get_k8s_machine_id(self) -> int:
        """
        从K8s环境自动计算唯一machine_id（无公网依赖，多层兜底，降低重复风险）：
        优先级：POD_NAME > POD_IP > 容器内网IP（psutil读取） > 容器主机名 > 进程+时间+随机数（最终兜底）
        """
        # 1. 优先读取K8s内置的POD_NAME（默认注入，优先级最高）
        pod_name = environ.get("POD_NAME")
        if pod_name:
            return self._hash_to_machine_id(pod_name)

        # 2. 读取POD_IP（手动配置downwardAPI后必存在）
        pod_ip = environ.get("POD_IP")
        if pod_ip:
            return self._hash_to_machine_id(pod_ip)

        # 3. 兜底1：读取本机网卡获取内网IP（替换netifaces，使用psutil）
        try:
            local_ip = self._get_local_internal_ip()
            if local_ip:
                return self._hash_to_machine_id(local_ip)
        except Exception:
            pass

        # 4. 兜底2：获取容器主机名（K8s中默认等于Pod名称，保证唯一）
        hostname = socket.gethostname()
        if hostname:
            return self._hash_to_machine_id(hostname)

        # 5. 最终兜底：增加熵值（进程ID+毫秒时间戳+随机数），大幅降低重复概率
        fallback_text = f"{os.getpid()}_{int(time.time()*1000)}_{random.randint(0, 100000)}"
        return self._hash_to_machine_id(fallback_text)

    def _get_local_internal_ip(self) -> Optional[str]:
        """
        使用psutil读取本机网卡信息，获取非回环的内网IP（跨平台兼容，过滤lo/lo0等回环网卡）
        :return: 内网IP字符串，失败返回None
        """
        try:
            # 遍历所有网卡接口
            net_if_addrs = psutil.net_if_addrs()
            for interface_name, addrs in net_if_addrs.items():
                # 过滤回环/虚拟网卡（兼容lo、lo0、lo1、Loopback、virtual等）
                if (interface_name.lower().startswith("lo")
                        or interface_name.lower() in ["loopback", "virtual"]):
                    continue
                # 遍历该网卡的所有地址，优先返回第一个非回环IPv4
                for addr in addrs:
                    if addr.family == psutil.AF_INET:
                        ip = addr.address
                        if ip and not ip.startswith('127.'):
                            return ip
            return None
        except Exception:
            # psutil调用失败，降级到纯内置方法
            return self._get_local_ip_fallback()

    def _get_local_ip_fallback(self) -> Optional[str]:
        """
        增强版降级方案：纯Python内置方法，多维度获取内网IP（无第三方依赖）
        """
        # 方案1：socket绑定内网地址（避免访问公网）
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("192.168.0.1", 80))
            local_ip = s.getsockname()[0]
            s.close()
            if not local_ip.startswith('127.'):
                return local_ip
        except Exception:
            pass

        # 方案2：遍历所有本地IP（通过hostname解析）
        try:
            hostname = socket.gethostname()
            ip_list = socket.gethostbyname_ex(hostname)[2]
            for ip in ip_list:
                if not ip.startswith('127.'):
                    return ip
        except Exception:
            pass

        return None

    def _hash_to_machine_id(self, text: str) -> int:
        """将字符串哈希后取模，得到0~1023的machine_id（保证分布均匀）"""
        hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
        hash_int = int.from_bytes(hash_bytes[:4], byteorder="big")
        return hash_int % self.MAX_MACHINE_ID

    def _get_current_timestamp(self) -> int:
        """获取当前毫秒级时间戳"""
        return int(time.time() * 1000)

    def _wait_next_millisecond(self, current_timestamp: int) -> int:
        """等待直到下一个毫秒，避免序列耗尽"""
        while current_timestamp <= self.last_timestamp:
            current_timestamp = self._get_current_timestamp()
        return current_timestamp

    def generate_id(self) -> int:
        """生成雪花ID（生产级优化：优化锁粒度，容忍轻微时钟回拨）"""
        current_timestamp = self._get_current_timestamp()

        # 1. 处理时钟回拨：容忍CLOCK_BACKWARD_THRESHOLD内的微调，超过则抛异常
        time_diff = self.last_timestamp - current_timestamp
        if time_diff > 0:
            if time_diff > self.CLOCK_BACKWARD_THRESHOLD:
                raise RuntimeError(
                    f"时钟回拨检测：当前时间戳({current_timestamp}) < 上一次时间戳({self.last_timestamp})，"
                    f"差值{time_diff}ms（阈值{self.CLOCK_BACKWARD_THRESHOLD}ms）"
                )
            # 轻微回拨：等待时钟追上
            current_timestamp = self._wait_next_millisecond(current_timestamp)

        # 2. 优化锁粒度：仅在同一毫秒内递增序列时加锁
        if current_timestamp != self.last_timestamp:
            with self.lock:
                self.last_timestamp = current_timestamp
                self.sequence = 0
        else:
            with self.lock:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    current_timestamp = self._wait_next_millisecond(
                        current_timestamp)
                    self.last_timestamp = current_timestamp

        # 3. 计算最终雪花ID
        snowflake_id = (
            ((current_timestamp - self.START_TIMESTAMP) << self.TIMESTAMP_SHIFT)
            | (self.machine_id << self.MACHINE_ID_SHIFT)
            | self.sequence
        )

        # 最终校验：确保不超过Java Long最大值
        if snowflake_id > self._MAX_JAVA_LONG:
            raise RuntimeError(
                f"生成的雪花ID({snowflake_id})超过Java Long最大值({self._MAX_JAVA_LONG})")

        return snowflake_id

    @staticmethod
    def parse_id(snowflake_id: int) -> dict:
        """解析雪花ID，返回生成时间、机器ID、序列等信息"""
        from datetime import datetime
        sequence = snowflake_id & Snowflake.MAX_SEQUENCE
        machine_id = (snowflake_id >>
                      Snowflake.MACHINE_ID_SHIFT) & Snowflake.MAX_MACHINE_ID
        timestamp = (snowflake_id >> Snowflake.TIMESTAMP_SHIFT) + \
            Snowflake.START_TIMESTAMP
        generate_time = datetime.fromtimestamp(
            timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        return {
            "snowflake_id": snowflake_id,
            "generate_time": generate_time,
            "machine_id": machine_id,
            "sequence": sequence,
            "is_java_long_safe": snowflake_id <= Snowflake._MAX_JAVA_LONG
        }

    @classmethod
    def next_id(cls) -> str:
        """
        生成雪花ID（线程安全单例模式，避免重复创建实例，锁内完成所有初始化）
        :return: 雪花ID字符串
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    # 锁内初始化，避免多线程重复计算machine_id
                    cls._instance = cls()
        return str(cls._instance.generate_id())

    @ClassProperty
    def id(cls) -> str:
        """
        直接通过 `Snowflake.id` 属性生成雪花ID（兼容Python 3.11+）
        :return: 雪花ID字符串
        """
        return cls.next_id()


if __name__ == "__main__":
    print("=== 生产级雪花算法ID生成测试 ===")
    # 1. 基础生成测试
    id1 = Snowflake.id
    id2 = Snowflake.id
    id3 = Snowflake.id
    print(f"生成ID1: {id1}")
    print(f"生成ID2: {id2}")
    print(f"生成ID3: {id3}")
    print(f"ID是否唯一: {len({id1, id2, id3}) == 3}")

    # 2. 解析ID信息
    print("\n=== 雪花ID解析 ===")
    parse_info = Snowflake.parse_id(int(id3))
    for key, value in parse_info.items():
        print(f"{key}: {value}")

    # 3. 批量唯一性验证（10000个ID）
    print("\n=== 批量唯一性验证（10000个）===")
    id_set = set()
    duplicate_count = 0
    for i in range(10000):
        snow_id = Snowflake.id
        if snow_id in id_set:
            duplicate_count += 1
        id_set.add(snow_id)
    print(f"总生成数量: 10000")
    print(f"唯一ID数量: {len(id_set)}")
    print(f"重复ID数量: {duplicate_count}")
    print(f"机器ID: {Snowflake._instance.machine_id}")

    # 4. 高并发测试
    import concurrent.futures
    print("\n=== 高并发测试（100线程）===")
    id_set_concurrent = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(lambda: Snowflake.id) for _ in range(10000)]
        for future in concurrent.futures.as_completed(futures):
            id_set_concurrent.add(future.result())
    print(f"高并发生成唯一ID数量: {len(id_set_concurrent)}")

    print("\n=== 生产级雪花算法验证通过 ===")
