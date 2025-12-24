# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""用户系统服务模块

封装 **Auth / Menu / Role / User** 四大类接口：

- **统一登录 / 注册**
- **菜单**（增删改查 & 角色绑定）
- **角色**（增删改查 & 菜单绑定）
- **用户**（增删改查 & 角色 / 菜单查询）
"""
from __future__ import annotations

from typing import List

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.user_system import (
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
    Menu,
    TreeMenu,
    ListMenusResponse,
    CreateMenuRequest,
    CreateMenuResponse,
    UpdateMenuRequest,
    GetMenuRolesResponse,
    Role,
    ListRolesRequest,
    ListRolesResponse,
    CreateRoleRequest,
    CreateRoleResponse,
    UpdateRoleRequest,
    GetRoleMenusResponse,
    SearchRolesRequest,
    SearchRolesResponse,
    User,
    ListUsersRequest,
    ListUsersResponse,
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    SetUserRolesRequest,
    GetUserMenusResponse,
    SearchUsersRequest,
    SearchUsersResponse,
)


class UserSystemService:
    """用户系统服务"""

    def __init__(self, http: httpx.Client):
        self._auth = _Auth(http)
        self._menu = _Menu(http)
        self._role = _Role(http)
        self._user = _User(http)

    # ==================================================
    #  AUTH 一级方法
    # ==================================================
    def login(self, payload: LoginRequest) -> LoginResponse:
        """登录

        Args:
            payload: 登录请求体，包含 *username* / *password*

        Returns:
            LoginResponse: 登录成功后返回用户 ID 与 token
        """
        return self._auth.login(payload)

    def signup(self, payload: SignupRequest) -> SignupResponse:
        """注册

        Args:
            payload: 注册请求体

        Returns:
            SignupResponse: 新用户 ID
        """
        return self._auth.signup(payload)

    # ==================================================
    #  MENU 一级方法
    # ==================================================
    def list_menus(self, need_roles: bool = False) -> ListMenusResponse:
        """查询所有菜单

        Args:
            need_roles: 是否返回每个菜单已绑定角色

        Returns:
            ListMenusResponse
        """
        return self._menu.list(need_roles)

    def get_menu(self, menu_id: int) -> Menu:
        """获取单个菜单详情

        Args:
            menu_id: 菜单 ID

        Returns:
            Menu: 菜单对象（含父级、权限等字段）
        """
        return self._menu.get(menu_id)

    def create_menu(self, payload: CreateMenuRequest) -> int:
        """新建菜单

        Args:
            payload: 菜单创建请求体，包含名称 / 父级 / 权限标识等

        Returns:
            int: 新菜单的 ID
        """
        return self._menu.create(payload)

    def update_menu(self, menu_id: int, payload: UpdateMenuRequest) -> None:
        """编辑菜单

        Args:
            menu_id: 待更新菜单 ID
            payload: 更新字段（名称 / 父级 / 权限 / 角色绑定）
        """
        self._menu.update(menu_id, payload)

    def delete_menu(self, menu_id: int) -> None:
        """删除菜单

        Args:
            menu_id: 目标菜单 ID
        """
        self._menu.delete(menu_id)

    def get_menu_roles(self, menu_id: int) -> List[int]:
        """查询菜单已绑定的角色

        Args:
            menu_id: 菜单 ID

        Returns:
            list[int]: 角色 ID 列表
        """
        return self._menu.get_roles(menu_id)

    def set_menu_roles(self, menu_id: int, role_ids: List[int]) -> None:
        """重新绑定菜单角色

        Args:
            menu_id: 菜单 ID
            role_ids: 需绑定的角色 ID 列表
        """
        self._menu.set_roles(menu_id, role_ids)

    # ==================================================
    #  ROLE 一级方法
    # ==================================================
    def list_roles(self, payload: ListRolesRequest) -> ListRolesResponse:
        """分页查询角色

        Args:
            payload: 分页与过滤条件

        Returns:
            ListRolesResponse: 角色分页结果
        """
        return self._role.list(payload)

    def get_role(self, role_id: int) -> Role:
        """获取角色详情

        Args:
            role_id: 角色 ID

        Returns:
            Role: 角色对象，含菜单绑定信息（可选）
        """
        return self._role.get(role_id)

    def create_role(self, payload: CreateRoleRequest) -> int:
        """新建角色

        Args:
            payload: 角色创建请求体，支持初始菜单绑定

        Returns:
            int: 新角色 ID
        """
        return self._role.create(payload)

    def update_role(self, role_id: int, payload: UpdateRoleRequest) -> None:
        """编辑角色

        Args:
            role_id: 角色 ID
            payload: 更新字段（名称 / 类型 / 菜单绑定）
        """
        self._role.update(role_id, payload)

    def delete_role(self, role_id: int) -> None:
        """删除角色

        Args:
            role_id: 目标角色 ID
        """
        self._role.delete(role_id)

    def get_role_menus(self, role_id: int) -> List[int]:
        """获取角色已绑定菜单

        Args:
            role_id: 角色 ID

        Returns:
            list[int]: 菜单 ID 列表
        """
        return self._role.get_menus(role_id)

    def set_role_menus(self, role_id: int, menu_ids: List[int]) -> None:
        """设置角色菜单绑定

        Args:
            role_id: 角色 ID
            menu_ids: 菜单 ID 列表
        """
        self._role.set_menus(role_id, menu_ids)

    def search_roles(self, payload: SearchRolesRequest) -> SearchRolesResponse:
        """条件检索角色

        Args:
            payload: 检索条件（名称 / 角色 ID / 菜单 ID 等）

        Returns:
            SearchRolesResponse: 检索结果
        """
        return self._role.search(payload)

    # ==================================================
    #  USER 一级方法
    # ==================================================
    def list_users(self, payload: ListUsersRequest) -> ListUsersResponse:
        """分页查询用户

        Args:
            payload: 分页与关键词过滤

        Returns:
            ListUsersResponse: 用户分页结果
        """
        return self._user.list(payload)

    def get_user(self, user_id: int) -> User:
        """获取用户详情

        Args:
            user_id: 用户 ID

        Returns:
            User: 用户完整信息（含角色 / 标签等）
        """
        return self._user.get(user_id)

    def create_user(self, payload: CreateUserRequest) -> int:
        """新建用户

        Args:
            payload: 用户创建请求体

        Returns:
            int: 新用户 ID
        """
        return self._user.create(payload)

    def update_user(self, user_id: int, payload: UpdateUserRequest) -> None:
        """编辑用户

        Args:
            user_id: 用户 ID
            payload: 更新字段（昵称 / 邮箱 / 角色 / 标签等）
        """
        self._user.update(user_id, payload)

    def delete_user(self, user_id: int) -> None:
        """删除用户

        Args:
            user_id: 目标用户 ID
        """
        self._user.delete(user_id)

    def set_user_roles(self, user_id: int, payload: SetUserRolesRequest) -> None:
        """重新绑定用户角色

        Args:
            user_id: 用户 ID
            payload: 角色 ID 列表封装
        """
        self._user.set_roles(user_id, payload)

    def get_user_menus(
        self,
        user_id: int,
        parent_id: int | None = None,
        auth: str | None = None,
    ) -> List[TreeMenu]:
        """查询用户可见菜单

        Args:
            user_id: 用户 ID
            parent_id: 仅返回指定父级菜单下的子菜单（可选）
            auth: 仅返回特定权限标识的菜单（可选）

        Returns:
            list[TreeMenu]: 菜单树
        """
        return self._user.get_menus(user_id, parent_id=parent_id, auth=auth)

    def search_users(self, payload: SearchUsersRequest) -> List[User]:
        """条件搜索用户

        Args:
            payload: 搜索条件（用户名 / 邮箱 / 角色等）

        Returns:
            SearchUsersResponse: 搜索结果
        """
        resp = self._user.search(payload)
        return resp.data

    def search_one(self, nickname: str) -> int:
        """搜索单个用户并返回其 ID

        Args:
            nickname: 用户昵称


        Returns:
            int: 命中的用户 ID

        Raises:
            APIError: 未找到用户时抛出
        """
        req = SearchUsersRequest(
            nickname=nickname,
        )
        return self._user.search_one(req)

    @property
    def auth(self) -> _Auth:
        return self._auth

    @property
    def menu(self) -> _Menu:
        return self._menu

    @property
    def role(self) -> _Role:
        return self._role

    @property
    def user(self) -> _User:
        return self._user


class _Auth:
    _base = "/api/v1/auth"

    def __init__(self, http: httpx.Client):
        self._http = http

    def login(self, req: LoginRequest) -> LoginResponse:
        try:
            resp = self._http.post(
                f"{self._base}/login",
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)

            wrapper = APIWrapper[LoginResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def signup(self, req: SignupRequest) -> SignupResponse:
        try:
            resp = self._http.post(
                f"{self._base}/signup",
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[SignupResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError


class _Menu:
    _base = "/api/v1/menus"

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, need_roles: bool) -> ListMenusResponse:
        try:
            resp = self._http.get(self._base, params={"need_roles": str(need_roles).lower()})
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[ListMenusResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get(self, menu_id: int) -> Menu:
        try:
            resp = self._http.get(f"{self._base}/{menu_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[Menu].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def create(self, req: CreateMenuRequest) -> int:
        try:
            resp = self._http.post(self._base, json=req.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[CreateMenuResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def update(self, menu_id: int, req: UpdateMenuRequest) -> None:
        try:
            resp = self._http.put(f"{self._base}/{menu_id}", json=req.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def delete(self, menu_id: int) -> None:
        try:
            resp = self._http.delete(f"{self._base}/{menu_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get_roles(self, menu_id: int) -> List[int]:
        try:
            resp = self._http.get(f"{self._base}/{menu_id}/roles")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[GetMenuRolesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.role_ids
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def set_roles(self, menu_id: int, role_ids: List[int]) -> None:
        try:
            resp = self._http.put(f"{self._base}/{menu_id}/roles", json={"role_ids": role_ids})
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError


class _Role:
    _base = "/api/v1/roles"
    _search = "/api/v1/search-roles"

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, req: ListRolesRequest) -> ListRolesResponse:
        try:
            resp = self._http.get(self._base, params=req.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[ListRolesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get(self, role_id: int) -> Role:
        try:
            resp = self._http.get(f"{self._base}/{role_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[Role].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def create(self, req: CreateRoleRequest) -> int:
        try:
            resp = self._http.post(self._base, json=req.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[CreateRoleResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def update(self, role_id: int, req: UpdateRoleRequest) -> None:
        try:
            resp = self._http.put(f"{self._base}/{role_id}", json=req.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def delete(self, role_id: int) -> None:
        try:
            resp = self._http.delete(f"{self._base}/{role_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get_menus(self, role_id: int) -> List[int]:
        try:
            resp = self._http.get(f"{self._base}/{role_id}/menus")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[GetRoleMenusResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.menu_ids
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def set_menus(self, role_id: int, menu_ids: List[int]) -> None:
        try:
            resp = self._http.put(f"{self._base}/{role_id}/menus", json={"menu_ids": menu_ids})
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def search(self, req: SearchRolesRequest) -> SearchRolesResponse:
        try:
            resp = self._http.post(self._search, json=req.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[SearchRolesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError


class _User:
    _base = "/api/v1/users"
    _search = "/api/v1/search-users"

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, req: ListUsersRequest) -> ListUsersResponse:
        try:
            resp = self._http.get(self._base, params=req.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, user_id: int) -> User:
        try:
            resp = self._http.get(f"{self._base}/{user_id}")
            wrapper = APIWrapper[User].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, req: CreateUserRequest) -> int:
        try:
            resp = self._http.post(self._base, json=req.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateUserResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def update(self, user_id: int, req: UpdateUserRequest) -> None:
        try:
            resp = self._http.put(f"{self._base}/{user_id}", json=req.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete(self, user_id: int) -> None:
        try:
            resp = self._http.delete(f"{self._base}/{user_id}")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def set_roles(self, user_id: int, req: SetUserRolesRequest) -> None:
        try:
            resp = self._http.put(
                f"{self._base}/{user_id}/roles", json=req.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_menus(self, user_id: int, parent_id: int | None = None, auth: str | None = None) -> List[TreeMenu]:
        try:
            params = {}
            if parent_id is not None:
                params["parent_id"] = parent_id
            if auth:
                params["auth"] = auth

            resp = self._http.get(f"{self._base}/{user_id}/menus", params=params)
            wrapper = APIWrapper[GetUserMenusResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.menus
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def search(self, req: SearchUsersRequest) -> SearchUsersResponse:
        try:
            resp = self._http.post(self._search, json=req.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[SearchUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def search_one(self, req: SearchUsersRequest) -> int:
        resp = self.search(req)

        if resp.data is None:
            raise APIError(f"no user found")

        if len(resp.data) > 1:
            raise APIError("more than one user found")

        for user in resp.data:
            if user.nickname == req.nickname:
                return user.id
        raise APIError("no user found")
