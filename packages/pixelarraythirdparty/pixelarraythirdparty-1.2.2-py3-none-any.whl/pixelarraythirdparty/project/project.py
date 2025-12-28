from pixelarraythirdparty.client import AsyncClient


class ProjectManagerAsync(AsyncClient):
    async def create_project(
        self,
        name: str,
    ):
        """
        description:
            创建新的项目。
        parameters:
            name(str): 项目名称
        return:
            data(dict): 项目信息
                - id(int): 项目ID
                - name(str): 项目名称
                - created_at(str): 项目创建时间
            success(bool): 操作是否成功
        """
        data = {
            "name": name,
        }
        data, success = await self._request("POST", "/api/projects/create", json=data)
        if not success:
            return {}, False
        return data, True

    async def list_project(
        self,
        page: int = 1,
        page_size: int = 10,
        name: str = None,
    ):
        """
        description:
            分页查询项目列表，支持按项目名称进行搜索。
        parameters:
            page(int): 页码
            page_size(int): 每页数量
            name(str): 项目名称搜索，支持模糊匹配
        return:
            data(dict): 项目列表信息
                - projects(list): 项目列表
                    - id(int): 项目ID
                    - name(str): 项目名称
                    - created_at(str): 项目创建时间
                - total(int): 总项目数量
                - page(int): 当前页码
                - page_size(int): 每页数量
            success(bool): 操作是否成功
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if name is not None:
            params["name"] = name
        data, success = await self._request("GET", "/api/projects/list", params=params)
        if not success:
            return {}, False
        return data, True

    async def delete_project(self, project_id: int):
        """
        description:
            根据项目ID删除指定的项目记录。如果项目下还有产品或反馈，则不允许删除。
        parameters:
            project_id(int): 项目ID
        return:
            data(None): 删除成功时返回None
            success(bool): 操作是否成功
        """
        data, success = await self._request("DELETE", f"/api/projects/{project_id}")
        if not success:
            return {}, False
        return data, True

