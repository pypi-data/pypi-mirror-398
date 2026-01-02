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
    
from kxy.framework.redis_client import RedisClient
redis_client = RedisClient('127.0.0.1',6379,None,0,'test')
async def query():
    await redis_client.set('test', 'test')
    print(await redis_client.get_string('test'))
    await redis_client.set_json('test', {'test':'test'})
    print(await redis_client.get_json('test'))
    await redis_client.set('test', 1)
    print(await redis_client.get_int('test'))
    
loop:asyncio.AbstractEventLoop = asyncio.new_event_loop()
# loop.run_until_complete(test_table_add())
loop.run_until_complete(query())