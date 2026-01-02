import polars as pl
import types
from _typeshed import Incomplete
from datahub.setting import SftpSetting
from paramiko import SFTPClient as _SFTPClient

__all__ = ['SFTPClient']

class SFTPClient:
    setting: Incomplete
    chmod: Incomplete
    ssh: Incomplete
    sftp: _SFTPClient
    def __init__(self, setting: SftpSetting, chmod: int = 509) -> None:
        '''
        SFTP客户端类，支持上下文管理器模式和普通调用模式
        示例:
        # 作为上下文管理器使用
        >>> with SFTPClient(setting) as sftp:
        ...     print(sftp.listdir("/"))

        # 普通方式使用
        >>> client = SFTPClient(setting)
        >>> client.connect()
        >>> print(client.sftp.listdir("/"))
        >>> client.close()

        :param setting: SFTP连接配置
        :param chmod: 新建文件夹权限设置, 默认为775 (drwxrwxr-x)
        '''
    def ensure_dir(self, dir_path: str, chmod: int = 509) -> bool:
        """
        确保目录存在,递归创建根目录,不存在则创建并设置权限

        :param dir_path: 目录
        :param chmod: 权限, defaults to 0o775
        :return 是否已存在, True为路径已存在无需创建
        """
    def rmdir_recursive(self, path: str):
        """
        递归删除目录及其子目录和文件

        :param path: 目录路径
        :return: None
        """
    def read_df(self, remote_dir: str, pattern: str) -> pl.DataFrame:
        """
        读取远程parquet文件

        :param remote_dir: 远程文件夹路径
        :param pattern: 文件名匹配模式，支持正则， 如: data_2024*.parquet, *.parquet
        (https://docs.python.org/zh-cn/3/library/fnmatch.html)
        :return:
        """
    def connect(self):
        """建立连接并返回sftp客户端"""
    def close(self) -> None:
        """关闭连接"""
    def __enter__(self): ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None: ...
