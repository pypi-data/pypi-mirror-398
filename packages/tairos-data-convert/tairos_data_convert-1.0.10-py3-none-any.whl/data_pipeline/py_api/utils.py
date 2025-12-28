from datetime import datetime
import pytz

TZ = pytz.timezone('Asia/Shanghai')


def str_to_timestamp(date_str: str) -> int:
    # 解析字符串为datetime对象
    dt = TZ.localize(datetime.strptime(date_str, "%Y%m%d-%H%M%S"))
    # 转换为时间戳
    return int(dt.timestamp())
