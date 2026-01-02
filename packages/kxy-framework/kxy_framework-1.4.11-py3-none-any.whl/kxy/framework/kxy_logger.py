from datetime import datetime, timedelta
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
import weakref

import uuid
from logging import Handler

from .util import SUtil
from .DailyRotatingFileHandler import DailyRotatingFileHandler
from .context import trace_id,session_id,seq,user_id,last_log_time
from kxy.framework.DailyRotatingFileHandler import DailyRotatingFileHandler

from .kxy_logger_filter import ConditionOperator, QueryCondition
from .context import last_log_time

class KxyLogger(logging.LoggerAdapter):
    def __init__(self, logger:logging.Logger, extra=None):
        super().__init__(logger, extra or {})
        self.logger = logger
        self.parent = logger.parent
        self.propagate = logger.propagate
        self.handlers = logger.handlers
        self.disabled = logger.disabled
        self.basePath = 'log/app'
        self.file_type = 'log'
        for handler_ref in logging._handlerList:
            handler = handler_ref() if isinstance(handler_ref, weakref.ref) else handler_ref
            if isinstance(handler, DailyRotatingFileHandler):
                self.basePath = handler.base_filename
                self.file_type = handler.file_type

    @staticmethod
    def getLogger(name:str):
        __logger= logging.getLogger(name)
        return KxyLogger(__logger)
    @staticmethod
    def new_trace(traceId=''):
        if not traceId:
            traceId = uuid.uuid4().hex[:16]
        trace_id.set(traceId)
        session_id.set(uuid.uuid4().hex[:16])
        seq.set(0)
        return traceId
    @classmethod
    def init_logger(cls,logLeve,appName,env,filename='log/app',file_type='log',backupCount=5,maxBytes=10485760,mutiple_process=False,cleanup_mode='delete', disk_max=80)->tuple['KxyLogger',Handler]:
        """
            初始化日志处理器实例
            
            Args:
                appName:应用名称
                filename (str): 日志文件名
                file_type (str, optional): 文件类型，默认为'log'
                when (str, optional): 日志轮转时间点，默认为'D', S:秒,M:每分,H:每小时,D:一天,W:每周
                interval (int, optional): 日志轮转间隔，默认为1
                backupCount (int, optional): 保留的备份文件数量，默认为5
                maxBytes (int, optional): 单个日志文件最大字节数，默认为10485760（10MB）
                mutiple_process (bool, optional): 是否支持多进程写入，默认为False
                cleanup_mode (str, optional): 清理模式，默认为'delete'- 删除， 'zip'-压缩
                disk_max (int, optional): 压缩阈值，默认为80，当磁盘超过80%时，立即压缩日志文件，否则在夜间0-6 之间压缩日志
        """
        localIp = SUtil.get_local_ip()
        if '/' not in filename or filename[-1]=='/':
            raise Exception('filename must be like "log/xxx"')
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                # 计算与上次日志的时间间隔
                current_time = time.time()
                prev_time = last_log_time.get()
                duration = current_time - prev_time if prev_time > 0 else 0
                last_log_time.set(current_time)
                logCategory='default'
                if hasattr(record,'logCategory'):
                    logCategory = record.logCategory
                # 构建日志记录的字典
                log_record = {
                    "appName":appName,
                    "serverAddr":os.environ.get('IP',localIp),
                    "cluster": env,
                    "level": record.levelname,
                    "filename": record.filename,
                    "lineno": record.lineno,
                    "traceId": record.trace_id,
                    "sessionId": record.session_id,
                    "userId":record.userid,
                    "seqId": record.seq,
                    "logCategory":logCategory,
                    "message": record.getMessage(),
                    "CreateTime": self.formatTime(record, self.datefmt),
                    "createdOn": int(time.time() * 1000),  # 添加 Unix 时间戳
                    "duration": int(duration * 1000000)  # 添加持续时间，单位毫秒，保留2位小数
                }
                # 将字典转换为 JSON 字符串
                return json.dumps(log_record, ensure_ascii=False)
            
        _logger = logging.getLogger(appName)
        _logger.setLevel(logLeve)
        # 创建一个 RotatingFileHandler 对象
        # 确保 log 目录存在
        if '/' in filename:
            floder = filename.split('/')[0]
            os.makedirs(floder, exist_ok=True)
        handler = DailyRotatingFileHandler(
            filename=filename,
            file_type=file_type,
            when='D',
            interval=300,
            backupCount=backupCount,
            maxBytes=maxBytes,  # 10MB
            mutiple_process = mutiple_process,
            cleanup_mode = cleanup_mode,
            disk_max = disk_max
        )
        formatter = JsonFormatter()

        # 设置日志记录级别
        handler.setLevel(logLeve)
        handler.setFormatter(formatter)
        handler.addFilter(TraceIdFilter())
        
        logging.basicConfig(
            level=logLeve,
            handlers=[handler]
        )
        
        logger = cls(_logger)
        return logger,handler

                  
    def refresh_time(self):
        last_log_time.set(time.time())
    def get_filtered_files(self, start_date=None, end_date=None):
        """
        返回self.basePath目录下的文件列表，只返回文件名称为file_type结尾的文件名
        
        Args:
            start_date (str, optional): 开始日期，格式为'20250815'，默认为当天
            end_date (str, optional): 结束日期，格式为'20250815'，默认为当天
            
        Returns:
            list: 符合条件的文件名列表
        """
        if not os.path.exists(self.basePath):
            return []
        
        # 获取目录下所有文件
        all_files = os.listdir(self.basePath)
        
        # 根据文件后缀过滤
        filtered_files = [f for f in all_files if f.endswith(self.file_type)]
        
        # 如果没有指定日期范围，默认使用当天日期
        if start_date is None and end_date is None:
            today = datetime.now().strftime('%Y%m%d')
            start_date = today
            end_date = today
        # 如果只指定了开始日期，结束日期默认为开始日期
        elif start_date is not None and end_date is None:
            end_date = start_date
        # 如果只指定了结束日期，开始日期默认为结束日期
        elif start_date is None and end_date is not None:
            start_date = end_date
        
        # 将日期字符串转换为整数进行比较
        try:
            start_int = int(start_date)
            end_int = int(end_date)
        except (ValueError, TypeError):
            # 如果日期格式不正确，返回空列表
            return []
        
        date_range_files = []
        date_pattern = r'(\d{8})'
        
        for filename in filtered_files:
            match = re.search(date_pattern, filename)
            if match:
                try:
                    file_date = int(match.group(1))
                    # 检查文件日期是否在指定范围内
                    if start_int <= file_date <= end_int:
                        date_range_files.append(filename)
                except ValueError:
                    # 忽略无法解析为整数的日期
                    continue
        
        return date_range_files
    
    def _add_log_category(self, logLeve, msg, logCategory='default', *args, **kwargs):
        """通用的日志分类添加方法"""
        extra = kwargs.get('extra', {})
        extra["logCategory"] = logCategory
        kwargs['extra'] = extra
        kwargs['stacklevel'] = kwargs.get('stacklevel', 4)

        return self.log(logLeve, msg, *args, **kwargs)

    def info(self, msg, logCategory='default', *args, **kwargs):
        return self._add_log_category(logging.INFO, msg, logCategory, *args, **kwargs)
    
    def debug(self, msg, logCategory='default', *args, **kwargs):
        return self._add_log_category(logging.DEBUG, msg, logCategory, *args, **kwargs)
    
    def warning(self, msg, logCategory='default', *args, **kwargs):
        return self._add_log_category(logging.WARNING, msg, logCategory, *args, **kwargs)
    
    def error(self, msg, logCategory='default', *args, **kwargs):
        return self._add_log_category(logging.ERROR, msg, logCategory, *args, **kwargs)
    
    def critical(self, msg, logCategory='default', *args, **kwargs):
        return self._add_log_category(logging.CRITICAL, msg, logCategory, *args, **kwargs)
    
    def query(self, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None, 
                            filter: QueryCondition = None) -> List[Dict]:
        """
        查询日志内容，根据traceId组织日志结构
        
        Args:
            start_date (str, optional): 开始日期，格式为'YYYY-MM-DD'，默认为当天
            end_date (str, optional): 结束日期，格式为'YYYY-MM-DD'，默认为当天
            conditions (dict, optional): 查询条件字典，用于过滤日志
        
        Returns:
            List[Dict]: 按traceId组织的日志记录列表
        """
        # 确定查询日期范围
        if start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = start_date

        # 将日期字符串转换为datetime对象
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_date == end_date:
            files = self.get_filtered_files(start_date.replace('-', ''))
        else:
            # 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
            start_date_fmt = start_date.replace('-', '')
            end_date_fmt = end_date.replace('-', '')
            files = self.get_filtered_files(start_date=start_date_fmt, end_date=end_date_fmt)

        
        # 存储所有相关日志和traceId映射
        trace_logs = {}  # traceId -> [log_entries]
        matched_logs = []  # 初步匹配的日志
        
        # 第一步：遍历指定日期范围内的所有日志文件
        conditions = []
        if filter:
            conditions = filter.to_dict()

        for filename in files:
            file_path = os.path.join(self.basePath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # 收集所有日志中的traceId
                            trace_id = log_entry.get('traceId', '')
                            if trace_id:
                                if trace_id not in trace_logs:
                                    trace_logs[trace_id] = []
                                trace_logs[trace_id].append(log_entry)
                            
                            # 检查是否符合查询条件
                            if not conditions or self._match_conditions(log_entry, conditions):
                                matched_logs.append(log_entry)
                        except json.JSONDecodeError:
                            # 跳过无效的JSON行
                            continue
            except IOError:
                # 跳过无法读取的文件
                continue
        
        # 第二步：找出匹配日志相关的所有traceId
        related_trace_ids = set()
        for log_entry in matched_logs:
            trace_id = log_entry.get('traceId', '')
            if trace_id:
                related_trace_ids.add(trace_id)
        
        # 第三步：收集所有相关traceId的所有日志（包括其他日期的）
        all_related_logs = []
        for trace_id in related_trace_ids:
            if trace_id in trace_logs:
                all_related_logs.extend(trace_logs[trace_id])
            else:
                # 如果traceId不在当前日期范围内，需要在整个日志目录中查找
                all_files = self.get_filtered_files()  # 获取所有文件
                for filename in all_files:
                    file_path = os.path.join(self.basePath, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    log_entry = json.loads(line.strip())
                                    if log_entry.get('traceId', '') == trace_id:
                                        all_related_logs.append(log_entry)
                                except json.JSONDecodeError:
                                    continue
                    except IOError:
                        continue
        
        # 第四步：重新组织traceId映射
        final_trace_logs = {}
        for log_entry in all_related_logs:
            trace_id = log_entry.get('traceId', '')
            if trace_id not in final_trace_logs:
                final_trace_logs[trace_id] = []
            final_trace_logs[trace_id].append(log_entry)
        
        # 第五步：按seqId组织日志结构
        result = []
        for trace_id, logs in final_trace_logs.items():
            # 按seqId排序
            logs.sort(key=lambda x: x.get('seqId', 0))
            
            # 找到seqId为1的首行日志
            head_log = None
            children_logs = []
            
            for log in logs:
                if log.get('seqId', 0) == 1:
                    head_log = log
                else:
                    children_logs.append(log)
            
            # 构造返回结构
            if head_log:
                head_log['children'] = children_logs
                result.append(head_log)
            else:
                # 如果没有找到seqId为1的日志，则将第一个作为首行
                if logs:
                    head_log = logs[0]
                    head_log['children'] = logs[1:]
                    result.append(head_log)
        
        return result

    def _match_conditions(self, log_entry: Dict, conditions: Dict[str, Any]) -> bool:
        """
        检查日志条目是否符合给定条件，支持多种比较操作
        
        Args:
            log_entry (Dict): 日志条目
            conditions (Dict): 查询条件，支持以下操作符：
                - 默认(直接比较): {'level': 'ERROR'}
                - 大于: {'seqId': {ConditionOperator.GREATER_THAN: 10}}
                - 小于: {'seqId': {ConditionOperator.LESS_THAN: 100}}
                - 不等于: {'level': {ConditionOperator.NOT_EQUAL: 'DEBUG'}}
                - 包含: {'message': {ConditionOperator.CONTAINS: 'error'}}
            
        Returns:
            bool: 是否匹配
        """
        for key, condition in conditions.items():
            # 如果字段不存在于日志条目中，不匹配
            if key not in log_entry:
                return False
                
            log_value = log_entry[key]
            
            # 处理不同的条件类型
            if isinstance(condition, dict):
                # 处理操作符条件
                for op, value in condition.items():
                    # 支持字符串和枚举形式的操作符
                    op_value = op.value if isinstance(op, ConditionOperator) else op
                    
                    if op_value == ConditionOperator.GREATER_THAN.value:  # 大于
                        if not (log_value > value):
                            return False
                    elif op_value == ConditionOperator.LESS_THAN.value:  # 小于
                        if not (log_value < value):
                            return False
                    elif op_value == ConditionOperator.NOT_EQUAL.value:  # 不等于
                        if not (log_value != value):
                            return False
                    elif op_value == ConditionOperator.CONTAINS.value:  # 包含
                        if not isinstance(log_value, str) or value not in log_value:
                            return False
                    else:
                        # 不支持的操作符
                        return False
            else:
                # 默认相等比较
                if log_value != condition:
                    return False
                    
        return True

class VirtualLogger():
    def refresh_time(self):
        pass
    def info(self, msg, logCategory='default', *args, **kwargs):
        pass
    
    def debug(self, msg, logCategory='default', *args, **kwargs):
        pass
    
    def warning(self, msg, logCategory='default', *args, **kwargs):
        pass
    
    def error(self, msg, logCategory='default', *args, **kwargs):
        pass
    
class TraceIdFilter(logging.Filter):
    def filter(self, record):
        traceId = trace_id.get()
        if not traceId:
            traceId = KxyLogger.new_trace()
        record.trace_id = traceId
        record.session_id = session_id.get()
        record.userid = user_id.get()
        last_log_time.set(time.time())
        cur_seq = seq.get()
        record.seq = cur_seq
        seq.set(cur_seq+1)
        return True