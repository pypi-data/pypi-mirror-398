BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTk4MjQwMjUsImlhdCI6MTc1OTIxOTIyNSwidWlkIjoxfQ.w2ISB8w_1wPVBuLNNc5_zRHtM_ZENTi1vNvPN9t6-9U"


from src.aihub.client import Client
from src.aihub.models.notebook_management import ListImagesReq, HardwareType, AppType, ListNotebooksReq, GetNotebookReq, GetConfigsReq, StartNotebookReq, StopNotebookReq, EditNotebookReq, DeleteNotebookReq, CreateNotebookReq

client = Client(base_url=BASE_URL, token=TOKEN)

def test_list_images():
    resp = client.notebook_management.list_images(
        ListImagesReq(app_type=AppType.Notebook, hardware_type=HardwareType.CPU)
    )

    for image in resp.data:
        print(image.model_dump_json(indent=4))

def test_list_notebooks():
    resp = client.notebook_management.list_notebooks(ListNotebooksReq(app_type=AppType.Notebook, hardware_type=HardwareType.CPU))
    for notebook in resp.data:
        print(notebook.model_dump_json(indent=4))

def test_get_notebook():
    resp = client.notebook_management.get_notebook(GetNotebookReq(id=26))
    print(resp.model_dump_json(indent=4))


def test_get_configs():
    resp = client.notebook_management.get_configs(GetConfigsReq())
    print(resp.model_dump_json(indent=4))

def test_start_notebook():
    client.notebook_management.start_notebook(StartNotebookReq(id=13))
    print("start notebook success")

def test_stop_notebook():
    client.notebook_management.stop_notebook(StopNotebookReq(id=13))
    print("stop notebook success")

def test_edit_notebook():
    client.notebook_management.edit_notebook(EditNotebookReq(
        id=26,
        image_id=3,
        sku_cnt=1,
        storage_ids=[1,],
        shm=1,
        resolution="1920x1000"
    ))
    print("edit notebook success")

def test_delete_notebook():
    client.notebook_management.delete_notebook(DeleteNotebookReq(id=26))
    print("delete notebook success")

def test_create_notebook():
    resp = client.notebook_management.create_notebook(CreateNotebookReq(
        app_type=AppType.VncSsh,
        hardware_type=HardwareType.CPU,
        image_id=3,
        sku_cnt=1,
        storage_ids=[1,],
        shm=1,
        resolution="1920x1000"
    ))
    print(f"create notebook success, id: {resp.id}")