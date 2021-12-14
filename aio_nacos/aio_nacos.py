#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
@File :    aio_nacos.py
@Author :    zqsc
@Time :    2021/12/13
@Contact :    zhao_zqsc@sina.com
@Python Version :    3.8.5
"""

import asyncio
import aiohttp
from .nacos_config import NacosConfig
from .nacos_services import NacosServices
from .nacos_error import check_status, NacosServerRegisterError
from .nacos_models import Beat
from datetime import datetime
import json
import logging


class AioNacos():
    """协程nacos驱动"""

    def __init__(self, loop, n_host, n_port, n_user, n_password, proxy=None, loger=None):
        self.nacos_addr = f'http://{n_host}:{n_port}'
        self.user = n_user
        self.password = n_password
        self.loop = loop
        self.proxy = proxy
        self.loger = loger if loger else logging
        self.conn = aiohttp.TCPConnector(verify_ssl=False, loop=self.loop)
        self.session = aiohttp.ClientSession(connector=self.conn, loop=self.loop)

        self.ttl = datetime.now().timestamp()
        self.token = None

        self.loop.create_task(self.__keep_login())  # 持续登录

        self.nacos_config = NacosConfig(self)
        self.nacos_services = NacosServices(self)

        self.loger.info('nacos连接成功')

    async def __get_token(self):
        """获取token"""
        url = self.nacos_addr + '/nacos/v1/auth/login'
        data = f'username={self.user}&password={self.password}'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        async with self.session.post(url, data=data, headers=headers, proxy=self.proxy) as response:
            check_status(response.status)
            res = await response.read()
            resp = json.loads(res)
        self.token = resp.get('accessToken')
        self.ttl = datetime.now().timestamp() + resp.get('tokenTtl') // 1000
        return self.token

    async def __keep_login(self):
        """保持登录 self.token, self.ttl"""
        self.loger.debug('保持token持续登录')
        while 1:
            if not self.token or self.ttl - 4 < datetime.now().timestamp():
                await self.__get_token()
            await asyncio.sleep(0.1)

    async def put_heartbeat(self, service_name, service_ip, service_port, weight, ephemeral, group_name, namespace_id,
                            metadata):
        """心跳检测循环"""
        beatJson = {"serviceName": service_name, "ip": service_ip, "port": service_port, "weight": int(weight),
                    'cluster': namespace_id, 'scheduled': True,
                    "metadata": {"starttime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
        print(beatJson)
        beat = Beat(**beatJson)

        while 1:
            # 必须字段
            params = {'serviceName': service_name}
            params['beat'] = beat.json(separators=',:')
            # 非必要字段
            if namespace_id:
                params['namespaceId'] = namespace_id  # 默认public
            if ephemeral:
                params['ephemeral'] = ephemeral
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            url = self.nacos_addr + '/nacos/v1/ns/instance/beat'
            # 权限证明
            if self.token:
                params['accessToken'] = self.token
            async with self.session.put(url, params=params, proxy=self.proxy, headers=headers) as response:
                check_status(response.status)
                res = await response.read()
                if json.loads(res).get('code') != 10200:
                    raise NacosServerRegisterError('服务注册失败！')
            await asyncio.sleep(5)

    async def register(self, s_name, s_host, s_port, weight: float = 1.0, ephemeral='', group_name='',
                       namespace_id='', metadata=''):
        """ 持续注册本服务"""
        self.loop.create_task(
            self.put_heartbeat(s_name, s_host, s_port, weight, ephemeral, group_name, namespace_id, metadata))
        self.loger.info('已开启心跳循环')
        return True

    def add_url_auth(self, url: str) -> str:
        """添加权限认证"""
        # 权限验证
        if self.token:
            url += f'?accessToken={self.token}'
        elif self.user:
            url += f'?username={self.user}&password={self.password}'
        return url

    async def close(self):
        """关闭"""
        await asyncio.gather(self.conn.close(), self.session.close())
        self.loger.info('已关闭nacos连接')

    # 配置
    async def init_config(self, data_id: str = None, group: str = None, tenant: str = 'public'):
        """监视配置，返回 NacosConfig， 使用 NacosConfig[data_id] 获取配置"""
        await self.nacos_config.init_config(data_id, group, tenant)
        return self.nacos_config

    # 监视器
    async def watch_service(self, service_name, group, namespace_id, healthy_only=True):
        """监视服务， 返回 NacosServices, 使用 NacosServices[service_name] 获取对应服务列表"""
        await self.nacos_services.watch_service(service_name, group, namespace_id, healthy_only=True)
        return self.nacos_services
