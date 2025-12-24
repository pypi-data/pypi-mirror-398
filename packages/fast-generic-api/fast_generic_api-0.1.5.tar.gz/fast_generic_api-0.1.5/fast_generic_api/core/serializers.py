# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午6:30
# @Author  : fzf
# @FileName: serializers.py
# @Software: PyCharm
from typing import Any
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


class CoreSerializers(BaseModel):
    """基础 BaseModel，提供 `.data` 属性返回 JSON 可序列化内容"""

    model_config = {"from_attributes": True}

    @property
    def data(self) -> Any:
        """返回可直接用于 FastAPI JSONResponse 的 dict"""
        return jsonable_encoder(self)

    @classmethod
    async def from_tortoise(cls, instance):
        data = await instance.to_dict()

        # 自动处理 ManyToMany 字段
        m2m_fields = instance._meta.m2m_fields

        for field in m2m_fields:
            related_objs = await getattr(instance, field).all()
            data[field] = [obj.id for obj in related_objs]

        return cls(**data)