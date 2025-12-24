import math
import secrets
import string
import time
from dataclasses import dataclass

DEFAULT_ALPHABET = string.digits + string.ascii_letters + "-_"


def nanoid(size: int = 21, alphabet: str = DEFAULT_ALPHABET):
    """nanoid 生成函数。

    该函数使用加密安全的随机数生成器创建一个URL友好的唯一标识符。
    生成的ID由指定字母表中的字符组成，默认使用URL安全的字符集。

    Args:
        size (int, optional): 生成ID的长度。默认为21。
        alphabet (str, optional): 用于生成ID的字符集。默认为URL安全的字符集。

    Returns:
        str: 生成的随机ID字符串。

    Note:
        - 使用掩码机制确保随机数在字母表范围内
        - 通过token_bytes生成加密安全的随机字节
        - 实际生成的随机字节数会根据size和alphabet长度动态调整
    """
    alphabet_len = len(alphabet)
    # 掩码长度
    mask = (1 << (alphabet_len - 1).bit_length()) - 1
    step = math.ceil(size * 1.6 * mask / alphabet_len)
    charts = []
    for _ in range(step):
        random_bytes = secrets.token_bytes(step)
        for byte in random_bytes:
            # 通过掩码机制限制在指定范围内生成随机数字, 类似于 %
            index = byte & mask
            if index < alphabet_len:
                charts.append(alphabet[index])
            if len(charts) == size:
                return "".join(charts)


@dataclass
class Snakeflow:
    value: int
    """雪花id值"""
    machine_id: int
    """机器码"""
    sequence: int
    """序列号"""
    epoch: int
    """起时时间戳"""
    timestamp: int
    """时间戳"""
    timediff: int
    """时间差"""


class SnakeflowId:
    def __init__(self, machine_id=1, epoch=1288834974657):
        self.machine_id = machine_id
        self.epoch = epoch
        self.last_timestamp = -1

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp):
        """等待下一个毫秒数。避免同一毫秒生成了4095个超出限制"""
        timestamp = self._get_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._get_timestamp()
        return timestamp

    def set_params(self, machine_id=1, epoch=1288834974657):
        self.machine_id = machine_id
        self.epoch = epoch

    def generate(self):
        """生成一个雪花id

        Returns:
            str: 生成的Snakeflow ID。
        """
        timestamp = self._get_timestamp()
        # 时钟回拨处理
        if timestamp < self.last_timestamp:
            raise Exception("Clock moved backwards. Refusing to generate id")
        # 如果是同一毫秒内
        if timestamp == self.last_timestamp:
            # 雪花id，最后最多4095个
            self.sequence = (self.sequence + 1) & 0xFFF
            # 序列号溢出，等待下一毫秒
            if self.sequence == 0:
                timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0
        self.last_timestamp = timestamp
        id = str((timestamp - self.epoch) << 22 | self.machine_id << 12 | self.sequence)
        return id.zfill(20)

    def parse(self, snakeflow: str, epoch: str | None = None):
        if not epoch:
            epoch = self.epoch
        snakeflow = int(snakeflow)
        # 雪花id，机器码占10为，所以需要与 0x3FF(二进制10个1) 进行位运算
        match_id = snakeflow >> 12 & 0x3FF
        sequence = snakeflow & 0xFFF
        # 1FFFFFFFFFF 就是二进制的41个1, 雪花id前面41为为时间戳，间隔部分
        timediff = snakeflow >> 22 & 0x1FFFFFFFFFF
        return Snakeflow(
            value=int(snakeflow),
            machine_id=match_id,
            sequence=sequence,
            epoch=epoch,
            timestamp=timediff + epoch,
            timediff=timediff,
        )


snakeflowId = SnakeflowId()
