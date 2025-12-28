import aiohttp
from typing import Dict, Any, Tuple


class AsyncClient:
    def __init__(self, api_key: str):
        """
        description:
            初始化异步客户端
        parameters:
            api_key(str): API密钥，用于身份验证
        """
        self.base_url = "https://thirdparty.pixelarrayai.com"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    async def _request(
        self, method: str, url: str, **kwargs
    ) -> Tuple[Dict[str, Any], bool]:
        """
        description:
            发送异步HTTP请求的通用方法
        parameters:
            method(str): HTTP方法，如"GET"、"POST"、"PUT"、"DELETE"等
            url(str): 请求URL路径（相对于base_url）
            **kwargs: 其他请求参数，如json、params、headers等
        return:
            data(Dict[str, Any]): 响应数据字典，如果请求失败则返回空字典
            success(bool): 请求是否成功
        """
        # 如果kwargs中有headers，则合并headers
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            kwargs = {k: v for k, v in kwargs.items() if k != "headers"}

        async with aiohttp.ClientSession() as session:
            req_method = getattr(session, method.lower())
            async with req_method(
                f"{self.base_url}{url}", headers=headers, **kwargs
            ) as resp:
                if resp.status == 200:
                    try:
                        result = await resp.json()
                        if result.get("success") is True:
                            return result.get("data", {}), True
                    except:
                        # 如果不是JSON响应，返回空
                        pass
                return {}, False

    async def _request_raw(
        self, method: str, url: str, **kwargs
    ) -> Tuple[int, Dict[str, Any]]:
        """
        description:
            发送异步HTTP请求的原始方法，返回完整的HTTP状态码和响应数据
        parameters:
            method(str): HTTP方法，如"GET"、"POST"、"PUT"、"DELETE"等
            url(str): 请求URL路径（相对于base_url）
            **kwargs: 其他请求参数，如json、params、headers等
        return:
            status_code(int): HTTP状态码
            data(Dict[str, Any]): 响应数据字典，如果解析失败则返回空字典
        """
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            kwargs = {k: v for k, v in kwargs.items() if k != "headers"}

        async with aiohttp.ClientSession() as session:
            req_method = getattr(session, method.lower())
            async with req_method(
                f"{self.base_url}{url}", headers=headers, **kwargs
            ) as resp:
                try:
                    data = await resp.json()
                except:
                    data = {}
                return resp.status, data
