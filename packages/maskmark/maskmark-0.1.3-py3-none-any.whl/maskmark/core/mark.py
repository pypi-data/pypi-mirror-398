#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py
@File    ：mark.py
@IDE     ：PyCharm
@Author  ：Handk
@Date    ：2025/3/20 19:16
@Describe：水印算法包
"""

from PIL import Image, ImageFont, ImageDraw
import pymupdf
from docx import Document
from docx.oxml import parse_xml
import os
from ..utils import file
from pymupdf.mupdf import PDF_ENCRYPT_KEEP

# 字体路径
reg_font_name = "SourceHanSansSC-VF.ttf"
reg_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'font', reg_font_name)
bold_font_name = "SourceHanSansCN-Bold.otf"
bold_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'font', bold_font_name)


def image_text_mark(image_path, watermark_text="Sample Watermark", font_size=36, fill_color=(190, 190, 190, 70),
                    save=False, save_path=None, show=True):
    """
    对图片添加文本水印
    :param image_path: 图片的存储路径
    :param watermark_text: 水印内容，默认为"Sample Watermark"
    :param font_size: 字体大小，默认为36
    :param fill_color: 文字颜色（RGBA格式），默认为浅灰色且半透明
    :param save: 是否保存,默认不保存
    :param save_path: 保存路径，默认覆盖原图
    :param show: 是否展示结果，默认展示
    """
    # 不指定保存路径则默认保存到原路径
    if save_path is None:
        save_path = image_path

    # 根据文件扩展名确定处理方式
    ext = image_path.lower().rsplit('.', 1)[-1]

    if ext == 'svg':
        # 将SVG转换为PNG格式
        # 由于cairo库安装较为复杂，暂时取消
        # out = io.BytesIO()
        # with open(image_path, "rb") as svg_file:
        #     cairosvg.svg2png(bytestring=svg_file.read(), write_to=out)
        # base = Image.open(out).convert("RGBA")
        ValueError("SVG格式暂不支持，请转换为PNG或JPG格式")

    elif str(ext).lower() in ["png", "jpg", "jpeg"]:
        # 直接打开非SVG图片
        base = Image.open(image_path).convert("RGBA")
    else:
        ValueError("该图片格式暂不支持")
        return 1
    # 创建一个比原图同样大的透明层用于绘制水印，防止水印倾斜之后存在遗漏
    txt_layer = Image.new('RGBA', (base.size[0] * 2, base.size[1] * 2), (255, 255, 255, 0))
    # 在txt_layer上绘制文字
    d = ImageDraw.Draw(txt_layer)

    # 选择字体和大小
    fnt = ImageFont.truetype(reg_font_path, font_size)

    # 获取文本尺寸
    left, top, right, bottom = fnt.getbbox(watermark_text)
    text_size_h, text_size_w = bottom - top, right - left

    # 循环打印文字，让文字水印遍布图片
    for y in range(0, int(base.size[1] * 2 - text_size_h), int(text_size_h + text_size_h * 2)):
        for x in range(0, int(base.size[0] * 2 - text_size_w), int(text_size_w + text_size_w / 7)):
            # 设置文字位置
            text_pos = (x, y)
            # 把文字画上去
            d.text(text_pos, watermark_text, font=fnt, fill=fill_color, stroke_width=1)
    # 把水印图层旋转45度
    txt_layer = txt_layer.rotate(45)

    # 将带有水印的透明层与原图合并
    base.alpha_composite(txt_layer, source=(int(base.size[1] / 2), int(base.size[0] / 2)))

    # 显示结果
    if show:
        base.show()

    if save:
        base.save(save_path)
        file.file_only_read(save_path)
        return 0
    return 0


def pdf_text_mark(pdf_path, watermark_text="Sample Watermark", font_size=8, font_color=(40, 40, 40, 40),save_path=None):
    """
    为pdf文件添加文本水印
    :param pdf_path:
    :param watermark_text:
    :param font_size:
    :param fill_color:
    :return:
    """
    # 标识是否为原文件保存
    incremental_flag = True
    # 不指定保存路径则默认保存到原路径
    if save_path is None:
        save_path = pdf_path
    # 如果保存路径与pdf文件路径不一致则修改原地保存标识
    if save_path is not pdf_path:
        incremental_flag = False


    # 水印倾斜角度
    rotate_angle = 45
    font_color = [x / 255 for x in font_color]
    pdf = pymupdf.open(pdf_path)
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        # 嵌入字体
        xref = page.insert_font(fontname="SourceHan", fontfile=bold_font_path)
        rect = page.rect
        CELLS = pymupdf.make_table(rect, cols=4, rows=10)
        shape = page.new_shape()  # create Shape

        for row in range(len(CELLS)):
            for col in range(len(CELLS[0])):
                shape.draw_rect(CELLS[row][col])  # draw rectangle

                # 设置旋转中心点
                # 中心点为每个网格的左边缘中心点
                point = pymupdf.Point(0.2 * (CELLS[row][col][2] - CELLS[row][col][0]) + CELLS[row][col][0],
                                      0.7 * (CELLS[row][col][3] - CELLS[row][col][1]) + CELLS[row][col][1])
                shape.insert_text(
                    point, watermark_text, rotate=0,
                    fontname="SourceHan", fontsize=font_size,
                    color=font_color, morph=(point, pymupdf.Matrix(rotate_angle))
                )
            shape.commit()

    pdf.save(save_path,incremental=incremental_flag,encryption=PDF_ENCRYPT_KEEP)
    pdf.close()
    file.file_only_read(save_path)
    return 0

def pdf_img_mark(pdf_path, img_path, alpha=0.5, scale=0.5, save_path=None):
    """
    为PDF文件添加图片水印，将图片以半透明状态放置于每一页的中央作为背景，水印不可删除。

    :param pdf_path: str，PDF文件的路径
    :param img_path: str，水印图片的路径（支持PNG、JPG等格式）
    :param alpha: float，图片透明度，取值范围0-1，0为完全透明，1为完全不透明，默认0.5
    :param scale: float，图片缩放比例，默认0.5（即缩小至原图的50%）
    :param save_path: str，保存处理后PDF的路径，若为None则覆盖原文件，默认None
    :return: int，0表示成功，非0表示失败
    :raises ValueError: 当图片文件无法读取或格式不支持时抛出
    """
    if save_path is None:
        save_path = pdf_path
    
    pdf = pymupdf.open(pdf_path)
    for page in pdf:
        rect = page.rect
        page_w, page_h = rect.width, rect.height
        
        # 读取图片
        try:
            img = pymupdf.Pixmap(img_path)
        except Exception as e:
            raise ValueError(f"无法读取图片文件: {e}")
        
        if img.is_invalid:
            raise ValueError("图片格式不受支持或文件损坏")
        
        # 计算缩放后的图片尺寸
        img_w = img.width * scale
        img_h = img.height * scale
        
        # 计算中央位置
        x = (page_w - img_w) / 2
        y = (page_h - img_h) / 2
        img_rect = pymupdf.Rect(x, y, x + img_w, y + img_h)
        
        # 插入图片，设置透明度
        page.insert_image(img_rect, pixmap=img, alpha=alpha)
        
        # 释放资源
        img = None
    
    pdf.save(save_path)
    pdf.close()
    file.file_only_read(save_path)
    return 0

def word_text_mark(word_path, watermark_text="Sample Watermark", font_size=36, font_color=(180, 180, 180, 30),save_path=None):
    """
    使用python-docx和VML为word文件添加多行多列灰色水印，模拟铺满页面（插入到正文层，不在页眉）
    :param word_path: Word文件路径
    :param watermark_text: 水印文字
    :param font_size: 字体大小
    :param font_color: (R,G,B,alpha) 0-255，alpha无效
    :return:
    """
    # 不指定保存路径则默认保存到原路径
    if save_path is None:
        save_path = word_path

    doc = Document(word_path)
    r, g, b, _ = font_color
    color_hex = f"#{r:02x}{g:02x}{b:02x}"
    # VML水印XML模板
    vml_watermark = f'''
    <w:pict xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:v="urn:schemas-microsoft-com:vml"
            xmlns:o="urn:schemas-microsoft-com:office:office">
      <v:shape id="WordArt1" type="#_x0000_t136"
        style='position:absolute;margin-left:-{font_size*4}pt;margin-top:{font_size*8}pt;width:{font_size*20}pt;height:{font_size*5}pt;z-index:-251654144;visibility:visible;rotation:-45;mso-wrap-style:square'
        fillcolor="{color_hex}"
        stroked="f"
        o:allowincell="f" o:allowoverlap="f">
        <v:textpath style='font-family:微软雅黑;font-size:{font_size}pt' on="t" string="{watermark_text}"/>
        <v:fill opacity="0.2"/>
        <v:shadow on="t" color="black" obscured="t"/>
      </v:shape>
    </w:pict>
    '''
    # 插入到每节的header
    for section in doc.sections:
        header = section.header
        p = header.add_paragraph()
        p._element.append(parse_xml(vml_watermark))
    # 保存
    doc.save(save_path)
    file.file_only_read(save_path)
    return 0
