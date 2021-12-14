#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
@File :    nacos_config.py
@Author :    zqsc
@Time :    2021/12/13
@Contact :    zhao_zqsc@sina.com
@Python Version :    3.8.5
"""

from .nacos_error import check_status
from .nacos_models import Config
import json
import hashlib



class NacosConfig:
    """同步配置"""

    @staticmethod
    def make_MD5(content: bytes):
        return hashlib.md5(content).hexdigest()

    def __init__(self, nacos_client):
        # 必须值验证
        self.nacos_client = nacos_client
        self.conf_md5 = ''  # md5值
        self.loger = nacos_client.loger
        self.config_pool = {}

    async def init_config(self, data_id: str = None, group: str = None, tenant: str = 'public'):
        await self.__get_config(data_id, group, tenant)
        self.nacos_client.loop.create_task(self.watch_config(data_id, group, tenant))

    async def watch_config(self, data_id, group, tenant):
        """监听nacos中的配置"""
        while 1:
            res = await self.__post_config_check(data_id, group, tenant)
            if res:
                await self.__get_config(data_id, group, tenant)

    async def __post_config_check(self, data_id, group, tenant):
        """检查md5, nacos又返回值 则配置有更新"""
        # 内容生成
        headers = {'Long-Pulling-Timeout': '3000'}
        if tenant and tenant != 'public':
            data = {'Listening-Configs': f'{data_id}\002{group}\002{self.config_pool.get(data_id).md5}\002{tenant}\001'}
        else:
            data = {'Listening-Configs': f'{data_id}\002{group}\002{self.config_pool.get(data_id).md5}\001'}
        url = self.nacos_client.nacos_addr + '/nacos/v1/cs/configs/listener'
        # url权限 权限证明
        url = self.nacos_client.add_url_auth(url)
        # 开始md5验证
        async with self.nacos_client.session.post(url, data=data, headers=headers,
                                                  proxy=self.nacos_client.proxy) as response:
            check_status(response.status)
            res = await response.read()
            return res

    async def __get_config(self, data_id, group, tenant):
        """获得配置配置， 并写入配置池中"""
        self.loger.info('从nacos中更新配置-data_id:%s; grout:%s; tenant:%s' % (data_id, group, tenant))
        # 基础参数
        params = {'dataId': data_id, 'group': group, }
        # 非必要参数
        if tenant and tenant != 'public':
            params['tenant'] = tenant
        url = self.nacos_client.nacos_addr + '/nacos/v1/cs/configs'
        # 权限证明
        url = self.nacos_client.add_url_auth(url)
        async with self.nacos_client.session.get(url=url, params=params, proxy=self.nacos_client.proxy) as response:
            check_status(response.status)  #
            conf_md5 = response.headers.getone('Content-MD5')
            conf_type = response.headers.getone('Config-Type')
            res = await response.read()
        # 解析配置
        if conf_type == 'json':
            conf = Config(conf_md5)
            conf.__dict__.update(json.loads(res))
            self.config_pool[data_id] = conf

    def __getitem__(self, attr):
        if self.config_pool.get(attr):
            return self.config_pool.get(attr)
        else:
            self.loger.warning('没有同步该配置:%s' % attr)
            return None
