# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     windows_utils.py
# Description:  windows窗口的操作工具模块
# Author:       ASUS
# CreateDate:   2025/11/27
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import os
import base64
from airtest.cli.parser import cli_setup
from airtest.core.api import touch, auto_setup, Template

allow_btn_base64_str = 'iVBORw0KGgoAAAANSUhEUgAAATYAAABACAIAAAAf0syWAAAACXBIWXMAAB2HAAAdhwGP5fFlAAAEKElEQVR42u2dv08UQRSAr1MSKxMLCv4DS7W6ilha+gdILAxcQi0kWFyBwVhR2EJCBZUJNhIblCPEXC6n2LheLjl/hEsMxAvkUODAl0wclp3Zmb1f3CZ+L18j7E7x1i9vZvfNkDkjCCLFkSEFBIGiBEH0WtGtRmUiWBgtzw4XclfWHwBAnxDFRLRcsCjSJVL0sHU0VV0eWh8jdwCXiUg3XV05Oj1xKfphv3bz/WOSBTAobhVnRMNYRUVicgQwWERDu6Kbv4KrzG8BBo1oqAvpBUVlwUp2ANKAyGhRNFvKkxqANHC3/NSi6I2NcVIDkAZGNictipIXgPSAogAoCgAoCoCiAICiAICiACgKACgKgKKQBrKl/FxttR/D3v80T3pRFLolaO7Ioynv19q9cfzzwtredtxv5VedDQsoCue8/FlUj2apvtHWjVPVZXVjoRFYL9g9PuhgWEBROOfFjzduzdzIXXF6a4GZ66IodIhMU5utP/JQZKJrvSCJXdpSsd38ObNcFIVu/fz2e9e6iVetJCPiWd8JyQjq4Url1D9s65BIfSOgKFzwKs5PR3m0jia2h6fKen2LoigKffFTUf53to2UXO+YEWPlLhHV/N+AjSgKLmR5qfwUi7yH1GiZ5WKvpZESao6PoigKbaw/E75obdfSuBKKoigKnuIZXh+u7W3LP8PInDZo7oRRXzXDES6MqtvBXE8u1TfiSjSKoii4FO3J3+fRy9c4RdW3Vmu7AoqiKPi7/MQxXSfVZxU1KRVEHkGVQbPlQDc5yAhqzqyu1y0KXvdQFEXBU0jNdaP5ULRycZ9hzG8wKIqi0BesNjoUVcXT7Z45AU4Y5uslQFEUbVtRb3lEURSFHu9xiTTodqkoE10UhZ6hmocie1xQFEXJS1pQPQaRDyQoiqLkJRXM1VatH1fcispd5pth0z3vWyVAUfCg2vrMnaJuRa0buCPuyRJX6jOKoih0ju5PMIXpRtFsKa/f6JqFFEVRFBKh+4SsRyIkUTSimf5qoha3cecVoSiKgh/d9Ld7fGDdjOZQVAqjWSEjByzIsHEbYlAURcFTPPXmFYdIuuFeZA47LNerSWxknalrsirLjj2oKIqi4JdTvSJyb+Z2dwhFDs7VF3sP40RRFAU7epu1iOo9iEhdX2gE+tAwvVlUbDRvV3u+kwyLoigKrnbcJBb1u99Q4FhdFAUAFAVAUQBAUQAURVEAFAUAFAX4DxQd2ZwkLwBpQGS0KHrv43NSA5AGREaLotPVFVIDkAZERouiX5r1a28fkh2AwXL93aNKs25RVOLZ11ckCGCwzH9/rZWMKnpy2rpTfEKOAAbF7eKMaBirqMRh60jmwUPrYyQL4DIR6aaqyyJg2MdM3ObgrUYlFyyOlmeHCzlyB9A/RDERbSJYEOlMEzNnBEGkOP4C+x6pJBF8uPMAAAAASUVORK5CYII='


def gen_allow_btn_image(image_name: str) -> None:
    # 1. 解码 Base64 成二进制数据
    image_data = base64.b64decode(allow_btn_base64_str)

    # 2. 写入文件（保存图片）
    with open(image_name, "wb") as image_file:
        image_file.write(image_data)


def windows_on_click(image_name: str, windows_title: str, is_delete: bool = True) -> None:
    if not cli_setup():
        auto_setup(__file__, logdir=False, devices=[f"Windows:///?title_re=^{windows_title}$"])

    touch(Template(filename=image_name, record_pos=(0, 0), resolution=(1920, 1080)))
    if is_delete is True:
        if os.path.exists(image_name):
            os.remove(image_name)
