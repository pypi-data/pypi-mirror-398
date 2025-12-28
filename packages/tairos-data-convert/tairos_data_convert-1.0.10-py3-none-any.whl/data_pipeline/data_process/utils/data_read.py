"""数据读取模块，支持rosbag和mcap格式"""
import os
from typing import Iterator, Tuple, Optional, Any
from pathlib import Path

import rosbag
from mcap_ros1.decoder import DecoderFactory as ROS1DecoderFactory
from mcap.reader import make_reader


class BagReader:
    """数据读取器，支持rosbag和mcap格式"""

    def __init__(self, bag_path: str):
        """
        初始化数据读取器

        Args:
            bag_path: bag或mcap文件路径
        """
        if not os.path.exists(bag_path):
            raise FileNotFoundError(f"文件不存在: {bag_path}")

        self.bag_path = bag_path
        self.is_rosbag = bag_path.endswith(".bag")
        self.is_mcap = bag_path.endswith(".mcap")

        if not (self.is_rosbag or self.is_mcap):
            raise ValueError(f"不支持的文件格式: {bag_path}")

        if self.is_rosbag:
            self.reader = rosbag.Bag(bag_path, 'r')
        else:
            self.file = open(bag_path, "rb")
            self.reader = make_reader(self.file, decoder_factories=[ROS1DecoderFactory()])
            self.summary = self.reader.get_summary()

    def get_start_time(self) -> float:
        """获取数据开始时间（秒）"""
        if self.is_rosbag:
            return self.reader.get_start_time()
        else:
            return self.summary.statistics.message_start_time / 1e9

    def get_end_time(self) -> float:
        """获取数据结束时间（秒）"""
        if self.is_rosbag:
            return self.reader.get_end_time()
        else:
            return self.summary.statistics.message_end_time / 1e9

    def read_messages(self, topics: Optional[list] = None) -> Iterator[Tuple[str, Any, float]]:
        """
        读取消息

        Args:
            topics: 要读取的topic列表，如果为None则读取所有topic

        Yields:
            (topic, message, timestamp): topic名称、消息对象、时间戳（秒）
        """
        if self.is_rosbag:
            for topic, msg, t in self.reader.read_messages(topics=topics):
                yield topic, msg, t.to_sec()
        else:
            for _, channel, message, decoded_msg in self.reader.iter_decoded_messages(topics=topics):
                yield channel.topic, decoded_msg, message.log_time / 1e9

    def get_file_type(self) -> str:
        """获取文件类型"""
        if self.is_rosbag:
            return "bag"
        elif self.is_mcap:
            return "mcap"
        else:
            return Path(self.bag_path).suffix[1:]  # 去掉点号

    def get_topics(self) -> list:
        if self.is_rosbag:
            _, topic_info = self.reader.get_type_and_topic_info()
            return list(topic_info.keys())
        else:
            topics = []
            for channel_info in self.summary.channels.values():
                topics.append(channel_info.topic)
            return topics

    def close(self):
        if self.is_rosbag:
            self.reader.close()
        else:
            self.file.close()

    def __enter__(self):
        # open resources
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # close resources
        self.close()
