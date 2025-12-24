from __future__ import annotations

import json
import os


class ReportService:
    @staticmethod
    def report_envs():
        pod_namespace = os.environ.get('POD_NAMESPACE', '')
        pod_name = os.environ.get('POD_NAME', '')
        if not pod_namespace or not pod_name:
            return
        env_file_path = f'/var/mtp/log/{pod_namespace}/{pod_name}/env'
        try:
            os.makedirs(os.path.dirname(env_file_path), exist_ok=True)
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(dict(os.environ)))
        except Exception as e:
            print(f"[report_envs] 写入失败: {e}", flush=True)
