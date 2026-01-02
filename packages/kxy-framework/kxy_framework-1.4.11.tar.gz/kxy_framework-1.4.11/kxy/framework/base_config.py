import os
from abc import ABC, abstractmethod
from enum import Enum
from urllib.parse import urlparse


class IdGeneratorType(str, Enum):
    """ID生成器类型枚举"""
    SNOWFLAKE = 'snowflake'
    OPEN_ID_CLIENT = 'open_id_client'


class BaseConfig(ABC):
    BussinessLog = False

    # ID生成器配置
    ID_GENERATOR_TYPE = IdGeneratorType.SNOWFLAKE  # IdGeneratorType.SNOWFLAKE 或 IdGeneratorType.OPEN_ID_CLIENT
    OPEN_ID_SERVER_URL = None  # open_id_server的地址，例如: 'http://localhost:8080'
    OPEN_ID_CLIENT_SEGMENT_SIZE = 1000  # 默认号段大小
    DATABASE_NAME = None  # 数据库名称
    mysql_url = ''

    @abstractmethod
    def SSO_URL(self):
        pass

    @abstractmethod
    def SystemCode(self):
        pass
    @abstractmethod
    def JWT_SECRET_KEY(self):
        pass
    @abstractmethod
    def JWT_ALGORITHM(self):
        pass

    def env_first(self):
        for name in [f for f in dir(self) if not callable(f) and not f.startswith('__')]:
            v=os.environ.get(name)
            if v:
                setattr(self, name, v)

    def get_database_name_from_url(self) -> str:
        """
        从 mysql_url 中解析出数据库名称

        支持的 URL 格式:
        - mysql://user:password@host:port/database
        - mysql+pymysql://user:password@host:port/database
        - mysql+aiomysql://user:password@host:port/database

        Returns:
            str: 数据库名称，如果解析失败则返回 DATABASE_NAME 的值

        Examples:
            >>> config.mysql_url = "mysql+aiomysql://root:123456@localhost:3306/my_database"
            >>> config.get_database_name_from_url()
            'my_database'
        """
        try:
            parsed = urlparse(self.mysql_url)
            # path 格式为 '/database_name' 或 '/database_name?params'
            self.DATABASE_NAME = parsed.path.lstrip('/')
            # 如果有查询参数，只取数据库名称部分
            if '?' in self.DATABASE_NAME:
                self.DATABASE_NAME = self.DATABASE_NAME.split('?')[0]

            return self.DATABASE_NAME
        except Exception:
            return self.DATABASE_NAME

    @property
    def database_name(self) -> str:
        """
        获取数据库名称的属性
        优先从 mysql_url 中解析，如果解析失败则使用 DATABASE_NAME
        """
        if self.DATABASE_NAME:
            return self.DATABASE_NAME
        else:
            return self.get_database_name_from_url()