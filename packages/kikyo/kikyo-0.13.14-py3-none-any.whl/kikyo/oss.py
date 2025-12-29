from abc import ABCMeta, abstractmethod
from typing import Any


class Bucket(metaclass=ABCMeta):

    @abstractmethod
    def get_object_link(self, key: str) -> str:
        """
        获取对象的下载链接

        :param key: 对象的名称
        """

    @abstractmethod
    def put_object(self, key: str, data: Any):
        """
        上传对象

        :param key: 对象的名称
        :param data: 对象数据
        """

    @abstractmethod
    def get_object(self, key: str) -> Any:
        """
        下载对象

        :param key: 对象的名称
        :return: 对象数据
        """

    @abstractmethod
    def object_exists(self, key: str) -> bool:
        """
        检查对象是否存在

        :param key: 对象的名称
        :return: 是否存在
        """

    @abstractmethod
    def remove_object(self, key: str):
        """
        删除对象

        :param key: 对象的名称
        """


class OSS(metaclass=ABCMeta):
    """
    提供对象存储服务
    """

    @abstractmethod
    def bucket(self, name: str) -> Bucket:
        """
        获取bucket

        :param name: bucket名称
        """
