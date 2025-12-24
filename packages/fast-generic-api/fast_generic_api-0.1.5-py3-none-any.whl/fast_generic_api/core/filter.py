# -*- coding: utf-8 -*-
from tortoise.queryset import QuerySet
from typing import Dict, Any, Callable, Optional, Union


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
            qs = cls._apply_filter_static(qs, field, value)
        return qs

    @staticmethod
    def _apply_filter_static(qs: QuerySet, field: str, value: Any) -> QuerySet:
        """根据字段和值应用过滤"""
        if value is None:
            return qs

        # 自定义方法优先
        if field in CoreFilterSet.filters and callable(CoreFilterSet.filters[field]):
            return CoreFilterSet.filters[field](qs, field, value)

        # 字符串多选
        if isinstance(value, str) and ',' in value:
            return qs.filter(**{f"{field}__in": value.split(',')})

        # 列表/元组直接 __in
        if isinstance(value, (list, tuple)):
            return qs.filter(**{f"{field}__in": value})

        # 默认精确匹配
        return qs.filter(**{field: value})
