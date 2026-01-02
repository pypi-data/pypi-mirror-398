import logging
import random
import sys
import os
import time

# 正确添加项目根路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from kxy.framework.kxy_logger import KxyLogger

KxyLogger.init_logger(logging.DEBUG,'kxy.mall.api','production',filename='log/app',file_type='log',backupCount=5,maxBytes=10000,mutiple_process=False,cleanup_mode='zip',disk_max=1)
logger = KxyLogger.getLogger('sdfsfsdf')
# logger = logging.getLogger(__name__)


logger.info('hello world1',extra={"logCategory":'http'})
for i in range(20):
    # time.sleep(random.randint(2,5))
    # logger.info(f'hello world {i}')
    logger.info(f'hello world {i}',extra={"logCategory":'grpc'})