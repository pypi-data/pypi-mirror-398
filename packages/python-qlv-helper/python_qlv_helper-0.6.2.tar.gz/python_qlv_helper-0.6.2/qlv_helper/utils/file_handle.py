# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     file_handle.py
# Description:  文件处理工具模块
# Author:       ASUS
# CreateDate:   2025/11/25
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import os
import inspect


def get_caller_dir() -> str:
    # 获取调用者的 frame
    frame = inspect.stack()[1]
    caller_file = frame.filename  # 调用者文件的完整路径
    return os.path.dirname(os.path.abspath(caller_file))


def save_image(file_name: str, img_bytes: bytes) -> None:
    """
    保存验证码图片到本地。
    若文件已存在，会自动覆盖。
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    # "wb" 会覆盖已有文件
    with open(file_name, "wb") as f:
        f.write(img_bytes)
