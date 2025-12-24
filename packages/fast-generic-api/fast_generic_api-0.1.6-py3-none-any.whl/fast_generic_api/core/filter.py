# -*- coding: utf-8 -*-
from tortoise.queryset import QuerySet
from typing import Dict, Any, Callable, Optional, Union
from tortoise.expressions import Q


class CoreFilterSet:
    """
    基础 Tortoise FilterSet
    - 支持自定义方法过滤
    - 支持精确匹配 / 多选 __in
    - 自动排除 offset、limit 等分页参数
    初始化时直接返回过滤后的 QuerySet。
    """

    model = None
    filters: Dict[str, Callable[[QuerySet, str, Any], QuerySet]] = {}
    exclude_fields = {"offset", "limit"}
    search_fields = []

    def __new__(cls, queryset: QuerySet, data: Optional[Union[Dict[str, Any], Any]] = None):
        """
        __new__ 在初始化时直接返回过滤后的 QuerySet，而不是实例
        """
        if cls.model is None:
            raise ValueError("model must be defined")
        if not isinstance(queryset, QuerySet):
            raise TypeError("queryset must be a Tortoise QuerySet")
        data_dict = dict(data or {})

        qs = queryset
        for field, value in data_dict.items():
            if field in cls.exclude_fields:
                continue
            qs = cls._apply_filter(qs, field, value)
        return qs

    @classmethod
    def _apply_filter(cls, qs: QuerySet, field: str, value: Any):
        if value is None:
            return qs

        # ⭐ 这里一定要用 cls.filters，而不是 CoreFilterSet.filters
        if field in cls.filters:
            return cls.filters[field](qs, field, value)

        # 多选
        if isinstance(value, str) and ',' in value:
            return qs.filter(**{f"{field}__in": value.split(',')})

        if isinstance(value, (list, tuple)):
            return qs.filter(**{f"{field}__in": value})

        return qs.filter(**{field: value})

    @classmethod
    def filter_search(cls, qs, value):
        if not value:
            return qs

        q_obj = Q()

        for field in cls.search_fields:
            q_obj |= Q(**{f"{field}__contains": value})

        return qs.filter(q_obj)