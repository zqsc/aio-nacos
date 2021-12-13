#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
@File :    example.py
@Author :    zqsc
@Time :    2021/12/13
@Contact :    zhao_zqsc@sina.com
@Python Version :    3.8.5
"""
import asyncio
from aio_nacos import AioNacos


async def example():
    """举例"""

    await nc.register('example', '192.168..8.66', 4444)

    conf = await nc.init_config('config-property', 'BDCT', 'test-space')

    services = await nc.watch_service('property', 'DEFAULT_GROUP', 'test-space')

    while True:
        print(conf.config_pool)
        print(services.services_pool)
        print(services.get_service('property'))
        await asyncio.sleep(3)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    nc = AioNacos(loop, '127.0.0.1', n_port=8848, n_user='nacos', n_password='nacos')

    loop.run_until_complete(example())
