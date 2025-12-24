from __future__ import annotations

import unittest
import uuid

from src.aihub.client import Client
from src.aihub.models.user_system import *

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ5MDY2ODUwODAsImlhdCI6MTc1MzA4NTA4MCwidWlkIjoxMH0.89bQ66BJDGoCzwxuxugRRt9acPFKEVmgqXMZX7ApnhM"


class TestUserSystem(unittest.TestCase):
    def test_auth(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        uname = f"ut_{uuid.uuid4().hex[:6]}"
        signup_resp = client.user_system.signup(
            SignupRequest(
                username=uname, password="Pa55w0rd!", nickname="UTest", email=f"{uname}@example.com", role_ids=[]
            )
        )
        self.assertGreater(signup_resp.id, 0)
        login_resp = client.user_system.login(LoginRequest(username=uname, password="Pa55w0rd!"))
        self.assertTrue(login_resp.token)

    def test_menu(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        name = f"menu_{uuid.uuid4().hex[:6]}"
        menu_id = client.user_system.create_menu(CreateMenuRequest(name=name, parent=0, auth="stop"))
        self.assertGreater(menu_id, 0)

        new_name = name + "_upd"
        client.user_system.update_menu(menu_id, UpdateMenuRequest(name=new_name, parent=0, auth="stop"))

        menu = client.user_system.get_menu(menu_id)
        self.assertEqual(menu.name, new_name)

        menus = client.user_system.list_menus(need_roles=False)
        self.assertTrue(any(m.id == menu_id for m in menus.menus))

        client.user_system.set_menu_roles(menu_id=menu_id, role_ids=[1])
        menu_roles = client.user_system.get_menu_roles(menu_id=menu_id)
        self.assertEqual(menu_roles, [1])

        client.user_system.delete_menu(menu_id)
        menus2 = client.user_system.list_menus(need_roles=False)
        self.assertFalse(any(m.id == menu_id for m in menus2.menus))

    def test_role(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        name = f"role_{uuid.uuid4().hex[:6]}"
        role_id = client.user_system.create_role(CreateRoleRequest(name=name, role_type=1))
        self.assertGreater(role_id, 0)

        new_name = name + "_upd"
        client.user_system.update_role(role_id, UpdateRoleRequest(name=new_name))

        role = client.user_system.get_role(role_id)
        self.assertEqual(role.name, new_name)

        roles = client.user_system.list_roles(ListRolesRequest())
        self.assertTrue(any(r.id == role_id for r in roles.data))

        search_payload = SearchRolesRequest(role_ids=[role_id])
        search_resp = client.user_system.search_roles(search_payload)
        self.assertEqual(len(search_resp.data), 1)
        self.assertEqual(search_resp.data[0].id, role_id)

        client.user_system.set_role_menus(role_id=role_id, menu_ids=[1])
        role_menus = client.user_system.get_role_menus(role_id=role_id)
        self.assertEqual(role_menus, [1])

        client.user_system.delete_role(role_id)
        roles2 = client.user_system.list_roles(ListRolesRequest())
        self.assertFalse(any(r.id == role_id for r in roles2.data))

    def test_user(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        uname = f"user_{uuid.uuid4().hex[:6]}"
        uid = client.user_system.create_user(
            CreateUserRequest(
                id=3836,  # 这里有主键要求
                username=uname,
                password="U123456!",
                nickname="UTest",
                email=f"{uname}@example.com",
            )
        )
        self.assertGreater(uid, 0)

        client.user_system.update_user(uid, UpdateUserRequest(nickname="UTest2"))

        user = client.user_system.get_user(uid)
        self.assertEqual(user.nickname, "UTest2")

        users = client.user_system.list_users(ListUsersRequest())
        self.assertTrue(any(u.id == uid for u in users.data))

        search_payload = SearchUsersRequest(user_ids=[uid])
        search_resp = client.user_system.search_users(search_payload)
        self.assertEqual(len(search_resp.data), 1)
        self.assertEqual(search_resp.data[0].id, uid)

        uid_from_search_one = client.user_system.search_one(SearchUsersRequest(nickname="UTest2"))
        self.assertEqual(uid_from_search_one, uid)

        client.user_system.set_user_roles(uid, SetUserRolesRequest(role_ids=[1]))

        menus = client.user_system.get_user_menus(uid)
        self.assertIsInstance(menus, list)

        client.user_system.delete_user(uid)
        users2 = client.user_system.list_users(ListUsersRequest())
        self.assertFalse(any(u.id == uid for u in users2.data))

    def test_search_one(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        uid = client.user_system.search_one(
            nickname="admin",
        )
        self.assertGreater(uid, 0)
        # users = client.user_system.search_users(SearchUsersRequest(nickname="admin"))
        # print(users)
