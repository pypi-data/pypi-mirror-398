import concurrent
import os
from pathlib import Path

import yaml
from loguru import logger
import numpy as np

from data_pipeline.data_process.utils.data_load import (
    check_config_for_loading_dataset,
    check_config_for_loading_data,
    load_dataset,
    load_data,
)
from data_pipeline.data_process.utils.data_read import BagReader
from data_pipeline.data_process.utils.data_check import populate_dof_from_data
from data_pipeline.data_process.utils.output_dataset import Hdf5Dataset
from data_pipeline.data_process.utils.topic_mapping import get_data_for_value


def check_config(config: dict):
    if not config.get("dataset_id"):
        raise ValueError("配置中未设置dataset_id")

    if not config.get("fps"):
        raise ValueError("配置中未设置fps")

    output_dataset_dir = config.get("output_dataset_dir")
    if not output_dataset_dir:
        raise ValueError("配置中未设置output_dataset_dir")
    os.makedirs(output_dataset_dir, exist_ok=True)

    frame_structure = config.get("frame_structure")
    if not frame_structure:
        raise ValueError("配置中未设置frame_structure")

    if not config.get("convert_num_workers"):
        raise ValueError("配置中未设置convert_num_workers")

    if not config.get("data_load"):
        raise ValueError("配置中未设置data_load")
    check_config_for_loading_data(config.get("data_load"))
    check_config_for_loading_dataset(config.get("data_load"))


def get_frame_data(frame_structure_values_set: set, frame_structure: dict, topic_to_msg: dict, data_source: int):
    values_to_data = {}
    for v in frame_structure_values_set:
        values_to_data[v] = get_data_for_value(topic_to_msg, v, data_source)

    frame_data = {}
    for key, value in frame_structure.items():
        frame_data[key] = np.concatenate([values_to_data[v] for v in value["values"]], axis=0)

    return frame_data


def convert(metadata, config: dict):
    data_path = load_data(metadata, config.get("data_load"))

    data_source = metadata.get("metadata", {}).get("data_source", 0)
    frame_structure = config.get("frame_structure").copy()
    try:
        populate_dof_from_data(frame_structure, data_path, data_source)
    except (KeyError, ValueError) as e:
        return {
            "success": False,
            "error_message": str(e),
        }

    error_keys = []
    for key, value in frame_structure.items():
        if value["type"] == "float32" and value["dof"] == 0:
            error_keys.append(key)
    if error_keys:
        return {
            "success": False,
            "error_message": f"frame_structure中存在dof为0的key: {error_keys}",
        }

    frame_structure_values_set = set()
    for value in frame_structure.values():
        for v in value["values"]:
            frame_structure_values_set.add(v)

    output_dataset_path = os.path.join(
        config.get("output_dataset_dir"),
        os.path.basename(data_path).rsplit('.', 1)[0] + ".hdf5"
    )

    with Hdf5Dataset(output_dataset_path, frame_structure) as output_dataset:
        with BagReader(data_path) as bag_reader:
            start_time = bag_reader.get_start_time()
            end_time = bag_reader.get_end_time()
            sample_timestamps = np.arange(start_time, end_time, 1 / config.get("fps"))

            sample_index = 1
            topic_to_msg = {}
            for topic, msg, t in bag_reader.read_messages():
                if t > sample_timestamps[sample_index]:
                    try:
                        frame_data = get_frame_data(
                            frame_structure_values_set,
                            frame_structure,
                            topic_to_msg,
                            data_source
                        )
                        output_dataset.add_frame(frame_data)
                    except (KeyError, ValueError) as e:
                        if t - start_time > 1:
                            return {
                                "success": False,
                                "error_message": f"failed at relative time {t - start_time:2f}s: {str(e)}",
                            }

                    sample_index += 1
                    if sample_index >= len(sample_timestamps):
                        break

                topic_to_msg[topic] = msg

    return {
        "success": True,
    }


def convert_data(config_path: str):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    check_config(config)

    metadatas = load_dataset(config.get("dataset_id"), config.get("data_load"))
    # convert data in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=config.get("convert_num_workers")) as executor:
        futures = {executor.submit(convert, metadata, config): metadata for metadata in metadatas}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            logger.info(f"converted {futures[future]['metadata']['name']}, result: {result}")


if __name__ == "__main__":
    convert_data(Path(__file__).parent / "config.yaml")
