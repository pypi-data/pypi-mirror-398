# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午3:46
# @Author  : fzf
# @FileName: decorator.py
# @Software: PyCharm

def api_meta(summary: str = None, description: str = None,
             tags: list = None, responses: dict = None):
    def decorator(func):
        if summary:
            setattr(func, "_summary", summary)
        if description:
            setattr(func, "_description", description)
        if tags:
            setattr(func, "_tags", tags)
        if responses:
            setattr(func, "_responses", responses)
        return func
    return decorator