#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PixelArray 第三方微服务客户端
这个库包含了常用的开发工具和服务集成：
- order: 订单管理模块和支付模块
- product: 产品管理模块
- cron: 定时任务管理模块
- user: 用户管理模块
- unified_login: 统一登录模块
- feedback: 客户反馈模块
- project: 项目管理模块
"""

__version__ = "1.2.2"
__author__ = "Lu qi"
__email__ = "qi.lu@pixelarrayai.com"

# 导出主要模块
__all__ = [
    "product",
    "cron",
    "user",
    "order",
    "feedback",
    "project",
]
