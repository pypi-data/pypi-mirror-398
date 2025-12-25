# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  http-helper
# FileName:     reponse_handle_utils.py
# Description:  http响应处理工具模块
# Author:       ASUS
# CreateDate:   2025/11/24
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re


def get_html_title(html: str) -> str:
    # 使用正则表达式提取目标字符串
    pattern = '<title>(.*?)</title>'
    match = re.search(pattern, html)
    if match:
        title = match.group(1)
    else:
        title = "Abnormal HTML document structure"
    return title
