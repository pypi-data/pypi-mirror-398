import httpx
from kxy.framework.context import trace_id, session_id, user_id, access_token
from kxy.framework.base_config import BaseConfig
from kxy.framework.__logger import kxyLogger
class HttpClient:
    @staticmethod
    def get_default_headers():
        headers = {
            'x-trace-id': trace_id.get(),
        }
        
        # 只有当access_token存在且非空时才添加Authorization头部
        token = access_token.get()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        return headers
        
    
    @classmethod
    async def request(cls, method, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers.update(cls.get_default_headers())
        try:
            async with httpx.AsyncClient() as client:
                result = await client.request(method, url, headers=headers, **kwargs)
                kxyLogger.info(f'{method} {url} success {result.status_code}',extra={'Category':'http'})
                return result
        except Exception as ex:
            kxyLogger.error(f'{method} {url} error:{ex}',extra={'Category':'http'})
            raise ex
    
    @classmethod
    async def get(cls, url, **kwargs):
        return await cls.request('GET', url, **kwargs)
    
    @classmethod
    async def post(cls, url, **kwargs):
        return await cls.request('POST', url, **kwargs)
    
    @classmethod
    async def put(cls, url, **kwargs):
        return await cls.request('PUT', url, **kwargs)
    
    @classmethod
    async def delete(cls, url, **kwargs):
        return await cls.request('DELETE', url, **kwargs)
    # 新增支持 async with as 语法的客户端方法
    @classmethod
    def async_client(cls):
        """
        创建一个封装了默认 headers 的异步客户端，支持 async with 语法
        使用示例:
        async with HttpClient.async_client() as client:
            response = await client.get(url)
        """
        return _HttpClientWrapper()
    

class _HttpClientWrapper:
    """
    HttpClient 的异步客户端包装器，用于支持 async with 语法
    """
    async def __aenter__(self):
        # 创建 httpx.AsyncClient 实例并添加默认 headers
        self._client = httpx.AsyncClient()
        # 更新客户端的默认 headers
        default_headers = HttpClient.get_default_headers()
        self._client.headers.update(default_headers)
        await self._client.__aenter__()
        return self._client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 退出时清理资源
        return await self._client.__aexit__(exc_type, exc_val, exc_tb)