"""数据加载模块，支持通过goosefs或API获取数据集信息和bag路径"""
import os
import json
import shutil
from typing import List, Dict, Any, Tuple

import requests

from data_pipeline.py_api.api_utils import (
    get_download_url_by_data_id,
    get_all_data_from_dataset,
)


def check_config_for_loading_dataset(config: dict):
    read_dataset_file = config.get("read_dataset_file")
    if read_dataset_file is None:
        raise ValueError("配置中未设置read_dataset_file")

    if read_dataset_file and not config.get("goosefs_path"):
        raise ValueError("read_dataset_file为true，但配置中未设置goosefs_path")


def load_dataset(dataset_id: str, config: dict) -> List[Dict[str, Any]]:
    """
    根据配置选择从文件或API加载dataset

    Args:
        dataset_id: dataset ID

    Returns:
        metadata列表
    """
    if config.get("read_dataset_file"):
        file_path = os.path.join(config.get("goosefs_path"), f"dataset_conf/{dataset_id}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset文件不存在: {file_path}")

        with open(file_path, "r", encoding='utf-8') as f:
            return json.load(f)
    else:
        return get_all_data_from_dataset(dataset_id)


def _get_file_key(metadata: Dict[str, Any]) -> str:
    """从metadata中提取文件key"""
    files = metadata.get("cos_storage", {}).get("files", [])
    if len(files) == 0:
        raise ValueError("failed to get cos_storage.files")

    key = files[0].get("key", "")
    if not key:
        raise ValueError("failed to get cos_storage.files[0].key")

    return key


def _get_name_data_id_type(metadata: Dict[str, Any]) -> Tuple[str, str, str]:
    key = _get_file_key(metadata)

    metadata_name = metadata.get("metadata", {}).get("name")
    if not metadata_name:
        raise ValueError("failed to get metadata.name")

    data_id = metadata.get("metadata", {}).get("data_id")
    if not data_id:
        raise ValueError("failed to get metadata.data_id")

    return metadata_name, data_id, key.split(".")[-1]


def get_path_on_goosefs_or_goosefsx(metadata: Dict[str, Any], config: dict) -> str:
    key = _get_file_key(metadata)[1:]

    goosefs_filepath = os.path.join(config.get("goosefs_path"), key)
    if not os.path.exists(goosefs_filepath):
        raise FileNotFoundError(f"goosefs文件不存在: {goosefs_filepath}")

    if not config.get("use_goosefsx_as_cache"):
        return goosefs_filepath

    metadata_name, data_id, file_type = _get_name_data_id_type(metadata)
    goosefsx_filepath = os.path.join(config.get("bag_cache_dir"), f"{metadata_name}_{data_id}.{file_type}")
    shutil.copy(goosefs_filepath, goosefsx_filepath)
    return goosefsx_filepath


def download_bag_from_url(metadata: Dict[str, Any], config: dict) -> str:
    metadata_name, data_id, file_type = _get_name_data_id_type(metadata)

    download_url = get_download_url_by_data_id(data_id)
    if not download_url:
        raise ValueError(f"无法获取下载链接: {metadata_name}_{data_id}")

    save_path = os.path.join(config.get("bag_download_dir"), f'{metadata_name}_{data_id}.{file_type}')
    with requests.get(download_url, stream=True) as response:
        response.raise_for_status()

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    return save_path


def check_config_for_loading_data(config: dict):
    download_bag = config.get("download_bag")
    if download_bag is None:
        raise ValueError("配置中未设置download_bag")

    bag_download_dir = config.get("bag_download_dir")
    if download_bag and not bag_download_dir:
        raise ValueError("download_bag为true，但配置中未设置bag_download_dir")
    os.makedirs(bag_download_dir, exist_ok=True)

    if not download_bag:
        if not config.get("goosefs_path"):
            raise ValueError("download_bag为false，但配置中未设置goosefs_path")

        use_goosefsx_as_cache = config.get("use_goosefsx_as_cache")
        if use_goosefsx_as_cache is None:
            raise ValueError("download_bag为false，但配置中未设置use_goosefsx_as_cache")

        bag_cache_dir = config.get("bag_cache_dir")
        if use_goosefsx_as_cache and not bag_cache_dir:
            raise ValueError("use_goosefsx_as_cache为true，但配置中未设置bag_cache_dir")
        os.makedirs(bag_cache_dir, exist_ok=True)


# Return path of the raw data
def load_data(metadata: Dict[str, Any], config: dict) -> str:
    """
    根据配置选择下载或使用goosefs路径加载数据

    Args:
        metadata: metadata对象

    Returns:
        bag文件路径
    """
    if config.get("download_bag"):
        return download_bag_from_url(metadata, config)
    else:
        return get_path_on_goosefs_or_goosefsx(metadata, config)
