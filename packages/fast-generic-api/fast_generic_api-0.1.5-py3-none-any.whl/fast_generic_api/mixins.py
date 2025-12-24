# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:49
# @Author  : fzf
# @FileName: mixins.py
# @Software: PyCharm
from typing import Any, Optional
from fastapi import Request, Body
from fast_generic_api.core import status
from fast_generic_api.core.response import CoreResponse

from tortoise.fields.relational import ManyToManyFieldInstance


class BaseMixin:
    """提供通用工具方法"""
    action = None

    def _get_lookup_kwargs(self, uuid: Any) -> dict:
        lookup_field = self.lookup_url_kwarg or self.lookup_field
        return {lookup_field: uuid}

    # 排除m2m
    def exclude_m2m(self, data):
        """过滤 M2M 字段，只保留普通字段"""
        return {
            k: v for k, v in data.items()
            if not isinstance(self.queryset._meta.fields_map.get(k), ManyToManyFieldInstance)}

    async def handle_m2m(self, obj, data_dict: dict, replace: bool = True, ):
        """
        专门处理 ManyToMany 关系
        obj: 已创建的对象
        data_dict: 输入数据字典，包含可能的 M2M 字段
        """
        for field_name, ids in data_dict.items():
            # 先获取字段定义
            field_def = obj._meta.fields_map.get(field_name)
            if isinstance(field_def, ManyToManyFieldInstance) and ids:
                # 获取关联的模型类
                related_model = field_def.related_model
                # 获取实例列表
                instances = await related_model.filter(id__in=ids)
                # 添加到 M2M
                m2m_relation = getattr(obj, field_name)
                if replace:
                    # 替换现有 M2M
                    await m2m_relation.clear()
                # 添加新的关联
                if instances:
                    await m2m_relation.add(*instances)


class CreateModelMixin(BaseMixin):
    action = "create"

    async def create(self, data: Any = Body(...)) -> CoreResponse:
        """通用创建方法"""
        data_dict = self.input_data(data)

        obj = await self.queryset.create(**self.exclude_m2m(data_dict))
        await self.handle_m2m(obj, data_dict)
        serializer = await self.get_serializer(await obj.to_dict())
        return CoreResponse(serializer)


class ListModelMixin(BaseMixin):
    action = "list"

    async def list(self, request: Request) -> CoreResponse:
        """获取对象列表，支持过滤、排序和分页"""
        qs = self.get_queryset()
        if self.ordering:
            qs = qs.order_by(*self.ordering)
        if self.filter_class:
            qs = self.filter_class(qs, request.query_params)
        if self.pagination_class:
            serializer = await self.pagination_class.get_paginated_response(request, qs, self.get_serializer)
            return CoreResponse(serializer)
        serializer = await self.get_serializer(qs, many=True)
        return CoreResponse(serializer)


class RetrieveModelMixin(BaseMixin):
    action = "retrieve"

    async def retrieve(self, uuid: Any) -> CoreResponse:
        """获取单个对象（自动返回 M2M）"""
        self.kwargs.update(self._get_lookup_kwargs(uuid))
        instance = await self.get_object()
        serializer = await self.get_serializer(instance)
        return CoreResponse(serializer)


class UpdateModelMixin(BaseMixin):
    action = "update"

    async def update(self, uuid: Any, data: Any = Body(...)) -> CoreResponse:
        """更新对象（全量或部分更新）"""
        self.kwargs.update(self._get_lookup_kwargs(uuid))
        obj = await self.get_object()

        data_dict = self.input_data(data)
        await obj.update_from_dict(self.exclude_m2m(data_dict)).save()
        await self.handle_m2m(obj, data_dict)
        serializer = await self.get_serializer(await obj.to_dict())
        return CoreResponse(serializer)


class PartialUpdateModelMixin(UpdateModelMixin):
    action = "partial_update"

    # 复用 UpdateModelMixin 的 update 方法即可
    async def partial_update(self, uuid: Any, data: Any = Body(...)) -> CoreResponse:
        """部分更新对象"""
        return await self.update(uuid, data)


class DestroyModelMixin(BaseMixin):
    action = "destroy"

    async def destroy(self, uuid: Any) -> CoreResponse:
        """软删除对象"""
        self.kwargs.update(self._get_lookup_kwargs(uuid))
        instance = await self.get_object()
        await self.perform_destroy(instance)
        return CoreResponse(data=instance.uuid,
                            status_code=status.HTTP_204_NO_CONTENT)

    async def perform_destroy(self, instance):
        """执行软删除操作"""
        await instance.update_from_dict({"is_deleted": True}).save()
