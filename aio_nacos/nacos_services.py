#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
@File :    nacos_services.py
@Author :    zqsc
@Time :    2021/12/13
@Contact :    zhao_zqsc@sina.com
@Python Version :    3.8.5
"""

from .nacos_error import check_status
from .nacos_models import Services
import asyncio
import json
from random import choice


class NacosServices:
    """监视服务管理"""

    _instance = None
    _first_init = True

    def __new__(cls, *args, **kwargs):
        # 单例模式
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, nacos_client=None):
        if self.__class__._first_init:  # 防止重复初始化
            self.__class__._first_init = False
            super().__init__()
        else:
            return
        assert nacos_client, 'AioNacos未初始化'
        self.nacos_client = nacos_client  # nacos连接对象
        self.loop = self.nacos_client.loop  # 事件循环
        self.session = self.nacos_client.session  # 连接池

        self.services_pool = {}
        self.logger = self.nacos_client.logger

    async def watch_service(self, service_name, group, namespace_id, clusters=None, healthy_only=True):
        """添加监视服务器"""
        self.services_pool[service_name] = Services()
        task = self.nacos_client.loop.create_task(
            self.__while_service(service_name, group, namespace_id, clusters, healthy_only))
        self.services_pool[service_name].task = task

    async def __get_service(self, service_name, group, namespace_id, clusters, healthy_only):
        """获得nacos注册服务"""
        # 基础参数
        params = {'serviceName': service_name}
        # 非必要参数
        if group:
            params['groupName'] = group
        if namespace_id:  # 默认public
            params['namespaceId'] = namespace_id
        if clusters:
            params['clusters'] = clusters
        if healthy_only:
            params['healthyOnly'] = 'true'
        url = self.nacos_client.nacos_addr + '/nacos/v1/ns/instance/list'
        # 权限证明
        if self.nacos_client.token:
            params['accessToken'] = self.nacos_client.token
        async with self.session.get(url, params=params, proxy=self.nacos_client.proxy) as response:
            check_status(response.status)
            res = await response.read()
            result = json.loads(res)
            if self.services_pool[service_name].services != result['hosts']:
                self.logger.info('更新组件：%s' % service_name)
                self.services_pool[service_name].services = result['hosts']

    async def __while_service(self, service_name, group, namespace_id, clusters, healthy_only):
        """获取目标服务列表"""
        while 1:
            await self.__get_service(service_name, group, namespace_id, clusters, healthy_only)
            await asyncio.sleep(3)

    def get_service(self, service_name):
        """获取一个service"""
        temp = self.services_pool[service_name].services
        if not temp:
            return None
        res = choice(temp)
        return res['ip'], res['port']

    def __getitem__(self, attr):
        if self.services_pool.get(attr):
            return self.services_pool.get(attr)
        else:
            self.logger.warning('没有同步该配置:%s' % attr)
            return None
