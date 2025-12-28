# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     datetime_utils.py
# Description:  时间处理工具模块
# Author:       ASUS
# CreateDate:   2025/11/28
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from datetime import datetime


def get_current_dtstr() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")
