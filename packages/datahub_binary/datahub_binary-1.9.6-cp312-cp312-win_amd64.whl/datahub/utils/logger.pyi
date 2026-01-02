from .monitor import Feishu as Feishu
from _typeshed import Incomplete
from datetime import datetime as datetime
from pathlib import Path as Path
from typing import Callable, Literal

LOGURU_LEVEL: Incomplete

def timer_decorator(func: Callable) -> Callable:
    """
     简单计时装饰器，记录函数执行时间，并打印函数的传参值

    :param func: 被测试函数
    :return:
    """
def filter_log_level(record, level): ...

class Logger:
    log_dir: Incomplete
    retention: Incomplete
    name: Incomplete
    log_format: Incomplete
    trace: Incomplete
    debug: Incomplete
    info: Incomplete
    warning: Incomplete
    error: Incomplete
    exception: Incomplete
    min_level: Incomplete
    min_level_no: Incomplete
    monitor_type: Incomplete
    monitor: Incomplete
    def __init__(self, name: str, log_dir: str | None = None, retention: int = 5, monitor_type: Literal['Feishu'] = 'Feishu', prefix: str = '') -> None:
        """
        日志记录器

        :param name: logger名称
        :param log_dir: 输出目录, 无输出目录时不会记录log到文件
        :param retention: 保留天数
        :param monitor_type: 是否启用监控报警
        :param prefix: 日志文件前缀，默认为空
        """

def main() -> None: ...
