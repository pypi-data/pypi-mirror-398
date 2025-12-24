# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午1:21
# @Author  : fzf
# @FileName: pagination.py
# @Software: PyCharm
from fastapi import Request
from watchfiles import awatch


class CorePagination:
    default_limit = 10
    max_limit = 1000

    @classmethod
    def get_limit_offset(cls, request: Request):
        """
        从 query params 获取 limit 和 offset
        """
        limit = request.query_params.get("limit")
        offset = request.query_params.get("offset")

        # 默认值
        limit = int(limit) if limit and limit.isdigit() else cls.default_limit
        offset = int(offset) if offset and offset.isdigit() else 0

        # 限制最大 limit
        limit = min(limit, cls.max_limit)

        return limit, offset

    @classmethod
    async def get_paginated_response(cls, request: Request, queryset, serializer_fn):
        """
        真正执行分页函数
        """
        # 如果传进来的是 list，说明上游传错了，直接返回全部
        if isinstance(queryset, list):
            return {
                "total": len(queryset),
                "limit": len(queryset),
                "offset": 0,
                "results": serializer_fn(queryset, many=True)
            }

        # 下面是正常 QuerySet
        limit, offset = cls.get_limit_offset(request)
        total = await queryset.count()

        objs = await queryset.offset(offset).limit(limit)
        data = await serializer_fn(queryset, many=True)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": data,
        }