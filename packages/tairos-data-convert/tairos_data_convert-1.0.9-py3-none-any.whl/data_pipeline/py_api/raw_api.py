import requests

DEFAULT_ENDPOINT = "https://roboticsx-data.woa.com"


def get_error_message_from_exception(e):
    if "Trpc-Error-Msg" in e.response.headers:
        return e.response.headers["Trpc-Error-Msg"]
    return str(e)

# =============== DataCollection Service ===============


def get_config(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/GetConfig"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def upload_task_compiler(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/UploadTaskCompiler"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_task_compiler(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/Expose/ListTaskCompiler"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_task_compiler(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/UpdateTaskCompiler"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def delete_task_compiler(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/DeleteTaskCompiler"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_sub_task_compiler_ids(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/GetSubTaskCompilerIds"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_task_sample(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/GetTaskSample"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_task_samples(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/ListTaskSamples"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_collection_task(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/ListCollectionTask"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def submit_collection_task(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/SubmitCollectionTask"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def delete_collection_task(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/DeleteCollectionTask"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def set_collector_name(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/SetCollectorName"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_task_sample_by_collection_task_id(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/Expose/GetTaskSampleByCollectionTaskId"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def register_collector(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/RegisterCollector"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_collectors(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/Expose/ListCollectors"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def deactivate_collector(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/DeactivateCollector"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def activate_collector(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/ActivateCollector"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_labeling_status(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/UpdateLabelingStatus"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def create_task_compiler_set(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/CreateTaskCompilerSet"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_task_compiler_sets(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/ListTaskCompilerSets"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def delete_task_compiler_set(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/DeleteTaskCompilerSet"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def add_task_compilers_to_set(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/AddTaskCompilersToSet"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def remove_task_compilers_from_set(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/trpc.data_pipeline.collection.DataCollection/RemoveTaskCompilersFromSet"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)

# =============== DataManagement Service ===============


def list_data(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/list_data"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_data(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/get_data"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_download_url(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/get_download_url"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def export_qlabel_dataset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/export_qlabel_dataset"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_data_label(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/update_data_label"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def delete_data(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/delete_data"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def aggregate_data(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/aggregate_data"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_data_metadata(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/update_metadata"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def add_to_dataset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/add_to_dataset"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def remove_from_dataset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/collection/remove_from_dataset"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_asset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/asset/list_asset"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_asset_metadata(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/asset/update_metadata"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_ai_model(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/ai_model/list_ai_model"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def create_dataset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/dataset/create"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_dataset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/dataset/get"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_datasets(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/dataset/list"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def delete_dataset(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_management/dataset/delete"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)

# =============== EvalTask Service ===============


def list_eval_tasks(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/list"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def create_eval_task(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/create"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_task_status(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/update_status"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def update_collector_names(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/update_collector_names"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def overall_statistics(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/overall_stats"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def task_compiler_statistics(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/task_compiler_stats"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def list_my_eval_tasks(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/eval_task/list_my_tasks"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)

# =============== Account Service ===============


def get_userinfo(api_endpoint=DEFAULT_ENDPOINT, headers=None):
    url = f"{api_endpoint}/v1/account/get_userinfo"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


def get_current_user_role(api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/v1/role/GetCurrentUserRole"
    try:
        response = requests.post(url, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)


# =============== DataAccess Service ===============

def send_data(payload, api_endpoint=DEFAULT_ENDPOINT, headers=None, params=None):
    url = f"{api_endpoint}/data_access/send_data"
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        return True, response.json()
    except requests.exceptions.RequestException as e:
        return False, get_error_message_from_exception(e)
