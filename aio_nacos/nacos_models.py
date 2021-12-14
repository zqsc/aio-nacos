#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
@File :    nacos_models.py
@Author :    zqsc
@Time :    2021/12/13
@Contact :    zhao_zqsc@sina.com
@Python Version :    3.8.5
"""

from pydantic import BaseModel


class Beat(BaseModel):
    serviceName: str
    ip: str
    port: int
    cluster: str = 'public'
    scheduled: bool = True
    metadata: dict = {}
    weight: int = 1

    def __str__(self):
        return self.json(separators=',:')


class Services:
    def __init__(self):
        self.task = None
        self.services = None
        pass

class Config:
    def __init__(self, md5):
        self.md5 = md5

