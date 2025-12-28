import json
import time
import base64
import hmac
import hashlib
from collections import defaultdict

from data_pipeline.py_api.raw_api import (
    list_task_compiler,
    list_collection_task,
    list_data,
    list_task_samples,
    list_eval_tasks,
    aggregate_data,
    get_task_sample,
    get_userinfo,
    get_current_user_role,
    send_data,
    get_download_url,
)

DEFAULT_ENDPOINT = "https://roboticsx-data.woa.com"


class RemoteServiceError(Exception):
    """调用远程服务失败"""
    pass


def sample_from_task_compiler_id(id, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    payload = {
        "task_compiler_id": id
    }
    success, result = get_task_sample(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)
    return result["task_sample"]


def get_task_sample_by_id(id, api_endpoint=DEFAULT_ENDPOINT):
    query = {
        "id": id
    }
    payload = {
        "query": json.dumps(query)
    }

    success, result = list_task_samples(payload, api_endpoint)
    if not success:
        raise RemoteServiceError(result)

    response_json = result
    if "task_samples" not in response_json or len(response_json["task_samples"]) == 0:
        raise ValueError(f"没有找到符合条件的task sample, id: {id}")

    return response_json["task_samples"][0]


def get_all_data_from_dataset(dataset_id, api_endpoint=DEFAULT_ENDPOINT):
    """
    获取所有数据
    :param dataset_id: 数据集ID
    :return: 数据
    """
    query = {
        "set_associations.set_id": dataset_id
    }
    payload = {
        "query": {
            "json": json.dumps(query)
        }
    }

    page = 1
    page_size = 100
    data = []
    while True:
        payload["page_info"] = {
            "page": page,
            "page_size": page_size,
        }
        success, result = list_data(payload, api_endpoint)
        if not success:
            raise RemoteServiceError(result)

        response_json = result
        if "data" in response_json and "data_list" in response_json["data"]:
            data.extend(response_json["data"]["data_list"])
        else:
            break

        if len(response_json["data"]["data_list"]) < page_size:
            break
        page += 1

    return data


def get_all_data_from_eval_task(task_id, api_endpoint=DEFAULT_ENDPOINT):
    """
    获取所有数据
    :param task_id: 评测任务ID
    :return: 数据
    """
    query = {
        "metadata.collection_task_id": task_id,
        "metadata.collect_info.task_status": {
            "$in": [1, 2]
        }
    }
    payload = {
        "query": {
            "json": json.dumps(query)
        }
    }

    page = 1
    page_size = 100
    data = []
    while True:
        payload["page_info"] = {
            "page": page,
            "page_size": page_size,
        }
        success, result = list_data(payload, api_endpoint)
        if not success:
            raise RemoteServiceError(result)

        response_json = result
        if "data" in response_json and "data_list" in response_json["data"]:
            data.extend(response_json["data"]["data_list"])
        else:
            break

        if len(response_json["data"]["data_list"]) < page_size:
            break
        page += 1

    return data


def get_task_compiler_by_id(id, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    query = {
        "id": id
    }
    payload = {
        "query": json.dumps(query),
        "page_info": {
            "page": 1,
            "page_size": 100,
        }
    }

    success, result = list_task_compiler(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)

    response_json = result
    if "task_compilers" not in response_json or len(response_json["task_compilers"]) == 0:
        raise ValueError(f"没有找到符合条件的task compiler, id: {id}")

    return response_json["task_compilers"][0]


def get_all_task_compilers(query, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    """
    获取所有task compiler
    :param query: 查询条件
    :return: task compiler
    """
    payload = {
        "query": json.dumps(query)
    }

    page = 1
    page_size = 100
    task_compilers = []

    while True:
        payload["page_info"] = {
            "page": page,
            "page_size": page_size,
        }
        success, result = list_task_compiler(payload, api_endpoint, headers)
        if not success:
            raise RemoteServiceError(result)

        response_json = result
        if "task_compilers" in response_json:
            task_compilers.extend(response_json["task_compilers"])

        if "task_compilers" not in response_json or len(response_json["task_compilers"]) < page_size:
            break
        page += 1

    return task_compilers


def get_all_collection_tasks(query, api_endpoint=DEFAULT_ENDPOINT):
    """
    获取所有collection task
    :param query: 查询条件
    :return: collection task
    """
    payload = {
        "query": json.dumps(query)
    }

    page = 1
    page_size = 100
    collection_tasks = []

    while True:
        payload["page_info"] = {
            "page": page,
            "page_size": page_size,
        }
        success, result = list_collection_task(payload, api_endpoint)
        if not success:
            raise RemoteServiceError(result)

        response_json = result
        if "collection_tasks" in response_json:
            collection_tasks.extend(response_json["collection_tasks"])

        if "collection_tasks" not in response_json or len(response_json["collection_tasks"]) < page_size:
            break
        page += 1

    return collection_tasks


def get_collection_task_by_id(id, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    query = {
        "id": id
    }
    payload = {
        "query": json.dumps(query)
    }
    success, result = list_collection_task(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)

    response_json = result
    if "collection_tasks" not in response_json or len(response_json["collection_tasks"]) == 0:
        raise ValueError(f"没有找到符合条件的collection task, id: {id}, response: {response_json}")

    return response_json["collection_tasks"][0]


def get_eval_task_by_id(id, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    query = {
        "id": id
    }
    payload = {
        "query": json.dumps(query),
        "page_info": {
            "page": 1,
            "page_size": 1
        }
    }
    success, result = list_eval_tasks(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)

    response_json = result["data"]
    if "eval_tasks" not in response_json or len(response_json["eval_tasks"]) == 0:
        raise ValueError(f"没有找到符合条件的eval task, id: {id}")

    return response_json["eval_tasks"][0]


def call_aggregate_data(match, group, sort, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    payload = {
        "aggregate_pipeline": [
            json.dumps({"$match": match}),
            json.dumps({"$group": group}),
            json.dumps({"$sort": sort}),
        ]
    }
    success, result = aggregate_data(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)

    return result.get("data", [])


def get_data_count_per_task_compiler_for_eval_task_id(id, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    match = {
        "metadata.collection_task_id": id,
        "metadata.collect_info.task_status": {
            "$in": [1, 2],
        },
    }
    group = {
        "_id": {
            "task_compiler_id": "$metadata.task_compiler_id",
        },
        "count": {
            "$sum": 1,
        },
    }
    sort = {
        "_id": 1,
    }
    results = call_aggregate_data(match, group, sort, api_endpoint, headers)

    task_compiler_id_to_count = defaultdict(int)
    for result in results:
        task_compiler_id = result.get("group_fields", {}).get("task_compiler_id", "")
        count = result.get("aggregate_fields", {}).get("count", 0)
        task_compiler_id_to_count[task_compiler_id] = count

    return task_compiler_id_to_count


def get_nickname_and_user_id(api_endpoint=DEFAULT_ENDPOINT, headers=None):
    success, result = get_userinfo(api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)
    return result.get("user_info", {}).get("nick", ""), result.get("user_info", {}).get("uid", "")


def get_tenant_id(api_endpoint=DEFAULT_ENDPOINT, headers=None):
    success, result = get_current_user_role(api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)
    return result.get("data", {}).get("tenant_id", "")


def add_data_pipeline_signature_headers(headers, secret_key, hostname):
    nonce = f"{time.time_ns()}{int(time.time())}"
    timestamp = f"{int(time.time())}"

    message = (
        f"caller_name={hostname}&cmd=2&device_id={hostname}"
        f"&nonce={nonce}&timestamp={timestamp}"
    )
    signature = base64.b64encode(hmac.new(
        key=secret_key.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).digest())

    headers.update({
        "trpc-trans-info": json.dumps({
            "X-Data-Pipeline-Signature": base64.b64encode(signature).decode(),
            "X-Data-Pipeline-Nonce": base64.b64encode(nonce.encode()).decode(),
            "X-Data-Pipeline-Timestamp": base64.b64encode(timestamp.encode()).decode(),
        })
    })


def send_data_with_signature(
    status, hostname, secret_key, task_id, task_compiler_id,
    api_endpoint=DEFAULT_ENDPOINT, headers=None
):
    if headers is None:
        headers = {}
    add_data_pipeline_signature_headers(headers, secret_key, hostname)

    payload = {
        "cmd": 2,
        "caller": {
            "name": hostname
        },
        "event": {
            "event_type": 1,
            "collecting_status": {
                "task_id": task_id,
                "task_compiler_id": task_compiler_id,
                "step": 2,
                "status": status,
            },
        },
        "device_auth": {
            "device_id": hostname,
            "device_token": hostname
        },
        "client_ts_ms": int(time.time() * 1000)
    }

    success, result = send_data(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)
    return result


def get_download_url_by_data_id(id, api_endpoint=DEFAULT_ENDPOINT, headers=None):
    payload = {
        "id": id
    }
    success, result = get_download_url(payload, api_endpoint, headers)
    if not success:
        raise RemoteServiceError(result)

    url = result.get("data", "")
    if not url:
        raise ValueError("获取的下载连接为空")

    return url

if __name__ == "__main__":
    data = get_collection_task_by_id("b6e11e9b-84c1-4984-bbb8-ae6be21d002e")
    from pprint import pprint
    pprint(data)
