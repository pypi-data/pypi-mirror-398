import asyncio
import logging
import random
import sys
import os
import time

# 正确添加项目根路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from kxy.framework.date_util import DateUtil

print(DateUtil.in_hour('17:22-23:25'))