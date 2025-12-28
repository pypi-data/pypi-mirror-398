from pixelarraythirdparty.client import AsyncClient


class ProductManagerAsync(AsyncClient):
    async def create_product(
        self,
        name: str,
        description: str,
        price: float,
        category: str,
        status: str,
        is_subscription: bool,
        subscription_period: str,
        features: str,
        sort_order: int,
    ):
        """
        description:
            创建新的产品，支持订阅产品和一次性产品，产品信息包括名称、描述、价格、分类等。
        parameters:
            name(str): 产品名称
            description(str): 产品描述
            price(float): 产品价格（元）
            category(str): 产品分类
            status(str): 产品状态，可选值："ACTIVE"（激活）、"INACTIVE"（停用）
            is_subscription(bool): 是否为订阅产品
            subscription_period(str): 订阅周期，可选值："MONTHLY"（月付）、"YEARLY"（年付）
            features(str): 产品特性，JSON格式字符串
            sort_order(int): 排序权重
        return:
            data(dict): 产品信息
                - id(int): 产品ID
                - name(str): 产品名称
                - description(str): 产品描述
                - price(float): 产品价格（元）
                - category(str): 产品分类
                - status(str): 产品状态
                - is_subscription(bool): 是否为订阅产品
                - subscription_period(str): 订阅周期
                - features(str): 产品特性（JSON格式）
                - sort_order(int): 排序权重
                - created_at(str): 产品创建时间
                - updated_at(str): 产品更新时间
            success(bool): 操作是否成功
        """
        data = {
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "status": status,
            "is_subscription": is_subscription,
            "subscription_period": subscription_period,
            "features": features,
            "sort_order": sort_order,
        }
        data, success = await self._request("POST", "/api/products/create", json=data)
        if not success:
            return {}, False
        return data, True

    async def list_product(
        self,
        page: int = 1,
        page_size: int = 10,
        status: str = None,
        category: str = None,
        name: str = None,
    ):
        """
        description:
            分页查询产品列表，支持按状态、分类和名称进行筛选。
        parameters:
            page(int): 页码
            page_size(int): 每页数量
            status(str): 产品状态筛选，可选值："ACTIVE"（激活）、"INACTIVE"（停用）
            category(str): 产品分类筛选
            name(str): 产品名称搜索，支持模糊匹配
        return:
            data(dict): 产品列表信息
                - products(list): 产品列表
                - total(int): 总产品数量
                - page(int): 当前页码
                - page_size(int): 每页数量
            success(bool): 操作是否成功
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        if name is not None:
            params["name"] = name
        data, success = await self._request("GET", "/api/products/list", params=params)
        if not success:
            return {}, False
        return data, True

    async def get_product_detail(self, product_id: str):
        """
        description:
            根据产品ID获取产品的详细信息。
        parameters:
            product_id(str): 产品ID
        return:
            data(dict): 产品详细信息
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", f"/api/products/{product_id}")
        if not success:
            return {}, False
        return data, True

    async def update_product(
        self,
        product_id: str,
        name: str,
        description: str,
        price: float,
        category: str,
        status: str,
        is_subscription: bool,
        subscription_period: str,
        features: str,
        sort_order: int,
    ):
        """
        description:
            更新指定产品的信息，包括名称、描述、价格、状态等。
        parameters:
            product_id(str): 产品ID
            name(str): 产品名称
            description(str): 产品描述
            price(float): 产品价格（元）
            category(str): 产品分类
            status(str): 产品状态，可选值："ACTIVE"（激活）、"INACTIVE"（停用）
            is_subscription(bool): 是否为订阅产品
            subscription_period(str): 订阅周期，可选值："MONTHLY"（月付）、"YEARLY"（年付）
            features(str): 产品特性，JSON格式字符串
            sort_order(int): 排序权重
        return:
            data(dict): 更新后的产品信息
                - id(int): 产品ID
                - name(str): 产品名称
                - description(str): 产品描述
                - price(float): 产品价格（元）
                - category(str): 产品分类
                - status(str): 产品状态
                - is_subscription(bool): 是否为订阅产品
                - subscription_period(str): 订阅周期
                - features(str): 产品特性（JSON格式）
                - sort_order(int): 排序权重
                - created_at(str): 产品创建时间
                - updated_at(str): 产品更新时间
            success(bool): 操作是否成功
        """
        data = {
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "status": status,
            "is_subscription": is_subscription,
            "subscription_period": subscription_period,
            "features": features,
            "sort_order": sort_order,
        }
        data, success = await self._request(
            "PUT", f"/api/products/{product_id}", json=data
        )
        if not success:
            return {}, False
        return data, True

    async def delete_product(self, product_id: str):
        """
        description:
            根据产品ID删除指定的产品记录。
        parameters:
            product_id(str): 产品ID
        return:
            data(None): 删除成功时返回None
            success(bool): 操作是否成功
        """
        data, success = await self._request("DELETE", f"/api/products/{product_id}")
        if not success:
            return {}, False
        return data, True

    async def get_product_categories(self):
        """
        description:
            获取所有可用的产品分类列表。
        return:
            data(dict): 产品分类信息
                - categories(list): 产品分类列表，如["subscription", "service", "addon"]
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", "/api/products/categories/list")
        if not success:
            return {}, False
        return data, True
