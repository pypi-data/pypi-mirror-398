#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_python 
@File    ：interface.py
@IDE     ：PyCharm 
@Author  ：Handk
@Date    ：2025/4/7 18:43 
@Describe：接口定义包
"""
from abc import ABC, abstractmethod


class ServiceInterface(ABC):
    """
    服务接口类
    """

    @abstractmethod
    def handle(self, data, rule):
        pass
