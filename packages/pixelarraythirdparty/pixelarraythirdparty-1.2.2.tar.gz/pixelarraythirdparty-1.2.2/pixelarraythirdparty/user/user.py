import aiohttp
from typing import Optional
from pixelarraythirdparty.client import AsyncClient


class UserManagerAsync(AsyncClient):
    async def list_user(
        self,
        page: int = 1,
        page_size: int = 10,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ):
        """
        description:
            分页查询用户列表，支持按角色和状态进行筛选。仅管理员可访问。
        parameters:
            page(int): 页码
            page_size(int): 每页数量
            role(str): 用户角色筛选，可选值："admin"（管理员）、"user"（普通用户）
            is_active(bool): 用户状态筛选，True为激活，False为禁用
        return:
            data(dict): 用户列表信息
                - users(list): 用户列表
                - total(int): 总用户数量
                - page(int): 当前页码
                - page_size(int): 每页数量
            success(bool): 操作是否成功
        """
        params = {"page": page, "page_size": page_size}
        if role is not None:
            params["role"] = role
        if is_active is not None:
            params["is_active"] = is_active
        data, success = await self._request("GET", "/api/users/list", params=params)
        if not success:
            return {}, False
        return data, True

    async def create_user(self, username: str, password: str, email: str, role: str):
        """
        description:
            创建新的用户账户，仅管理员可访问。
        parameters:
            username(str): 用户名
            password(str): 密码
            email(str): 邮箱地址
            role(str): 用户角色，可选值："admin"（管理员）、"user"（普通用户）
        return:
            data(dict): 用户信息
                - id(int): 用户ID
                - username(str): 用户名
                - email(str): 邮箱地址
                - role(str): 用户角色
                - is_active(bool): 是否激活，默认为True
                - created_at(str): 用户创建时间
            success(bool): 操作是否成功
        """
        data = {
            "username": username,
            "password": password,
            "email": email,
            "role": role,
        }
        data, success = await self._request("POST", "/api/users/create", json=data)
        if not success:
            return {}, False
        return data, True

    async def update_user(
        self, user_id: int, username: str, email: str, role: str, is_active: bool
    ):
        """
        description:
            更新指定用户的信息，包括用户名、邮箱、角色和状态。仅管理员可访问。
        parameters:
            user_id(int): 用户ID
            username(str): 用户名
            email(str): 邮箱地址
            role(str): 用户角色，可选值："admin"（管理员）、"user"（普通用户）
            is_active(bool): 是否激活
        return:
            data(dict): 更新后的用户信息
                - id(int): 用户ID
                - username(str): 用户名
                - email(str): 邮箱地址
                - role(str): 用户角色
                - is_active(bool): 是否激活
                - created_at(str): 用户创建时间
                - updated_at(str): 用户信息更新时间
            success(bool): 操作是否成功
        """
        data = {
            "username": username,
            "email": email,
            "role": role,
            "is_active": is_active,
        }
        data, success = await self._request("PUT", f"/api/users/{user_id}", json=data)
        if not success:
            return {}, False
        return data, True

    async def delete_user(self, user_id: int):
        """
        description:
            根据用户ID删除指定的用户记录。仅管理员可访问。
        parameters:
            user_id(int): 用户ID
        return:
            data(None): 删除成功时返回None
            success(bool): 操作是否成功    
        """
        data, success = await self._request("DELETE", f"/api/users/{user_id}")
        if not success:
            return {}, False
        return data, True

    async def get_user_detail(self, user_id: int):
        """
        description:
            根据用户ID获取用户的详细信息。仅管理员可访问。
        parameters:
            user_id(int): 用户ID
        return:
            data(dict): 用户详细信息
                - id(int): 用户ID
                - username(str): 用户名
                - email(str): 邮箱地址
                - role(str): 用户角色
                - is_active(bool): 是否激活
                - created_at(str): 用户创建时间
                - last_login_at(str): 最后登录时间
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", f"/api/users/{user_id}")
        if not success:
            return {}, False
        return data, True

    async def reset_user_password(self, user_id: int, new_password: str):
        """
        description:
            重置指定用户的密码。仅管理员可访问。
        parameters:
            user_id(int): 用户ID
            new_password(str): 新密码
        return:
            data(None): 重置成功时返回None
            success(bool): 操作是否成功
        """
        data = {"new_password": new_password}
        data, success = await self._request(
            "POST", f"/api/users/{user_id}/reset-password", json=data
        )
        if not success:
            return {}, False
        return data, True
