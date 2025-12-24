# !/usr/bin/env python
# -*-coding:utf-8 -*-
import unittest
import uuid

BASE_URL = "http://192.168.13.160:30052"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTI1NDQwNDksImlhdCI6MTc1MTkzOTI0OSwidWlkIjoyfQ.MfB_7LK5oR3RAhga3jtgcvJqYESeUPLbz8Bc_y3fouc"


class TestArtifact(unittest.TestCase):
    def test_artifact(self):
        from src.aihub.client import Client

        client = Client(base_url=BASE_URL, token=TOKEN)
        run_id = uuid.uuid4().hex
        client.artifact.create_artifact(
            local_path="data/video_data/00000.jpg",
            artifact_path="video_data/00000.jpg",
            run_id=run_id,
        )
        client.artifact.download_artifacts(
            run_id=run_id, artifact_path="video_data/00000.jpg", local_dir="data/output"
        )
        client.artifact.create_artifacts(
            local_dir="data/video_data",
            artifact_path="video_data2",
            run_id=run_id,
        )
        client.artifact.download_artifacts(
            run_id=run_id, artifact_path="video_data2", local_dir="data/output2"
        )
