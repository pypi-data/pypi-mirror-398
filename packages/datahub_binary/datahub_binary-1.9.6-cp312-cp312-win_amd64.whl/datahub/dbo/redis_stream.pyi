from ..protos.client_msg import deserialize as deserialize, serialize as serialize
from _typeshed import Incomplete
from datahub.setting import RedisSetting as RedisSetting
from typing import Any, Callable, Iterator, Sequence

class RedisStream:
    client: Incomplete
    ident: Incomplete
    def __init__(self, setting: RedisSetting) -> None:
        """
        接收Redis Stream消息

        :param setting: 配置
        """
    def ensure_group(self, topics: Sequence[str]):
        """
        创建消费者组

        :param topics: 主题列表
        :return:
        """
    def set_position(self, topic: str, posi: str):
        """
        设置消费者组的位置

        :param topic: Topic
        :param posi: 位置标记, 格式 {timestamp_ms}-{int}
        :return:
        """
    def read(self, topics: Sequence[str], count: int = 1, ignore_pending: bool = False, block: int = 0, decode_func=...) -> Iterator[Any]:
        """
        迭代读取proto消息, 自动ack

        :param topics: topic列表
        :param count: 单次读取上限
        :param ignore_pending: 是否忽略pending消息, 如果为False, 则会先读取pending消息, 然后读取最新消息
        :param block: 阻塞毫秒数，0为一直等待，超时后会直接返回
        :param decode_func: 解码函数，默认使用proto解码
        :return: proto msg
        """
    def write(self, topic: str, proto_msg: Any, encode_func: Callable = ...):
        """
        向stream写入proto消息

        :param topic: 主题
        :param proto_msg: proto消息
        :param encode_func: 编码函数，默认使用proto
        :return: None
        """
    def delete(self, topic: str):
        """
        删除给定的stream

        :param topic: 主题
        :return: None
        """
    def ack(self, topic: str, message_id: str): ...
