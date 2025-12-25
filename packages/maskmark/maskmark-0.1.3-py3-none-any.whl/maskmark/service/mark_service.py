#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py
@File    ：mark_service.py
@IDE     ：PyCharm
@Author  ：Handk
@Date    ：2025/3/27 15:25
@Describe：服务层水印函数集合，利用底层算法实现一系列能力
"""
import datetime
import time

from .interface import ServiceInterface
from ..core.mark import *


class Mark_image(ServiceInterface):
    def handle(self, image_path, rule):
        """
        为图片添加水印
        :param image_path: 图片文件路径
        :param rule: 水印规则
        :return: 是否完成，0代表完成，1代表存在异常
        """
        # 获取水印类型
        mark_type = rule.get("Method")
        if mark_type == "text":
            return self.handle_text(image_path, rule.get("Content"))

    def handle_text(self, image_path, rule):
        """
        为图片添加文本水印
        :param image_path: 图片文件路径
        :param rule: 水印规则
        :return: 是否完成，0代表完成，1代表存在异常
        """
        # 获取自定义占位数据
        d = rule.get("d")

        # 获取模板
        template = rule.get("template")

        # 组合水印内容
        ## 加入支持的占位符信息
        d["Date"] = datetime.date.today()
        d["Time"] = datetime.datetime.now().time().strftime("%H:%M:%S")
        ## 其他信息根据传入的参数d嵌入到字符串中
        watermark_text = template.format(**d)
        return image_text_mark(image_path, show=False,save=True,watermark_text=watermark_text)


class Mark_pdf(ServiceInterface):
    def handle(self, pdf_path, rule):
        """
        为PDF文件添加水印
        :param pdf_path: PDF文件路径
        :param rule: 水印规则
        :return: 是否完成，0代表完成，1代表存在异常
        """
        # 获取水印类型
        mark_type = rule.get("Method")
        if mark_type == "text":
            return self.handle_text(pdf_path, rule.get("Content"))
        if mark_type == "image":
            return self.handle_image(pdf_path, rule.get("Content"))

    def handle_text(self, pdf_path, rule):
        # 获取自定义占位数据
        d = rule.get("d")

        # 获取模板
        template = rule.get("template")

        # 组合水印内容
        ## 加入支持的占位符信息
        d["Date"] = datetime.date.today()
        d["Time"] = datetime.datetime.now().time().strftime("%H:%M:%S")
        ## 其他信息根据传入的参数d嵌入到字符串中
        watermark_text = template.format(**d)
        return pdf_text_mark(pdf_path, watermark_text=watermark_text)
    
    def handle_image(self, pdf_path, rule):
        # 获取自定义占位数据
        d = rule.get("d")

        # 获取模板
        template = rule.get("template")

        # 组合水印内容
        ## 加入支持的占位符信息
        d["Date"] = datetime.date.today()
        d["Time"] = datetime.datetime.now().time().strftime("%H:%M:%S")
        ## 其他信息根据传入的参数d嵌入到字符串中
        watermark_text = template.format(**d)
        # return pdf_image_mark(pdf_path, watermark_text=watermark_text)

class Mark_word(ServiceInterface):
    def handle(self, word_path, rule):
        """
        为Word文件添加水印
        :param word_path: Word文件路径
        :param rule: 水印规则
        :return: 是否完成，0代表完成，1代表存在异常
        """
        # 获取水印类型
        mark_type = rule.get("Method")
        if mark_type == "text":
            return self.handle_text(word_path, rule.get("Content"))

    def handle_text(self, word_path, rule):
        # 获取自定义占位数据
        d = rule.get("d")

        # 获取模板
        template = rule.get("template")

        # 组合水印内容
        ## 加入支持的占位符信息
        d["Date"] = datetime.date.today()
        d["Time"] = datetime.datetime.now().time().strftime("%H:%M:%S")
        ## 其他信息根据传入的参数d嵌入到字符串中
        watermark_text = template.format(**d)
        return word_text_mark(word_path, watermark_text=watermark_text)


mark_word_service = Mark_word()
mark_image_service = Mark_image()
mark_pdf_service = Mark_pdf()
