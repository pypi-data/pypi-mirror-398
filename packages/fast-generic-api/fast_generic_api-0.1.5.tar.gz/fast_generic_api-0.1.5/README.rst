🚀 Fast Auto Framework
======================

.. raw:: html

   <div align="center">

**一个功能强大、设计优雅的FastAPI自动化API框架，提供类似Django REST Framework的体验**

**简体中文** | `English <README.en.md>`_

.. image:: https://img.shields.io/badge/Python-3.11+-blue.svg
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/FastAPI-0.100+-green.svg
   :target: https://fastapi.tiangolo.com/
.. image:: https://img.shields.io/badge/Tortoise%20ORM-0.20+-orange.svg
   :target: https://tortoise-orm.readthedocs.io/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: LICENSE

`📖 快速开始 <#-快速开始>`_ • `🏗️ 核心功能 <#-核心功能>`_ • `📚 API参考 <#-api参考>`_ • `🔧 高级配置 <#-高级配置>`_ • `🤝 贡献 <#-贡献>`_

.. raw:: html

   </div>

🌟 为什么选择 Fast Auto Framework？
===================================

Fast Auto Framework 是一个专为FastAPI设计的自动化API框架，提供了类似Django REST Framework的开发体验，让你能够快速构建高质量的API服务。

.. raw:: html

   <div align="center">

+--------------+----------------+-------------+----------------+
| 🎯 **CRUD自动化** | ⚡ **快速开发** | 🛡️ **类型安全** | 📈 **扩展性强** |
+==============+================+=============+================+
| 内置完整CRUD操作 | 几行代码即可创建API | 基于Pydantic和Python类型注解 | 模块化设计，易于扩展 |
+--------------+----------------+-------------+----------------+

.. raw:: html

   </div>

✨ 核心功能
=========

🔧 CRUD操作自动化
-----------------
- **CreateModelMixin** - 创建资源
- **ListModelMixin** - 列表查询（支持分页和过滤）
- **RetrieveModelMixin** - 详情查询
- **UpdateModelMixin** - 完整更新
- **PartialUpdateModelMixin** - 部分更新
- **DestroyModelMixin** - 软删除功能

📦 通用API视图
--------------
- **GenericAPIView** - 统一的API视图基类
- **自动路由注册** - 基于类属性的自动路由生成
- **权限控制** - 灵活的权限依赖注入
- **序列化器支持** - 支持不同操作使用不同序列化器

🌐 响应处理
-----------
- **统一响应格式** - 标准化的API响应结构
- **分页响应** - 内置分页信息
- **错误处理** - 统一的错误响应格式
- **JSON序列化** - 自动处理Pydantic和datetime类型

🏗️ 高级功能
-----------
- **过滤系统** - 灵活的查询过滤
- **分页支持** - LimitOffset分页机制
- **UUID支持** - 自定义UUID作为主键
- **排序功能** - 支持多字段排序

🛠️ 技术栈
========

+----------+----------------+----------------+
| 组件     | 技术选型       | 版本要求        |
+==========+================+================+
| **Web框架** | FastAPI        | 0.100+         |
+----------+----------------+----------------+
| **ORM**  | Tortoise ORM   | 0.20+          |
+----------+----------------+----------------+
| **序列化** | Pydantic       | 2.0+           |
+----------+----------------+----------------+
| **数据库** | 支持多种数据库 | -              |
+----------+----------------+----------------+
| **Python版本** | Python       | 3.11+          |
+----------+----------------+----------------+

📁 项目结构
==========

.. code-block::

   fast_auto_framework/
   ├── __init__.py                 # 包初始化
   ├── mixins.py                   # CRUD混入类
   ├── generics.py                 # 通用API视图
   ├── core/                       # 核心模块
   │   ├── __init__.py            # 核心模块初始化
   │   ├── exceptions.py          # 自定义异常
   │   ├── filter.py              # 过滤系统
   │   ├── pagination.py          # 分页功能
   │   ├── response.py            # 统一响应
   │   └── status.py              # HTTP状态码
   ├── example/                    # 示例代码
   │   ├── __init__.py            # 示例模块初始化
   │   └── example.py             # 使用示例
   └── README.md                   # 项目文档

🚀 快速开始
==========

⚡ 安装依赖
-----------

.. code-block:: bash

   # 克隆项目
   git clone <your-repo-url>
   cd fast_auto_framework

   # 安装依赖
   pip install fastapi tortoise-orm pydantic

💻 基础使用
----------

1. 创建模型
~~~~~~~~~~~

.. code-block:: python

   from tortoise.models import Model
   from tortoise import fields

   class User(Model):
       id = fields.IntField(pk=True)
       username = fields.CharField(max_length=100, unique=True)
       email = fields.CharField(max_length=100, unique=True)
       is_deleted = fields.BooleanField(default=False)
       created_at = fields.DatetimeField(auto_now_add=True)
       updated_at = fields.DatetimeField(auto_now=True)

       class Meta:
           table = "users"

2. 创建序列化器
~~~~~~~~~~~~~~~

.. code-block:: python

   from pydantic import BaseModel
   from datetime import datetime

   class UserBase(BaseModel):
       username: str
       email: str

   class UserCreate(UserBase):
       pass

   class UserUpdate(UserBase):
       pass

   class UserInDB(UserBase):
       id: int
       created_at: datetime
       updated_at: datetime
       is_deleted: bool

       class Config:
           from_attributes = True

3. 创建API视图
~~~~~~~~~~~~~

.. code-block:: python

   from fastapi import APIRouter
   from fast_auto_framework.generics import GenericAPIView
   from fast_auto_framework import mixins
   from models import User
   from serializers import UserInDB, UserCreate, UserUpdate

   # 创建路由
   router = APIRouter(prefix="/api", tags=["Users"])

   class UserViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    GenericAPIView):
       router = router
       prefix = "/users"
       queryset = User
       serializer_class = UserInDB
       serializer_create_class = UserCreate
       serializer_update_class = UserUpdate
       ordering = ["-created_at"]
       lookup_field = "id"

4. 启动应用
~~~~~~~~~~

.. code-block:: python

   from fastapi import FastAPI
   from api.views import router

   app = FastAPI(title="Fast Auto Framework Example")
   app.include_router(router)

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000)

📚 API参考
=========

可用的Mixin类
------------

CreateModelMixin
~~~~~~~~~~~~~~~
- **方法**: ``POST /{prefix}/create/``
- **功能**: 创建新资源
- **请求体**: 根据 ``serializer_create_class`` 定义
- **响应**: 创建的资源详情

ListModelMixin
~~~~~~~~~~~~~
- **方法**: ``GET /{prefix}/list/``
- **功能**: 获取资源列表
- **查询参数**: 
  - ``limit``: 每页数量（默认：10，最大：1000）
  - ``offset``: 偏移量（默认：0）
  - 其他过滤字段
- **响应**: 分页的资源列表

RetrieveModelMixin
~~~~~~~~~~~~~~~~~
- **方法**: ``GET /{prefix}/{lookup_field}/``
- **功能**: 获取单个资源详情
- **路径参数**: 
  - ``{lookup_field}``: 资源标识符
- **响应**: 资源详情

UpdateModelMixin
~~~~~~~~~~~~~~~
- **方法**: ``PUT /{prefix}/{lookup_field}/``
- **功能**: 完整更新资源
- **路径参数**: 
  - ``{lookup_field}``: 资源标识符
- **请求体**: 根据 ``serializer_update_class`` 定义
- **响应**: 更新后的资源详情

PartialUpdateModelMixin
~~~~~~~~~~~~~~~~~~~~~~
- **方法**: ``PATCH /{prefix}/{lookup_field}/``
- **功能**: 部分更新资源
- **路径参数**: 
  - ``{lookup_field}``: 资源标识符
- **请求体**: 部分字段（可选）
- **响应**: 更新后的资源详情

DestroyModelMixin
~~~~~~~~~~~~~~~~
- **方法**: ``DELETE /{prefix}/{lookup_field}/``
- **功能**: 软删除资源（设置 ``is_deleted=True``）
- **路径参数**: 
  - ``{lookup_field}``: 资源标识符
- **响应**: 成功状态（204 No Content）

GenericAPIView配置
-----------------

+------------------------+------------+--------------------------+----------------+-------+
| 属性                   | 类型       | 描述                     | 默认值         |       |
+========================+============+==========================+================+=======+
| ``router``             | APIRouter  | FastAPI路由实例          | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``prefix``             | str        | API路径前缀              | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``queryset``           | Model      | 数据库模型               | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``serializer_class``   | BaseModel  | 默认序列化器             | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``serializer_create_class`` | BaseModel | 创建操作序列化器     | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``serializer_update_class`` | BaseModel | 更新操作序列化器     | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``lookup_field``       | str        | 资源查找字段             | "pk"           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``ordering``           | list       | 默认排序字段             | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``pagination_class``   | class      | 分页类                   | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``filter_class``       | class      | 过滤类                   | None           |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``permissions``        | list       | 权限依赖列表             | []             |       |
+------------------------+------------+--------------------------+----------------+-------+
| ``loop_uuid_field``    | str        | UUID字段名               | None           |       |
+------------------------+------------+--------------------------+----------------+-------+

🔧 高级配置
==========

自定义过滤
----------

.. code-block:: python

   from fast_auto_framework.core.filter import FilterSet
   from models import User

   class UserFilter(FilterSet):
       model = User
       exclude_fields = {"offset", "limit"}
       
       # 自定义过滤方法
       filters = {
           "username": lambda qs, field, value: qs.filter(username__icontains=value),
           "email": lambda qs, field, value: qs.filter(email__icontains=value),
       }

   # 在视图中使用
   class UserViewSet(...):
       filter_class = UserFilter

自定义分页
----------

.. code-block:: python

   from fast_auto_framework.core.pagination import LimitOffsetPagination

   class CustomPagination(LimitOffsetPagination):
       default_limit = 20
       max_limit = 500

   # 在视图中使用
   class UserViewSet(...):
       pagination_class = CustomPagination

权限控制
--------

.. code-block:: python

   from fastapi import Depends
   from fastapi.security import OAuth2PasswordBearer
   from fast_auto_framework.core.exceptions import HTTPPermissionException

   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

   async def get_current_active_user(token: str = Depends(oauth2_scheme)):
       # 验证token逻辑
       if not is_valid_token(token):
           raise HTTPPermissionException
       return user

   # 在视图中使用
   class UserViewSet(...):
       permissions = [Depends(get_current_active_user)]

📦 依赖
======

- **FastAPI** - Web框架
- **Tortoise ORM** - 异步ORM
- **Pydantic** - 数据验证和序列化

🤝 贡献
======

欢迎提交Issue和Pull Request来帮助改进这个项目！

贡献流程
--------

1. Fork项目
2. 创建功能分支 (``git checkout -b feature/AmazingFeature``)
3. 提交更改 (``git commit -m 'Add some AmazingFeature'``)
4. 推送到分支 (``git push origin feature/AmazingFeature``)
5. 开启Pull Request

📄 许可证
========

本项目采用MIT许可证 - 详情请查看 `LICENSE <LICENSE>`_ 文件

💖 致谢
======

- 感谢 `FastAPI <https://fastapi.tiangolo.com/>`_ 提供优秀的Web框架
- 感谢 `Django REST Framework <https://www.django-rest-framework.org/>`_ 提供设计灵感
- 感谢所有使用和支持这个项目的开发者！

.. raw:: html

   <blockquote>
      <p>🚀 <strong>开始使用</strong>：按照快速开始指南，5分钟内即可构建强大的API服务！</p>
   </blockquote>