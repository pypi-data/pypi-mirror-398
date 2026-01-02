# coding=UTF-8

from typing import Type, Optional


class ConfigManager:
    """
    配置管理器，用于管理框架的全局配置

    使用方式：
    1. 创建自定义配置类继承 BaseConfig
    2. 在应用启动时调用 ConfigManager.set_config(YourConfig) 设置配置
    3. 框架内部通过 ConfigManager.get_config() 获取配置

    示例：
        from kxy.framework import ConfigManager
        from kxy.framework.base_config import BaseConfig

        class MyConfig(BaseConfig):
            ID_GENERATOR_TYPE = 'open_id_client'
            OPEN_ID_CLIENT_URL = 'http://localhost:8080'

            def SSO_URL(self):
                return 'http://sso.example.com'
            # ... 实现其他抽象方法

        # 在导入其他框架模块之前设置配置
        ConfigManager.set_config(MyConfig)

        # 然后导入和使用框架其他模块
        from kxy.framework import BaseEntity
    """

    _config_class: Optional[Type] = None

    @classmethod
    def get_config(cls) -> Type:
        """
        获取当前配置类

        Returns:
            配置类（注意：返回的是类，不是实例）
        """
        if cls._config_class is None:
            from .base_config import BaseConfig
            return BaseConfig
        return cls._config_class

    @classmethod
    def set_config(cls, config_class: Type) -> None:
        """
        设置自定义配置类

        Args:
            config_class: 配置类（必须继承自 BaseConfig）

        注意：
            必须在导入 base_entity、base_dal 等模块之前调用此方法
            如果在这些模块已经被导入后调用，需要手动调用 reset_framework() 重置框架状态
        """
        cls._config_class = config_class

    @classmethod
    def reset(cls) -> None:
        """
        重置配置管理器到默认状态

        主要用于测试场景
        """
        cls._config_class = None
