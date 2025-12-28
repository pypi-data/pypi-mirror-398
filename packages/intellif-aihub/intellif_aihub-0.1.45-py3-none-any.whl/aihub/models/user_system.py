from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ======================================================================
# COMMON
# ======================================================================


class Role(BaseModel):
    """角色"""

    id: int = Field(description="角色ID")
    name: str = Field(description="角色名称")
    role_type: int = Field(alias="role_type", description="角色类型，1-管理员，2-普通")
    menu_ids: Optional[List[int]] = Field(None, alias="menu_ids", description="菜单列表")


class Menu(BaseModel):
    """菜单"""

    id: int = Field(description="菜单ID")
    name: str = Field(description="菜单名称")
    parent: int = Field(description="父级菜单ID")
    auth: str = Field(description="权限")


class TreeMenu(BaseModel):
    """菜单（树形）"""

    id: int = Field(description="菜单ID")
    name: str = Field(description="菜单名称")
    parent: int = Field(description="父级菜单ID")
    auth: str = Field(description="权限")
    children: Optional[List["TreeMenu"]] = Field(None, description="子菜单")
    roles: Optional[List[Role]] = Field(None, description="绑定角色列表")


class TagBrief(BaseModel):
    """标签"""

    id: int = Field(description="标签ID")
    name: str = Field(description="标签名称")


# ======================================================================
# ------------------------------- AUTH ---------------------------------
# ======================================================================


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(alias="username", description="用户名")
    password: str = Field(alias="password", description="密码")


class LoginResponse(BaseModel):
    """登录返回"""

    id: int = Field(alias="id", description="用户ID")
    token: str = Field(alias="token", description="JWT Token")


class SignupRequest(BaseModel):
    """注册请求"""

    username: str = Field(alias="username", description="用户名")
    password: str = Field(alias="password", description="密码")
    nickname: str = Field(alias="nickname", description="昵称")
    email: str = Field(alias="email", description="邮箱")
    role_ids: List[int] = Field(alias="role_ids", description="角色列表")


class SignupResponse(BaseModel):
    """注册返回"""

    id: int = Field(alias="id", description="用户ID")


# ======================================================================
# ------------------------------- MENU ---------------------------------
# ======================================================================
class ListMenusRequest(BaseModel):
    """查询菜单列表请求"""

    need_roles: Optional[bool] = Field(None, alias="need_roles", description="是否同时返回菜单绑定的角色信息")


class ListMenusResponse(BaseModel):
    """查询菜单列表返回"""

    menus: List[TreeMenu] = Field(alias="menus", description="菜单树列表")


class CreateMenuRequest(BaseModel):
    """创建菜单请求"""

    name: str = Field(alias="name", description="菜单名称")
    parent: int = Field(alias="parent", description="父级菜单ID")
    auth: str = Field(alias="auth", description="权限")
    role_ids: Optional[List[int]] = Field(None, alias="role_ids", description="绑定的角色列表")


class CreateMenuResponse(BaseModel):
    """创建菜单返回"""

    id: int = Field(alias="id", description="菜单ID")


class UpdateMenuRequest(BaseModel):
    """更新菜单请求"""

    name: Optional[str] = Field(None, alias="name", description="菜单名称")
    parent: Optional[int] = Field(None, alias="parent", description="父级菜单ID")
    auth: str = Field(alias="auth", description="权限")
    role_ids: Optional[List[int]] = Field(None, alias="role_ids", description="绑定的角色列表")


class GetMenuRolesResponse(BaseModel):
    """获取菜单角色返回"""

    role_ids: List[int] = Field(alias="role_ids", description="菜单绑定的角色ID")


class SetMenuRolesRequest(BaseModel):
    """设置菜单角色请求"""

    role_ids: List[int] = Field(alias="role_ids", description="绑定的角色列表")


class SearchMenusRequest(BaseModel):
    """搜索菜单请求"""

    page_size: int = Field(20, alias="page_size", description="单页条数")
    page_num: int = Field(1, alias="page_num", description="页码")
    name: Optional[str] = Field(None, description="名称过滤")
    parent_ids: Optional[List[int]] = Field(None, alias="parent_ids", description="父级ID过滤")
    auth: Optional[str] = Field(None, description="权限过滤")
    menu_ids: Optional[List[int]] = Field(None, alias="menu_ids", description="菜单过滤")


class SearchMenusResponse(BaseModel):
    """搜索菜单返回"""

    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="单页条数")
    page_num: int = Field(alias="page_num", description="当前页")
    data: List[Menu] = Field(description="菜单列表")


# ======================================================================
# ------------------------------- ROLE ---------------------------------
# ======================================================================


class CreateRoleRequest(BaseModel):
    """创建角色请求"""

    id: Optional[int] = Field(None, description="自定义ID")
    name: str = Field(description="角色名称")
    role_type: int = Field(alias="role_type", description="角色类型")
    menu_ids: Optional[List[int]] = Field(None, alias="menu_ids", description="绑定菜单")


class CreateRoleResponse(BaseModel):
    """创建角色返回"""

    id: int = Field(description="角色ID")


class UpdateRoleRequest(BaseModel):
    """更新角色请求"""

    name: Optional[str] = Field(None, description="角色名称")
    role_type: Optional[int] = Field(None, alias="role_type", description="角色类型")
    menu_ids: Optional[List[int]] = Field(None, alias="menu_ids", description="菜单列表")


class GetRoleMenusResponse(BaseModel):
    """获取角色菜单返回"""

    menu_ids: List[int] = Field(alias="menu_ids", description="菜单ID")


class SetRoleMenusRequest(BaseModel):
    """设置角色菜单请求"""

    menu_ids: List[int] = Field(alias="menu_ids", description="菜单ID")


class ListRolesRequest(BaseModel):
    """查询角色列表请求"""

    page_size: int = Field(20, alias="page_size", description="单页条数")
    page_num: int = Field(1, alias="page_num", description="页码")
    role_type: Optional[int] = Field(None, alias="role_type", description="角色类型过滤")


class ListRolesResponse(BaseModel):
    """查询角色列表返回"""

    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="单页条数")
    page_num: int = Field(alias="page_num", description="当前页")
    data: List[Role] = Field(description="角色列表")


class SearchRolesRequest(BaseModel):
    """搜索角色请求"""

    page_size: int = Field(20, alias="page_size", description="单页条数")
    page_num: int = Field(1, alias="page_num", description="页码")
    name: Optional[str] = Field(None, description="名字过滤")
    role_ids: Optional[List[int]] = Field(None, alias="role_ids", description="角色ID过滤")
    menu_ids: Optional[List[int]] = Field(None, alias="menu_ids", description="菜单ID过滤")


class SearchRolesResponse(BaseModel):
    """搜索角色返回"""

    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="单页条数")
    page_num: int = Field(alias="page_num", description="当前页")
    data: List[Role] = Field(description="角色列表")


# ======================================================================
# ------------------------------- USER ---------------------------------
# ======================================================================


class User(BaseModel):
    """用户信息"""

    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    nickname: str = Field(description="昵称")
    email: str = Field(description="邮箱")
    roles: Optional[List[Role]] = Field(None, alias="roles", description="角色列表")
    status: int = Field(description="状态，1-可用，2-禁用")
    tags: Optional[List[TagBrief]] = Field(None, alias="tags", description="标签")
    created_at: int = Field(alias="created_at", description="创建时间戳（ms）")


class ListUsersRequest(BaseModel):
    """查询用户列表请求"""

    page_size: int = Field(20, alias="page_size", description="单页条数")
    page_num: int = Field(1, alias="page_num", description="页码")
    search_key: Optional[str] = Field(None, alias="search_key", description="搜索关键字")


class ListUsersResponse(BaseModel):
    """查询用户列表返回"""

    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="单页条数")
    page_num: int = Field(alias="page_num", description="当前页")
    data: List[User] = Field(description="用户列表")


class CreateUserRequest(BaseModel):
    """创建用户请求"""

    id: int = Field(description="用户id")
    username: str = Field(description="用户名")
    password: str = Field(description="密码")
    nickname: str = Field(description="昵称")
    email: str = Field(description="邮箱")
    role_ids: Optional[List[int]] = Field(None, alias="role_ids", description="角色列表")
    created_at: Optional[int] = Field(None, alias="created_at", description="创建时间戳")
    updated_at: Optional[int] = Field(None, alias="updated_at", description="更新时间戳")
    status: Optional[int] = Field(None, description="状态，1-可用，2-禁用")
    tag_ids: Optional[List[int]] = Field(None, alias="tag_ids", description="标签列表")


class CreateUserResponse(BaseModel):
    """创建用户返回"""

    id: int = Field(description="用户ID")


class UpdateUserRequest(BaseModel):
    """更新用户请求"""

    username: Optional[str] = Field(None, description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, description="密码")
    role_ids: Optional[List[int]] = Field(default_factory=list, alias="role_ids", description="角色列表")
    status: Optional[int] = Field(None, description="状态，1-可用，2-禁用")
    tag_ids: Optional[List[int]] = Field(default_factory=list, alias="tag_ids", description="标签列表")


class SetUserRolesRequest(BaseModel):
    """设置用户角色请求"""

    role_ids: List[int] = Field(alias="role_ids", description="角色列表")


class GetUserMenusResponse(BaseModel):
    """获取用户菜单返回"""

    menus: List[TreeMenu] = Field(description="菜单树")


class SearchUsersRequest(BaseModel):
    """搜索用户请求"""

    page_size: int = Field(20, alias="page_size", description="单页条数")
    page_num: int = Field(1, alias="page_num", description="当前页")
    username: Optional[str] = Field(None, description="用户名过滤")
    nickname: Optional[str] = Field(None, description="昵称过滤")
    email: Optional[str] = Field(None, description="邮箱过滤")
    user_ids: Optional[List[int]] = Field(None, alias="user_ids", description="用户ID过滤")
    role_ids: Optional[List[int]] = Field(None, alias="role_ids", description="角色ID过滤")
    role_names: Optional[List[str]] = Field(None, alias="role_names", description="角色名过滤")
    status: Optional[int] = Field(None, description="状态过滤")


class SearchUsersResponse(BaseModel):
    """搜索用户返回"""

    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="单页条数")
    page_num: int = Field(alias="page_num", description="当前页")
    data: Optional[List[User]] = Field(description="用户列表")


# 此行放在文件末尾，否则序列化报错
TreeMenu.model_rebuild()
