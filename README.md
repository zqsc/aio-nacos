# aio-nacos
异步nacos库

```angular2html
import asyncio
from aio_nacos import AioNacos


async def example():
    """举例"""

    await nc.register('example', '192.168.8.66', 4444)

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

```

### 问题
- 没有解决注册在非默认分组下，服务每隔30秒左右掉线，持续15秒后再次上线问题。固本nacos库只能注册默认分组下的服务
