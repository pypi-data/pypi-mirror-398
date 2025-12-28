import asyncio
import urllib.parse
import webbrowser
from typing import Dict, Optional, Tuple

from pixelarraythirdparty.client import AsyncClient


class OAuth2Login(AsyncClient):
    """
    统一的 OAuth2 登录客户端基类
    
    支持所有基于 OAuth2 的第三方登录（Google、微信、GitHub、GitLab、抖音等）
    通过配置不同的端点来支持不同的提供商
    
    使用示例:
    ```
    # Google登录
    google = OAuth2Login(
        api_key="your_api_key",
        provider="google"
    )
    user_info, success = await google.login()
    
    # 微信PC端扫码登录
    wechat = OAuth2Login(
        api_key="your_api_key",
        provider="wechat",
        login_type="desktop"
    )
    user_info, success = await wechat.login()
    
    # 微信手机端登录
    wechat_mobile = OAuth2Login(
        api_key="your_api_key",
        provider="wechat",
        login_type="mobile"
    )
    user_info, success = await wechat_mobile.login()
    
    # 支持refresh_token的提供商（如Google、GitLab）
    if user_info.get("refresh_token"):
        token_data, success = await google.refresh_access_token(
            user_info.get("refresh_token")
        )
    ```
    """
    
    # 提供商端点映射
    PROVIDER_ENDPOINTS = {
        "google": {
            "auth_url": "/api/unified-login/google/auth-url",
            "wait_login": "/api/unified-login/google/wait-login",
            "refresh_token": "/api/unified-login/google/refresh-token",
        },
        "wechat": {
            "auth_url": "/api/unified-login/wechat/auth-url",
            "wait_login": "/api/unified-login/wechat/wait-login",
        },
        "wechat-official": {
            "auth_url": "/api/unified-login/wechat-official/auth-url",
            "wait_login": "/api/unified-login/wechat-official/wait-login",
        },
        "github": {
            "auth_url": "/api/unified-login/github/auth-url",
            "wait_login": "/api/unified-login/github/wait-login",
        },
        "gitlab": {
            "auth_url": "/api/unified-login/gitlab/auth-url",
            "wait_login": "/api/unified-login/gitlab/wait-login",
            "refresh_token": "/api/unified-login/gitlab/refresh-token",
        },
        "douyin": {
            "auth_url": "/api/unified-login/douyin/auth-url",
            "wait_login": "/api/unified-login/douyin/wait-login",
        },
    }
    
    def __init__(
        self,
        api_key: str,
        provider: str,
        login_type: Optional[str] = None
    ):
        """
        description:
            初始化OAuth2登录客户端
        parameters:
            api_key(str): API密钥
            provider(str): 提供商名称，可选值：google, wechat, github, gitlab, douyin
            login_type(str, optional): 登录类型，仅对微信有效，可选值：desktop（PC端扫码）, mobile（手机端）
        """
        super().__init__(api_key)
        self.provider = provider.lower()
        self.login_type = login_type
        
        # 验证提供商是否支持
        if self.provider not in self.PROVIDER_ENDPOINTS:
            raise ValueError(
                f"不支持的提供商: {provider}。"
                f"支持的提供商: {', '.join(self.PROVIDER_ENDPOINTS.keys())}"
            )
        
        # 微信特殊处理：根据login_type选择不同的端点
        if self.provider == "wechat":
            if login_type == "mobile":
                self.provider = "wechat-official"
    
    def _get_endpoint(self, endpoint_type: str) -> str:
        """
        description:
            获取指定类型的端点URL
        parameters:
            endpoint_type(str): 端点类型，可选值：auth_url, wait_login, refresh_token
        return:
            endpoint(str): 端点URL
        """
        endpoints = self.PROVIDER_ENDPOINTS.get(self.provider, {})
        endpoint = endpoints.get(endpoint_type)
        if not endpoint:
            raise ValueError(
                f"提供商 {self.provider} 不支持 {endpoint_type} 端点"
            )
        return endpoint
    
    async def _get_auth_url(self) -> Tuple[Optional[Dict[str, str]], bool]:
        """
        description:
            获取OAuth授权URL
        return:
            auth_data(dict, optional): 授权数据字典，包含auth_url和state
            success(bool): 是否成功
        """
        endpoint = self._get_endpoint("auth_url")
        data, success = await self._request("POST", endpoint)
        if not success:
            return None, False
        auth_url = data.get("auth_url")
        if not auth_url:
            return None, False
        return data, True
    
    def _extract_state(self, auth_url: Optional[str]) -> Optional[str]:
        """
        description:
            从授权URL中提取state参数
        parameters:
            auth_url(str, optional): 授权URL
        return:
            state(str, optional): state参数值，如果提取失败则返回None
        """
        if not auth_url:
            return None
        try:
            parsed = urllib.parse.urlparse(auth_url)
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("state")
            if values:
                return values[0]
        except Exception:
            return None
        return None
    
    async def _wait_for_login(
        self, state: str, timeout: int
    ) -> Tuple[Dict, bool]:
        """
        description:
            等待登录结果，轮询检查登录状态
        parameters:
            state(str): 登录状态标识
            timeout(int): 超时时间（秒）
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1
        endpoint = self._get_endpoint("wait_login")
        
        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                endpoint,
                json={"state": state},
            )
            
            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True
            
            if status in (400, 408):
                break
            
            await asyncio.sleep(interval)
        
        return {}, False
    
    async def login(self, timeout: int = 180) -> Tuple[Dict, bool]:
        """
        description:
            仿 Supabase CLI 的一键登录流程：打开浏览器完成授权，终端端轮询等待登录结果
        parameters:
            timeout(int, optional): 等待用户完成授权的超时时间（秒），默认为180
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        auth_data, success = await self._get_auth_url()
        if not success or not auth_data:
            return {}, False
        
        auth_url = auth_data.get("auth_url")
        state = auth_data.get("state") or self._extract_state(auth_url)
        
        if not auth_url or not state:
            return {}, False
        
        webbrowser.open(auth_url, new=2)
        
        return await self._wait_for_login(state, timeout)
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[Dict, bool]:
        """
        description:
            使用refresh_token刷新access_token（仅支持Google和GitLab）
            
            注意：GitLab 采用 token rotation（令牌轮换）机制，每次刷新时会返回新的 refresh_token，
            旧的 refresh_token 会立即失效。必须保存新的 refresh_token 并替换旧的。
            Google 也可能在某些情况下返回新的 refresh_token。
        parameters:
            refresh_token(str): OAuth refresh_token
        return:
            token_data(dict): 包含新的access_token和可能的refresh_token的字典
            success(bool): 是否成功
        """
        try:
            endpoint = self._get_endpoint("refresh_token")
        except ValueError:
            return {}, False
        
        data, success = await self._request(
            "POST",
            endpoint,
            json={"refresh_token": refresh_token},
        )
        if not success:
            return {}, False
        return data, True


class GoogleLogin(AsyncClient):
    """
    Google OAuth2 登录客户端

    使用示例:
    ```
    google = GoogleLogin(api_key="your_api_key")
    user_info, success = await google.login()
    if success:
        access_token = user_info.get("access_token")
        refresh_token = user_info.get("refresh_token")
        
        # 使用refresh_token刷新access_token
        if refresh_token:
            token_data, success = await google.refresh_access_token(refresh_token)
            if success:
                new_access_token = token_data.get("access_token")
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def _get_auth_url(self) -> Tuple[Optional[Dict[str, str]], bool]:
        """
        description:
            获取Google OAuth授权URL
        return:
            auth_data(dict, optional): 授权数据字典，包含auth_url和state
            success(bool): 是否成功
        """
        data, success = await self._request(
            "POST", "/api/unified-login/google/auth-url"
        )
        if not success:
            return None, False
        auth_url = data.get("auth_url")
        if not auth_url:
            return None, False
        return data, True

    async def login(self, timeout: int = 180) -> Tuple[Dict, bool]:
        """
        description:
            仿 Supabase CLI 的一键登录流程：打开浏览器完成授权，终端端轮询等待登录结果
        parameters:
            timeout(int, optional): 等待用户完成授权的超时时间（秒），默认为180
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        auth_data, success = await self._get_auth_url()
        if not success or not auth_data:
            return {}, False

        auth_url = auth_data.get("auth_url")
        state = auth_data.get("state") or self._extract_state(auth_url)

        if not auth_url or not state:
            return {}, False

        webbrowser.open(auth_url, new=2)

        return await self._wait_for_google_login(state, timeout)

    def _extract_state(self, auth_url: Optional[str]) -> Optional[str]:
        if not auth_url:
            return None
        try:
            parsed = urllib.parse.urlparse(auth_url)
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("state")
            if values:
                return values[0]
        except Exception:
            return None
        return None

    async def _wait_for_google_login(
        self, state: str, timeout: int
    ) -> Tuple[Dict, bool]:
        """
        description:
            等待Google登录结果，轮询检查登录状态
        parameters:
            state(str): 登录状态标识
            timeout(int): 超时时间（秒）
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                "/api/unified-login/google/wait-login",
                json={"state": state},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False

    async def refresh_access_token(self, refresh_token: str) -> Tuple[Dict, bool]:
        """
        description:
            使用refresh_token刷新access_token
        parameters:
            refresh_token(str): Google OAuth refresh_token
        return:
            token_data(dict): 包含新的access_token和可能的refresh_token的字典
            success(bool): 是否成功
        """
        data, success = await self._request(
            "POST",
            "/api/unified-login/google/refresh-token",
            json={"refresh_token": refresh_token},
        )
        if not success:
            return {}, False
        return data, True


class WechatLogin(AsyncClient):
    """
    微信 OAuth2 登录客户端
    
    支持两种登录方式：
    - desktop: PC端扫码登录（使用微信开放平台）
    - mobile: 微信公众号OAuth登录（手机端微信内打开）

    使用示例:
    ```
    wechat = WechatLogin(api_key="your_api_key")
    # PC端扫码登录
    user_info, success = await wechat.login(login_type="desktop")
    # 微信公众号登录（手机端）
    user_info, success = await wechat.login(login_type="mobile")
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def _get_auth_url(self, login_type: str = "desktop") -> Tuple[Optional[Dict[str, str]], bool]:
        """
        description:
            获取微信授权URL
        parameters:
            login_type(str, optional): 登录类型，desktop表示PC端扫码登录，mobile表示微信公众号登录，默认为desktop
        return:
            auth_data(dict, optional): 授权数据字典，包含auth_url和state
            success(bool): 是否成功
        """
        if login_type == "mobile":
            # 微信公众号OAuth登录（手机端）
            endpoint = "/api/unified-login/wechat-official/auth-url"
        else:
            # PC端扫码登录
            endpoint = "/api/unified-login/wechat/auth-url"
        
        data, success = await self._request("POST", endpoint)
        if not success:
            return None, False
        auth_url = data.get("auth_url")
        if not auth_url:
            return None, False
        return data, True

    async def login(self, login_type: str = "desktop", timeout: int = 180) -> Tuple[Dict, bool]:
        """
        description:
            仿 Supabase CLI 的一键登录流程：打开浏览器完成授权，终端端轮询等待登录结果
        parameters:
            login_type(str, optional): 登录类型，desktop表示PC端扫码登录，mobile表示微信公众号登录，默认为desktop
            timeout(int, optional): 等待用户完成授权的超时时间（秒），默认为180
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        auth_data, success = await self._get_auth_url(login_type)
        if not success or not auth_data:
            return {}, False

        auth_url = auth_data.get("auth_url")
        state = auth_data.get("state") or self._extract_state(auth_url)

        if not auth_url or not state:
            return {}, False

        webbrowser.open(auth_url, new=2)

        return await self._wait_for_wechat_login(state, timeout, login_type)

    def _extract_state(self, auth_url: Optional[str]) -> Optional[str]:
        """
        description:
            从授权URL中提取state参数
        parameters:
            auth_url(str, optional): 授权URL
        return:
            state(str, optional): state参数值，如果提取失败则返回None
        """
        if not auth_url:
            return None
        try:
            parsed = urllib.parse.urlparse(auth_url)
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("state")
            if values:
                return values[0]
        except Exception:
            return None
        return None

    async def _wait_for_wechat_login(
        self, state: str, timeout: int, login_type: str = "desktop"
    ) -> Tuple[Dict, bool]:
        """
        description:
            等待微信登录结果，轮询检查登录状态
        parameters:
            state(str): 登录状态标识
            timeout(int): 超时时间（秒）
            login_type(str, optional): 登录类型，desktop表示PC端扫码登录，mobile表示微信公众号登录，默认为desktop
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        # 根据登录类型选择不同的等待接口
        if login_type == "mobile":
            endpoint = "/api/unified-login/wechat-official/wait-login"
        else:
            endpoint = "/api/unified-login/wechat/wait-login"

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                endpoint,
                json={"state": state},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False


class GitHubLogin(AsyncClient):
    """
    GitHub OAuth2 登录客户端

    使用示例:
    ```
    github = GitHubLogin(api_key="your_api_key")
    user_info, success = await github.login()
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def _get_auth_url(self) -> Tuple[Optional[Dict[str, str]], bool]:
        """
        description:
            获取GitHub OAuth授权URL
        return:
            auth_data(dict, optional): 授权数据字典，包含auth_url和state
            success(bool): 是否成功
        """
        data, success = await self._request(
            "POST", "/api/unified-login/github/auth-url"
        )
        if not success:
            return None, False
        auth_url = data.get("auth_url")
        if not auth_url:
            return None, False
        return data, True

    async def login(self, timeout: int = 180) -> Tuple[Dict, bool]:
        """
        description:
            仿 Supabase CLI 的一键登录流程：打开浏览器完成授权，终端端轮询等待登录结果
        parameters:
            timeout(int, optional): 等待用户完成授权的超时时间（秒），默认为180
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        auth_data, success = await self._get_auth_url()
        if not success or not auth_data:
            return {}, False

        auth_url = auth_data.get("auth_url")
        state = auth_data.get("state") or self._extract_state(auth_url)

        if not auth_url or not state:
            return {}, False

        webbrowser.open(auth_url, new=2)

        return await self._wait_for_github_login(state, timeout)

    def _extract_state(self, auth_url: Optional[str]) -> Optional[str]:
        """
        description:
            从授权URL中提取state参数
        parameters:
            auth_url(str, optional): 授权URL
        return:
            state(str, optional): state参数值，如果提取失败则返回None
        """
        if not auth_url:
            return None
        try:
            parsed = urllib.parse.urlparse(auth_url)
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("state")
            if values:
                return values[0]
        except Exception:
            return None
        return None

    async def _wait_for_github_login(
        self, state: str, timeout: int
    ) -> Tuple[Dict, bool]:
        """
        description:
            等待GitHub登录结果，轮询检查登录状态
        parameters:
            state(str): 登录状态标识
            timeout(int): 超时时间（秒）
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                "/api/unified-login/github/wait-login",
                json={"state": state},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False


class DouyinLogin(AsyncClient):
    """
    抖音 OAuth2 登录客户端

    使用示例:
    ```
    douyin = DouyinLogin(api_key="your_api_key")
    user_info, success = await douyin.login()
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def _get_auth_url(self) -> Tuple[Optional[Dict[str, str]], bool]:
        """
        description:
            获取抖音OAuth授权URL
        return:
            auth_data(dict, optional): 授权数据字典，包含auth_url和state
            success(bool): 是否成功
        """
        data, success = await self._request(
            "POST", "/api/unified-login/douyin/auth-url"
        )
        if not success:
            return None, False
        auth_url = data.get("auth_url")
        if not auth_url:
            return None, False
        return data, True

    async def login(self, timeout: int = 180) -> Tuple[Dict, bool]:
        """
        description:
            仿 Supabase CLI 的一键登录流程：打开浏览器完成授权，终端端轮询等待登录结果
        parameters:
            timeout(int, optional): 等待用户完成授权的超时时间（秒），默认为180
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        auth_data, success = await self._get_auth_url()
        if not success or not auth_data:
            return {}, False

        auth_url = auth_data.get("auth_url")
        state = auth_data.get("state") or self._extract_state(auth_url)

        if not auth_url or not state:
            return {}, False

        webbrowser.open(auth_url, new=2)

        return await self._wait_for_douyin_login(state, timeout)

    def _extract_state(self, auth_url: Optional[str]) -> Optional[str]:
        """
        description:
            从授权URL中提取state参数
        parameters:
            auth_url(str, optional): 授权URL
        return:
            state(str, optional): state参数值，如果提取失败则返回None
        """
        if not auth_url:
            return None
        try:
            parsed = urllib.parse.urlparse(auth_url)
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("state")
            if values:
                return values[0]
        except Exception:
            return None
        return None

    async def _wait_for_douyin_login(
        self, state: str, timeout: int
    ) -> Tuple[Dict, bool]:
        """
        description:
            等待抖音登录结果，轮询检查登录状态
        parameters:
            state(str): 登录状态标识
            timeout(int): 超时时间（秒）
        return:
            user_info(dict): 用户信息字典
            success(bool): 是否成功
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                "/api/unified-login/douyin/wait-login",
                json={"state": state},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False


class GitLabLogin(AsyncClient):
    """
    GitLab OAuth2 登录客户端

    使用示例:
    ```
    gitlab = GitLabLogin(api_key="your_api_key")
    user_info, success = await gitlab.login()
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def _get_auth_url(self) -> Tuple[Optional[Dict[str, str]], bool]:
        data, success = await self._request(
            "POST", "/api/unified-login/gitlab/auth-url"
        )
        if not success:
            return None, False
        auth_url = data.get("auth_url")
        if not auth_url:
            return None, False
        return data, True

    async def login(self, timeout: int = 180) -> Tuple[Dict, bool]:
        """
        仿 Supabase CLI 的一键登录流程：打开浏览器完成授权，
        终端端轮询等待登录结果

        :param timeout: 等待用户完成授权的超时时间（秒）
        """
        auth_data, success = await self._get_auth_url()
        if not success or not auth_data:
            return {}, False

        auth_url = auth_data.get("auth_url")
        state = auth_data.get("state") or self._extract_state(auth_url)

        if not auth_url or not state:
            return {}, False

        webbrowser.open(auth_url, new=2)

        return await self._wait_for_gitlab_login(state, timeout)

    def _extract_state(self, auth_url: Optional[str]) -> Optional[str]:
        if not auth_url:
            return None
        try:
            parsed = urllib.parse.urlparse(auth_url)
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("state")
            if values:
                return values[0]
        except Exception:
            return None
        return None

    async def _wait_for_gitlab_login(
        self, state: str, timeout: int
    ) -> Tuple[Dict, bool]:
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                "/api/unified-login/gitlab/wait-login",
                json={"state": state},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False

    async def refresh_access_token(self, refresh_token: str) -> Tuple[Dict, bool]:
        """
        description:
            使用refresh_token刷新access_token
            
            注意：GitLab 采用 token rotation（令牌轮换）机制，每次刷新时会返回新的 refresh_token，
            旧的 refresh_token 会立即失效。必须保存新的 refresh_token 并替换旧的。
        parameters:
            refresh_token(str): GitLab OAuth refresh_token
        return:
            token_data(dict): 包含新的access_token和可能的refresh_token的字典
            success(bool): 是否成功
        """
        data, success = await self._request(
            "POST",
            "/api/unified-login/gitlab/refresh-token",
            json={"refresh_token": refresh_token},
        )
        if not success:
            return {}, False
        return data, True


class SMSLogin(AsyncClient):
    """
    短信验证码登录客户端

    使用示例:
    ```
    sms = SMSLogin(api_key="your_api_key")
    # 发送验证码
    success = await sms.send_code(phone="13800138000")
    if success:
        # 验证验证码并登录
        user_info, success = await sms.login(phone="13800138000", code="123456")
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def send_code(self, phone: str) -> bool:
        """
        发送短信验证码

        :param phone: 手机号码
        :return: success 是否成功
        """
        data, success = await self._request(
            "POST", "/api/unified-login/sms/send-code", json={"phone": phone}
        )
        return bool(success)

    async def verify_code(self, phone: str, code: str) -> bool:
        """
        验证短信验证码

        :param phone: 手机号码
        :param code: 验证码
        :return: success 是否成功
        """
        _, success = await self._request(
            "POST",
            "/api/unified-login/sms/verify-code",
            json={"phone": phone, "code": code},
        )
        return bool(success)

    async def _wait_for_login(
        self, phone: str, timeout: int
    ) -> Tuple[Dict, bool]:
        """
        等待短信登录结果

        :param phone: 手机号码
        :param timeout: 超时时间（秒）
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                "/api/unified-login/sms/wait-sms-login",
                json={"phone": phone},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False

    async def login(
        self, phone: str, code: str, timeout: int = 180
    ) -> Tuple[Dict, bool]:
        """
        验证验证码并等待登录结果

        :param phone: 手机号码
        :param code: 验证码
        :param timeout: 等待登录结果的超时时间（秒）
        :return: (用户信息, 是否成功)
        """
        success = await self.verify_code(phone, code)
        if not success:
            return {}, False

        return await self._wait_for_login(phone, timeout)


class EmailLogin(AsyncClient):
    """
    邮箱验证码登录客户端

    使用示例:
    ```
    email = EmailLogin(api_key="your_api_key")
    # 发送验证码
    success = await email.send_code(email="user@example.com")
    if success:
        # 验证验证码并登录
        user_info, success = await email.login(email="user@example.com", code="123456")
    ```
    """

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def send_code(self, email: str) -> bool:
        """
        发送邮箱验证码

        :param email: 邮箱地址
        :return: success 是否成功
        """
        _, success = await self._request(
            "POST", "/api/unified-login/email/send-code", json={"email": email}
        )
        return bool(success)

    async def verify_code(self, email: str, code: str) -> bool:
        """
        验证邮箱验证码

        :param email: 邮箱地址
        :param code: 验证码
        :return: success 是否成功
        """
        _, success = await self._request(
            "POST",
            "/api/unified-login/email/verify-code",
            json={"email": email, "code": code},
        )
        return bool(success)

    async def _wait_for_login(
        self, email: str, timeout: int
    ) -> Tuple[Dict, bool]:
        """
        等待邮箱登录结果

        :param email: 邮箱地址
        :param timeout: 超时时间（秒）
        """
        interval = 2
        total_checks = max(1, timeout // interval) if timeout > 0 else 1

        for _ in range(total_checks):
            status, response = await self._request_raw(
                "POST",
                "/api/unified-login/email/wait-email-login",
                json={"email": email},
            )

            if status == 200 and response.get("success") is True:
                return response.get("data", {}), True

            if status in (400, 408):
                break

            await asyncio.sleep(interval)

        return {}, False

    async def login(
        self, email: str, code: str, timeout: int = 180
    ) -> Tuple[Dict, bool]:
        """
        验证验证码并等待登录结果

        :param email: 邮箱地址
        :param code: 验证码
        :param timeout: 等待登录结果的超时时间（秒）
        :return: (用户信息, 是否成功)
        """
        success = await self.verify_code(email, code)
        if not success:
            return {}, False

        return await self._wait_for_login(email, timeout)
