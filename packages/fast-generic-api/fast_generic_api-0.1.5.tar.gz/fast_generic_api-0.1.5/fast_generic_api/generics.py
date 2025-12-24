# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:42
# @Author  : fzf
# @FileName: generics.py
# @Software: PyCharm
from typing import Optional, Type, List

from fastapi import APIRouter, Request
from tortoise.models import Model, ModelMeta
from tortoise.queryset import QuerySet

from fast_generic_api import mixins
from fast_generic_api.core.exceptions import HTTPException, HTTPPermissionException


async def get_object_or_404(queryset, **filter_kwargs):
    obj = await queryset.filter(**filter_kwargs).first()
    if not obj:
        raise HTTPException
    return obj


class GenericAPIView:
    prefix: Optional[str] = None
    router: Optional[APIRouter] = None
    loop_uuid_field: Optional[str] = None
    permissions: list = []

    queryset: Type[Model] = None
    action: Optional[str] = None

    pagination_class = None

    filter_fields: List[Type] = []
    filter_class = None

    serializer_class = None
    serializer_create_class = None
    serializer_update_class = None

    lookup_field: str = "uuid"
    lookup_url_kwarg: Optional[str] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not cls.router or not cls.prefix:
            return

        instance = cls()

        # 映射方法到 HTTP 方法
        method_map = {
            "destroy_many": "DELETE",
            "list": "GET",
            "retrieve": "GET",
            "create": "POST",
            "update": "PUT",
            "partial_update": "PATCH",
            "destroy": "DELETE",
        }

        for method_name, http_method in method_map.items():
            if not hasattr(instance, method_name):
                continue

            endpoint = getattr(instance, method_name)

            # 读取装饰器注入的元信息
            summary = getattr(endpoint, "_summary", None)
            description = getattr(endpoint, "_description", None)
            tags = getattr(endpoint, "_tags", None)
            responses = getattr(endpoint, "_responses", None)

            # 构造路径
            path = cls.prefix
            if method_name in ["list", "create"]:
                path += f"/{method_name}/"
            elif method_name == "destroy_many":
                path += f"/destroy/many/"
            elif method_name in ["retrieve", "update", "partial_update", "destroy"]:
                param_name = cls.loop_uuid_field or "pk"
                path += f"/{{{param_name}}}/"

            # 注册路由（补充元参数）
            cls.router.add_api_route(
                path,
                endpoint,
                methods=[http_method],
                name=method_name,
                summary=summary,
                description=description,
                tags=tags,
                responses=None,
                dependencies=cls.permissions,
            )

    def __init__(self, request=None, **kwargs):
        self.request = request
        self.kwargs = kwargs
        self.format_kwarg = None

    # ================================
    # queryset、对象获取相关
    # ================================
    def get_queryset(self):
        assert self.queryset is not None, (
            f"'{self.__class__.__name__}' 必须提供 queryset 或重写 get_queryset()"
        )
        queryset = self.queryset

        if isinstance(queryset, ModelMeta):
            queryset = queryset.all()
        return queryset

    async def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            f'视图 {self.__class__.__name__} 需要 URL 参数 "{lookup_url_kwarg}"'
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = await get_object_or_404(queryset, **filter_kwargs)
        return obj



    # ================================
    # serializer
    # ================================
    async def get_serializer(self, instance, many: bool = False):
        serializer_class = self.get_serializer_class()
        # QuerySet 先执行
        if isinstance(instance, QuerySet):
            instance = await instance

        if many:
            return [await serializer_class.from_tortoise(obj) for obj in instance]
        return await serializer_class.from_tortoise(instance)

    def get_serializer_class(self):
        """根据 action 返回对应 Pydantic 类"""
        return getattr(self, "serializer_class")

    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
        }

    # ================================
    # queryset 过滤
    # ================================
    def filter_queryset(self, queryset):
        return queryset

    # ================================
    # 分页处理
    # ================================
    @property
    def paginator(self):
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    # def paginate_queryset(self, queryset):
    #     if self.paginator is None:
    #         return None
    #     return self.paginator.paginate_queryset(queryset, self.request, view=self)
    #
    # def get_paginated_response(self, data):
    #     assert self.paginator is not None
    #     return self.paginator.get_paginated_response(data)

    # ================================
    # 权限
    # ================================
    # async def check_object_permissions(self, obj):
    #     for perm in self.permissions:
    #         if not await perm(self.request, obj):
    #             raise HTTPPermissionException

    def input_data(self, input_data) -> dict:
        """
        将输入数据（Pydantic 模型或 dict）转换为 dict
        """
        if not isinstance(input_data, dict):
            processed_data = input_data.model_dump(exclude_unset=True)
        else:
            processed_data = input_data
        return processed_data

class CreateViewSet(mixins.CreateModelMixin,
                    GenericAPIView):
    """
    Concrete view for creating a model instance.
    """


class ListViewSet(mixins.ListModelMixin,
                  GenericAPIView):
    """
    Concrete view for listing a queryset.
    """
    pass


class RetrieveViewSet(mixins.RetrieveModelMixin,
                      GenericAPIView):
    """
    Concrete view for retrieving a model instance.
    """


class DestroyAPIView(mixins.DestroyModelMixin,
                     GenericAPIView):
    """
    Concrete view for deleting a model instance.
    """

class UpdateViewSet(mixins.PartialUpdateModelMixin,
                    GenericAPIView):
    """
    Concrete view for updating a model instance.
    """


class ListCreateViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        GenericAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """


class RetrieveUpdateViewSet(mixins.RetrieveModelMixin,
                            mixins.PartialUpdateModelMixin,
                            GenericAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """

class RetrieveDestroyViewSet(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             GenericAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """



class RetrieveUpdateDestroyViewSet(mixins.RetrieveModelMixin,
                                   mixins.DestroyModelMixin,
                                   mixins.PartialUpdateModelMixin,
                                   GenericAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """

class CustomViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass
