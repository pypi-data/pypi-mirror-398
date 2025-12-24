# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午1:50
# @Author  : fzf
# @FileName: exceptions.py
# @Software: PyCharm

class CoreException(Exception):
    code = 0
    detail = '基础错误'


class HTTPException(CoreException):
    code = 404
    detail = "Object not found"


class HTTPPermissionException(CoreException):
    code = 403
    detail = 'Permission denied'
