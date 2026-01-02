# coding=UTF-8

from .friendly_exception import FriendlyException
from .base_config import BaseConfig, IdGeneratorType
from .id_generator import SnowflakeIDGenerator
from .config_manager import ConfigManager
from kxy_open_id_client import SegmentClient, IdGeneratorFactory


# ID 生成器相关的全局变量（延迟初始化）
_id_generator_factory = None
_idgenerator = None
_initialized = False


def _ensure_initialized():
    """
    确保 ID 生成器已经初始化
    使用延迟初始化策略，允许用户在导入后、使用前设置自定义配置
    """
    global _id_generator_factory, _idgenerator, _initialized

    if _initialized:
        return

    config:BaseConfig = ConfigManager.get_config()

    if config.ID_GENERATOR_TYPE == IdGeneratorType.OPEN_ID_CLIENT:
        if SegmentClient is None or IdGeneratorFactory is None:
            raise ImportError(
                "kxy_open_id_client module is not installed. "
                "Please install it to use 'open_id_client' ID generator type, "
                "or change ID_GENERATOR_TYPE to 'snowflake'."
            )

        if not config.OPEN_ID_SERVER_URL:
            raise ValueError("OPEN_ID_CLIENT_URL must be set when ID_GENERATOR_TYPE is 'open_id_client'")

        _segment_client = SegmentClient(
            base_url=config.OPEN_ID_SERVER_URL,verify_ssl=False
        )
        _id_generator_factory = IdGeneratorFactory(
            _segment_client,
            config.SystemCode,
            config.database_name
        )
    else:
        # 默认使用雪花算法
        _idgenerator = SnowflakeIDGenerator()

    _initialized = True
class BaseEntity():

    InsertOtherFields = []
    InsertRequireFields = []
    UpdateFiles = []
    __AutoId__ = True
    def setId(self):
        # 确保 ID 生成器已初始化
        _ensure_initialized()

        config:BaseConfig = ConfigManager.get_config()

        if config.ID_GENERATOR_TYPE == IdGeneratorType.OPEN_ID_CLIENT:
            # 使用 open_id_client 生成器
            table_name = getattr(self.__class__, '__tablename__', 'default')
            next_id = _id_generator_factory.get_generator(table_name).next_id()
            if self._id_type == 'str':
                self.Id = str(next_id)
            else:
                self.Id = next_id
        else:
            # 使用雪花算法
            if self._id_type == 'str':
                self.Id = str(_idgenerator.get_next_id())
            else:
                self.Id = _idgenerator.get_next_id()
    def __init__(self,id_type='str',auto_id=True):
        '''
        id_type: str or int,指定Id的数据类型
        auto_id: 是否自动生成id
        '''
        self._id_type = id_type
        self.__AutoId__ = auto_id
        if self.__AutoId__:
            self.setId()
    def init_with_dict(self,fields):
        for field,value in fields.items():
            setattr(self, field, value)
        return self

    # 插入字段
    def InitInsertEntityWithJson(self, json_data):
        self.__init_require__(json_data, self.InsertRequireFields)
        self.__init_fileds__(json_data, self.InsertOtherFields)
        if self.__AutoId__ and not self.Id:
            self.setId()

    # 更新字段
    def InitUpdateFiles(self, json_data):
        self.__init_fileds__(json_data, self.UpdateFiles)
        self.__init_fileds__(json_data, self.InsertRequireFields)
        self.__init_fileds__(json_data, self.InsertOtherFields)

    def __init_fileds__(self, json_data, fields):
        for field in fields:
            value = json_data.get(field, None)
            if value is not None:
                setattr(self, field, value)

    def __init_require__(self, json_data, fields):
        for field in fields:
            value = json_data.get(field, None)
            if value is None:
                raise FriendlyException(field+' can not empty')
            setattr(self, field, value)

    def toDic(self):
        result = {}
        for name, value in vars(self).items():
            if name != '_sa_instance_state':
                result[name] = value
        return result


from sqlalchemy.types import TypeDecorator, VARCHAR
import json
class JSONString(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        # 保存到数据库时，自动转为字符串
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        # 查询出来时，自动转为 dict
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value