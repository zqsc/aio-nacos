#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
@File :    nacos_error.py
@Author :    zqsc
@Time :    2021/12/13
@Contact :    zhao_zqsc@sina.com
@Python Version :    3.8.5
"""

import traceback


class NacosBadRequestError(Exception):
    pass


class NacosForbiddenError(Exception):
    pass


class NacosNotFoundError(Exception):
    pass


class NacosServerError(Exception):
    pass


class NacosServerRegisterError(Exception):
    pass


def check_status(code: int):
    if code == 200:
        return
    elif code == 400:
        raise NacosBadRequestError('nacos-语法错误:', traceback.print_exc())
    elif code == 403:
        raise NacosForbiddenError('nacos-没有权限:', traceback.print_exc())
    elif code == 404:
        raise NacosNotFoundError('nacos-没有找到资源:', traceback.print_exc())
    elif code == 500:
        raise NacosServerError('nacos-服务内部错误:', traceback.print_exc())
