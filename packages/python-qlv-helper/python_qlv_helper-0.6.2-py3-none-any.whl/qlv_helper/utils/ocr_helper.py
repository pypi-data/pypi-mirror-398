# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     ocr_helper.py
# Description:  OCR模块
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import ddddocr
import requests
from typing import Union, Tuple
from aiohttp import ClientSession
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# 复用 OCR 实例，不用每次都重新加载模型（更快）
_ocr = ddddocr.DdddOcr(show_ad=False)


def fetch_and_ocr_captcha(url: str) -> Tuple[str, bytes]:
    # 1) 请求验证码图片
    resp = requests.get(url, timeout=10)
    img_bytes = resp.content

    # 2) OCR 识别
    result = _ocr.classification(img_bytes)

    return result, img_bytes


async def async_fetch_and_ocr_captcha(url: str) -> Tuple[str, bytes]:
    async with ClientSession() as session:
        async with session.get(url, timeout=10) as resp:
            img_bytes = await resp.read()

    result = _ocr.classification(img_bytes)
    return result, img_bytes


def recognize_captcha(image: Union[str, bytes]) -> str:
    """
    识别验证码图片，返回识别文本。
    参数:
        image: 图片路径 str，或图片的二进制 bytes
    返回:
        识别出的验证码字符串
    """
    try:
        # 如果是路径，读取文件
        if isinstance(image, str):
            with open(image, "rb") as f:
                img_bytes = f.read()
        else:
            img_bytes = image

        result = _ocr.classification(img_bytes)
        return result

    except Exception as e:
        raise RuntimeError(f"OCR 识别失败: {e}")


async def get_image_text(page: Page, selector: str, timeout: float = 5.0) -> Tuple[bool, str]:
    try:
        # 找到 img
        locator = page.locator(selector)
        if locator:
            img = await locator.element_handle(timeout=timeout * 1000)

            # 直接截图获取原始图片字节，不刷新图片
            img_bytes = await img.screenshot(timeout=timeout * 1000)

            # OCR 识别
            text = _ocr.classification(img_bytes)
            return True, text.strip()
        else:
            return False, f'没有找到当前页面中的【{selector}】图片'
    except PlaywrightTimeoutError:
        return False, f"元素 '{selector}' 未在 {timeout} 秒内找到"
    except Exception as e:
        return False, f"检查元素时发生错误: {str(e)}"
