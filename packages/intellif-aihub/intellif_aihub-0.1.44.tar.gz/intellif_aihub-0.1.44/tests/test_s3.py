# !/usr/bin/env python
# -*-coding:utf-8 -*-
import unittest


class TestS3(unittest.TestCase):
    def test_s3(self):
        import minio

        s3_client = minio.Minio(
            "192.168.14.17:9000",
            access_key="3CJS5Y9HIQX4VH17FO19",
            secret_key="sQBMcjTorqrqU4ZhVNCGHvX+MDiZergDRY+ytETF",
            secure=False,
            session_token="eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiIzQ0pTNVk5SElRWDRWSDE3Rk8xOSIsImV4cCI6MTc1MjY0ODQ3NSwicGFyZW50Ijoicm9vdCIsInNlc3Npb25Qb2xpY3kiOiJld29KQ1NKV1pYSnphVzl1SWpvZ0lqSXdNVEl0TVRBdE1UY2lMQW9KQ1NKVGRHRjBaVzFsYm5RaU9pQmJDZ2tKQ1hzS0NRa0pDU0pGWm1abFkzUWlPaUFpUVd4c2IzY2lMQW9KQ1FrSklrRmpkR2x2YmlJNklGc2ljek02S2lKZExBb0pDUWtKSWxKbGMyOTFjbU5sSWpvZ0ltRnlianBoZDNNNmN6TTZPam9xSWdvSkNRbDlDZ2tKWFFvSmZRPT0ifQ.c5YWZT-CQw_lsvYyNXHoWi-sqbM5xM4bbEZqZszdrXDiMkcNArzS3YGXBl7ZJFgzItmkEy4Mt7ys6u7NllSgOA",
        )
        res = s3_client.fput_object("dataset", "README.md", "README.md")
        print(res)
