from __future__ import annotations

import unittest
import uuid

from src.aihub.client import Client
from src.aihub.models.data_warehouse import *

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ5MDY2ODUwODAsImlhdCI6MTc1MzA4NTA4MCwidWlkIjoxMH0.89bQ66BJDGoCzwxuxugRRt9acPFKEVmgqXMZX7ApnhM"


class TestDataWarehouse(unittest.TestCase):
    def test_search(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        search_name = f"sdk_search_{uuid.uuid4().hex[:6]}"
        sid = client.data_warehouse.create_search(
            CreateSearchRequest(
                type=1,
                name=search_name,
                sql="select id,name from test_ljn_import_data where score > 30",
            )
        )
        self.assertGreater(sid, 0)

        lst = client.data_warehouse.list_searches(ListSearchRequest(name=search_name))
        self.assertTrue(any(s.id == sid for s in lst.data))

        detail = client.data_warehouse.get_search(sid)
        self.assertEqual(detail.name, search_name)
