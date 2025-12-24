# Intellif AI-Hub SDK

**Intellif AI-Hub** 官方 Python 开发包。  
一个 `Client` 对象即可完成数据集管理、标注统计、任务中心等常见操作，无需手写 HTTP 请求。

```
aihub_sdk/
├─ pyproject.toml
├─ requirements.txt
├─ src/aihub/
│   ├─ client.py
│   ├─ exceptions.py
│   ├─ models/…
│   ├─ services/…
│   └─ utils/…
└─ tests/
```

---

## 💻 安装

```bash
# PyPI 安装
pip install intellif-aihub
# 运行环境：Python ≥ 3.9
```

---

## 🚀 快速上手

```python
from aihub import Client

BASE  = "http://192.168.13.160:30021"
TOKEN = "eyJhb..."   # 或设置环境变量：export AI_HUB_TOKEN=...

with Client(base_url=BASE, token=TOKEN) as cli:
    # 1. 同时创建数据集 + 版本（上传本地 ZIP）
    ds_id, ver_id, tag = cli.dataset_management.create_dataset_and_version(
        dataset_name="cats",
        is_local_upload=True,
        local_file_path="/data/cats.zip",
        version_description="first release",
    )
    print("数据集标识:", tag)  # 输出：cats/V1

    # 2. 下载数据集
    cli.dataset_management.run_download(
        dataset_version_name=tag,
        local_dir="/tmp/cats",
        worker=8,
    )

    # 3. 获取标注平台全局统计
    stats = cli.labelfree.get_project_global_stats("cat-project")
    print("总标注数:", stats.global_stats.total_annotations)
```

---

## 🌍 环境变量

| 变量                       | 作用                                      | 默认值                           |
|----------------------------|-------------------------------------------|----------------------------------|
| `AI_HUB_TOKEN`             | API 鉴权 Token（可不在 `Client` 中显式传入） | –                                |

---

## 📦 打包 & 发布

项目采用 PEP 517 / `pyproject.toml` 构建规范。

```bash
# 1️⃣ 构建 wheel / sdist
python -m pip install --upgrade build
python -m build                 # 生成 dist/*.whl dist/*.tar.gz

# 2️⃣ 本地验证
pip install --force-reinstall dist/*.whl
python -c "import aihub, sys; print('SDK 版本:', aihub.__version__)"

# 3️⃣ 发布到 PyPI 或私有仓库
python -m pip install --upgrade twine
twine upload dist/*
```

文档调试：

```bash
mkdocs serve
```

构建文档镜像：

```bash
docker build -t 192.168.14.129:80/library/aihub/sdk_doc:latest -f doc.Dockerfile .
```
---