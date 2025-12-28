from pixelarraythirdparty.client import AsyncClient


class OrderManagerAsync(AsyncClient):
    async def create_order(
        self,
        product_id: str,
        body: str = None,
        remark: str = None,
        payment_channel: str = "WECHAT",
    ):
        """
        description:
            根据产品ID创建新的订单，系统会自动生成订单号，获取产品价格信息，并创建对应的支付订单。
        parameters:
            product_id(str): 产品ID
            body(str): 商品描述
            remark(str): 订单备注
            payment_channel(str): 支付渠道，可选值："WECHAT"（微信支付）、"ALIPAY"（支付宝支付）
        return:
            data(dict): 订单信息
                - id(int): 订单ID
                - out_trade_no(str): 商户订单号，格式为"ORD_时间戳_随机字符串"
                - payment_status(str): 支付状态，初始为"PENDING"（待支付）
                - payment_channel(str): 支付渠道
                - product_id(str): 产品ID
                - amount(str): 订单金额（元），格式为"99.00"
                - total_fee(int): 订单金额（分），用于支付接口
                - body(str): 商品描述
                - remark(str): 订单备注
                - created_at(str): 订单创建时间
                - updated_at(str): 订单更新时间
            success(bool): 操作是否成功
        """
        data = {
            "product_id": product_id,
            "body": body,
            "remark": remark,
            "payment_channel": payment_channel,
        }
        data, success = await self._request("POST", "/api/orders/create", json=data)
        if not success:
            return {}, False
        return data, True

    async def create_order_v2(
        self,
        product_id: str,
        body: str = None,
        remark: str = None,
        payment_channel: str = "WECHAT",
    ):
        """
        description:
            创建订单并直接返回支付二维码（V2，推荐）。
            相比旧流程（create_order + generate_qr_code），该接口一次请求完成下单和二维码链接生成。
        parameters:
            product_id(str): 产品ID
            body(str): 商品描述
            remark(str): 订单备注
            payment_channel(str): 支付渠道，可选值："WECHAT"、"ALIPAY"、"PAYPAL"
        return:
            data(dict): 返回数据
                - order(dict): 订单信息（字段同 create_order 返回）
                - qr_code_url(str): 支付二维码图片URL
            success(bool): 操作是否成功
        """
        data = {
            "product_id": product_id,
            "body": body,
            "remark": remark,
            "payment_channel": payment_channel,
        }
        data, success = await self._request("POST", "/api/orders/create_v2", json=data)
        if not success:
            return {}, False
        return data, True

    async def list_order(
        self,
        page: int = 1,
        page_size: int = 10,
        payment_status: str = None,
        out_trade_no: str = None,
    ):
        """
        description:
            分页查询订单列表，支持按支付状态和订单号进行筛选。
        parameters:
            page(int): 页码
            page_size(int): 每页数量
            payment_status(str): 支付状态，可选值："PENDING"（待支付）、"PAID"（已支付）、"REFUNDED"（已退款）、"CANCELLED"（已取消）
            out_trade_no(str): 订单号，支持模糊匹配
        return:
            data(dict): 订单列表信息
                - orders(list): 订单列表
                    - id(int): 订单ID
                    - out_trade_no(str): 商户订单号
                    - payment_status(str): 支付状态
                    - payment_channel(str): 支付渠道
                    - amount(str): 订单金额（元）
                    - total_fee(int): 订单金额（分）
                    - created_at(str): 订单创建时间
                    - updated_at(str): 订单更新时间
                - total(int): 总订单数量
                - page(int): 当前页码
                - page_size(int): 每页数量
            success(bool): 操作是否成功
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        # 只添加非None的参数
        if payment_status is not None:
            params["payment_status"] = payment_status
        if out_trade_no is not None:
            params["out_trade_no"] = out_trade_no
        data, success = await self._request("GET", "/api/orders/list", params=params)
        if not success:
            return {}, False
        return data, True

    async def get_order_detail(self, out_trade_no: str):
        """
        description:
            根据订单号获取订单的详细信息，包括支付状态、交易信息等。
        parameters:
            out_trade_no(str): 商户订单号
        return:
            data(dict): 订单详细信息
                - id(int): 订单ID
                - out_trade_no(str): 商户订单号
                - payment_status(str): 支付状态
                - product_id(str): 产品ID
                - amount(str): 订单金额（元）
                - total_fee(int): 订单金额（分）
                - body(str): 商品描述
                - transaction_id(str): 微信交易号（支付成功后才有）
                - openid(str): 用户openid（支付成功后才有）
                - trade_type(str): 交易类型（支付成功后才有）
                - bank_type(str): 银行类型（支付成功后才有）
                - fee_type(str): 货币类型，默认为"CNY"
                - is_subscribe(str): 是否关注公众号（支付成功后才有）
                - time_end(str): 支付完成时间（支付成功后才有）
                - created_at(str): 订单创建时间
                - updated_at(str): 订单更新时间
                - paid_at(str): 支付时间（支付成功后才有）
                - remark(str): 订单备注
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", f"/api/orders/{out_trade_no}")
        if not success:
            return {}, False
        return data, True

    async def update_order_status(self, out_trade_no: str, payment_status: str):
        """
        description:
            更新指定订单的支付状态，仅支持状态修改，其他字段不可修改。
        parameters:
            out_trade_no(str): 商户订单号
            payment_status(str): 支付状态，可选值："PENDING"（待支付）、"PAID"（已支付）、"REFUNDED"（已退款）、"CANCELLED"（已取消）
        return:
            data(dict): 更新后的订单信息
                - id(int): 订单ID
                - out_trade_no(str): 商户订单号
                - payment_status(str): 更新后的支付状态
                - transaction_id(str): 微信交易号（如果已支付）
                - openid(str): 用户openid（如果已支付）
                - trade_type(str): 交易类型（如果已支付）
                - bank_type(str): 银行类型（如果已支付）
                - fee_type(str): 货币类型
                - is_subscribe(str): 是否关注公众号（如果已支付）
                - time_end(str): 支付完成时间（如果已支付）
                - paid_at(str): 支付时间（如果已支付）
                - updated_at(str): 订单更新时间
                - remark(str): 订单备注
            success(bool): 操作是否成功
        """
        data = {"payment_status": payment_status}
        data, success = await self._request(
            "PUT", f"/api/orders/{out_trade_no}/status", json=data
        )
        if not success:
            return {}, False
        return data, True

    async def delete_order(self, out_trade_no: str):
        """
        description:
            根据订单号删除指定的订单记录。
        parameters:
            out_trade_no(str): 商户订单号
        return:
            data(None): 删除成功时返回None
            success(bool): 操作是否成功
        """
        data, success = await self._request("DELETE", f"/api/orders/{out_trade_no}")
        if not success:
            return {}, False
        return data, True

    async def get_order_stats(self):
        """
        description:
            获取订单的统计汇总信息，包括总订单数、各状态订单数量、总金额等。
        return:
            data(dict): 订单统计信息
                - total_orders(int): 总订单数量
                - pending_orders(int): 待支付订单数量
                - paid_orders(int): 已支付订单数量
                - refunded_orders(int): 已退款订单数量
                - total_amount(float): 总订单金额（元）
                - total_fee(int): 总订单金额（分）
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", "/api/orders/stats/summary")
        if not success:
            return {}, False
        return data, True

    async def generate_qr_code(self, out_trade_no: str):
        """
        description:
            为指定订单生成支付二维码，支持微信支付和支付宝。二维码会自动上传到OSS并返回访问URL。
            如果不指定payment_channel，会自动从订单详情中获取支付渠道。
        parameters:
            out_trade_no(str): 商户订单号
        return:
            data(dict): 二维码信息
                - qr_code_url(str): 二维码图片URL，可直接用于显示
                - out_trade_no(str): 商户订单号
            success(bool): 操作是否成功
        """
        order_detail, success = await self.get_order_detail(out_trade_no)
        print(order_detail)
        if not success:
            return {}, False

        if order_detail.get("payment_channel") == "WECHAT":
            url = "/api/orders/wx_pay/generate_qr_code"
            request_data = {
                "out_trade_no": out_trade_no,
            }
        elif order_detail.get("payment_channel") == "ALIPAY":
            url = "/api/orders/ali_pay/generate_qr_code"
            # 支付宝需要total_fee和subject，从已获取的订单详情中提取
            request_data = {
                "out_trade_no": out_trade_no,
                "total_fee": order_detail.get("total_fee"),
                "subject": order_detail.get("body", ""),
            }
        else:
            raise ValueError("Invalid payment channel")
        data, success = await self._request("POST", url, json=request_data)
        if not success:
            return {}, False
        return data, True

    async def refund_order(self, out_trade_no: str):
        """
        description:
            为指定订单申请退款，支持微信支付和支付宝。退款申请提交后，系统会处理退款并更新订单状态。
        parameters:
            out_trade_no(str): 商户订单号
        return:
            data(dict): 退款信息
                - out_refund_no(str): 退款单号，格式为"REFUND_订单号_时间戳"
                - out_trade_no(str): 商户订单号
                - total_fee(int): 退款金额（分，微信支付）
                - refund_amount(float): 退款金额（元，支付宝）
            success(bool): 操作是否成功
        """
        order_detail, success = await self.get_order_detail(out_trade_no)
        if not success:
            return {}, False

        if order_detail.get("payment_channel") == "WECHAT":
            url = "/api/orders/wx_pay/refund"
            request_data = {"out_trade_no": out_trade_no}
        elif order_detail.get("payment_channel") == "ALIPAY":
            url = "/api/orders/ali_pay/refund"
            request_data = {
                "out_trade_no": out_trade_no,
                "refund_amount": order_detail.get("total_fee") / 100.0,
                "refund_reason": "用户退款",
            }
        else:
            raise ValueError("Invalid payment channel")
        data, success = await self._request("POST", url, json=request_data)
        if not success:
            return {}, False
        return data, True

    async def get_revenue_trend(
        self,
        start_date: str = None,
        end_date: str = None,
        dimension: str = "day",
    ):
        """
        description:
            获取收入趋势统计，只统计已支付(PAID)的订单。支持按日、按周、按月三种维度统计。
        parameters:
            start_date(str): 开始日期，格式：YYYY-MM-DD，可选
            end_date(str): 结束日期，格式：YYYY-MM-DD，可选
            dimension(str): 统计维度，可选值："day"（按日）、"week"（按周）、"month"（按月），默认为"day"
        return:
            data(dict): 收入趋势统计信息
                - trend(list): 趋势数据列表
                    - date(str): 日期或时间段
                    - revenue(float): 收入金额（元）
                    - order_count(int): 订单数量
                - dimension(str): 统计维度
                - start_date(str): 开始日期
                - end_date(str): 结束日期
            success(bool): 操作是否成功
        """
        params = {
            "dimension": dimension,
        }
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        data, success = await self._request("GET", "/api/orders/stats/revenue-trend", params=params)
        if not success:
            return {}, False
        return data, True

    async def get_product_revenue_ranking(
        self,
        start_date: str = None,
        end_date: str = None,
        limit: int = 10,
    ):
        """
        description:
            获取产品收入排名，只统计已支付(PAID)的订单。按收入金额降序排列。
        parameters:
            start_date(str): 开始日期，格式：YYYY-MM-DD，可选
            end_date(str): 结束日期，格式：YYYY-MM-DD，可选
            limit(int): 返回排名数量，默认为10，最大100
        return:
            data(dict): 产品收入排名信息
                - ranking(list): 排名列表
                    - product_id(int): 产品ID
                    - product_name(str): 产品名称
                    - product_category(str): 产品分类
                    - revenue(float): 收入金额（元）
                    - order_count(int): 订单数量
                - start_date(str): 开始日期
                - end_date(str): 结束日期
            success(bool): 操作是否成功
        """
        params = {
            "limit": limit,
        }
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        data, success = await self._request("GET", "/api/orders/stats/product-ranking", params=params)
        if not success:
            return {}, False
        return data, True
