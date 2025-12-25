import time
import threading
import socket
import hashlib
import random
from typing import Optional
from os import environ
import netifaces


class Snowflake:
    """雪花算法生成器（无公网依赖，适配内网环境）"""
    START_TIMESTAMP = 1388534400000  # 2014-01-01 00:00:00
    SEQUENCE_BITS = 12
    MACHINE_ID_BITS = 10
    MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1  # 0~1023
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1
    MACHINE_ID_SHIFT = SEQUENCE_BITS
    TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS

    # 类级别的单例实例
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self, machine_id: Optional[int] = None):
        """
        初始化：优先使用传入的machine_id，否则自动从K8s环境获取
        :param machine_id: 手动指定机器ID（None则自动计算）
        """
        # 自动计算K8s环境下的machine_id
        if machine_id is None:
            machine_id = self._get_k8s_machine_id()

        if not (0 <= machine_id <= self.MAX_MACHINE_ID):
            raise ValueError(f"机器ID必须在0~{self.MAX_MACHINE_ID}之间")

        self.machine_id = machine_id
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def _get_k8s_machine_id(self) -> int:
        """
        从K8s环境自动计算唯一machine_id（无公网依赖，多层兜底）：
        优先级：POD_NAME > POD_IP > 容器内网IP（网卡读取） > 容器主机名 > 随机数（最终兜底）
        """
        # 1. 优先读取K8s内置的POD_NAME（默认注入，优先级最高）
        pod_name = environ.get("POD_NAME")
        if pod_name:
            return self._hash_to_machine_id(pod_name)

        # 2. 读取POD_IP（手动配置downwardAPI后必存在）
        pod_ip = environ.get("POD_IP")
        if pod_ip:
            return self._hash_to_machine_id(pod_ip)

        # 3. 兜底1：读取本机网卡获取内网IP（无公网依赖）
        try:
            local_ip = self._get_local_internal_ip()
            if local_ip:
                return self._hash_to_machine_id(local_ip)
            else:
                # logger.warning("读取网卡信息成功，但未找到非回环内网IP")
                pass
        except Exception as e:
            # logger.warning(f"读取本机网卡IP失败: {e}，尝试使用主机名")
            pass

        # 4. 兜底2：获取容器主机名（K8s中默认等于Pod名称，保证唯一）
        hostname = socket.gethostname()
        if hostname:
            # logger.info(
            #     f"未读取到POD_NAME/POD_IP/内网IP，使用主机名: {hostname}生成machine_id")
            return self._hash_to_machine_id(hostname)

        # 5. 最终兜底：生成随机数（仅极端情况使用，日志告警）
        random_id = random.randint(0, self.MAX_MACHINE_ID)
        # logger.warning(f"所有方式均失败，使用随机数生成machine_id: {random_id}（可能重复！）")
        return random_id

    def _get_local_internal_ip(self) -> Optional[str]:
        """
        读取本机网卡信息，获取非回环的内网IP（无公网依赖）
        :return: 内网IP字符串，失败返回None
        """
        try:
            # 遍历所有网卡
            for interface in netifaces.interfaces():
                # 获取网卡的IP地址信息
                addrs = netifaces.ifaddresses(interface)
                # 只取IPv4地址
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        # 过滤回环地址（127.0.0.1）和docker虚拟地址（172.17.0.0/16可选过滤）
                        if ip and not ip.startswith('127.'):
                            # 可选：过滤docker0的默认地址段（根据实际内网段调整）
                            # if not ip.startswith('172.17.'):
                            return ip
            return None
        except ImportError:
            # 若未安装netifaces，降级为socket方式（仅尝试本地解析，无公网连接）
            # logger.warning("未安装netifaces库，尝试降级方式获取IP")
            return self._get_local_ip_fallback()

    def _get_local_ip_fallback(self) -> Optional[str]:
        """
        降级方案：不连接公网，仅通过本地socket获取IP（兼容无netifaces的场景）
        """
        try:
            # 创建socket但不连接任何地址，仅绑定到本地
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 绑定到0.0.0.0:0（仅用于获取本机IP，不发送数据）
            s.bind(('', 0))
            local_ip = s.getsockname()[0]
            s.close()
            # 过滤回环地址
            if not local_ip.startswith('127.'):
                return local_ip
            return None
        except Exception:
            return None

    def _hash_to_machine_id(self, text: str) -> int:
        """将字符串哈希后取模，得到0~1023的machine_id（保证分布均匀）"""
        hash_bytes = hashlib.md5(text.encode("utf-8")).digest()
        hash_int = int.from_bytes(hash_bytes[:4], byteorder="big")
        return hash_int % self.MAX_MACHINE_ID

    def _get_current_timestamp(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millisecond(self, current_timestamp: int) -> int:
        while current_timestamp <= self.last_timestamp:
            current_timestamp = self._get_current_timestamp()
        return current_timestamp

    def generate_id(self) -> int:
        with self.lock:
            current_timestamp = self._get_current_timestamp()

            if current_timestamp < self.last_timestamp:
                raise RuntimeError(
                    f"时钟回拨检测：当前时间戳({current_timestamp}) < 上一次时间戳({self.last_timestamp})"
                )

            if current_timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    current_timestamp = self._wait_next_millisecond(
                        current_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = current_timestamp

            snowflake_id = (
                ((current_timestamp - self.START_TIMESTAMP) << self.TIMESTAMP_SHIFT)
                | (self.machine_id << self.MACHINE_ID_SHIFT)
                | self.sequence
            )

            return snowflake_id

    @staticmethod
    def parse_id(snowflake_id: int) -> dict:
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
            "sequence": sequence
        }

    @classmethod
    def next_id(cls) -> str:
        """
        生成雪花ID（单例模式，避免重复创建实例）
        :return: 雪花ID字符串
        """
        # 单例模式创建实例
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        # 生成ID并转为字符串返回
        return str(cls._instance.generate_id())


if __name__ == "__main__":
    # 生成1000个ID并验证
    id_set = set()  # 用于检测重复ID
    _MAX_JAVA_LONG = 9223372036854775807

    for i in range(1000):
        id_str = Snowflake.next_id()
        id_num = int(id_str)

        # 验证ID不超过Java long最大值
        assert id_num <= _MAX_JAVA_LONG, f"ID超过Java long最大值: {id_num}"

        # 验证ID不重复
        assert id_str not in id_set, f"重复生成ID: {id_str}"
        id_set.add(id_str)

        # 每100个ID打印一次解析结果
        if i % 100 == 0:
            parse_result = Snowflake.parse_id(id_num)
            print(f"生成ID: {id_str}")
            print(f"解析结果: {parse_result}")
            print("-" * 50)

    print(f"成功生成{len(id_set)}个唯一雪花ID，验证通过！")
