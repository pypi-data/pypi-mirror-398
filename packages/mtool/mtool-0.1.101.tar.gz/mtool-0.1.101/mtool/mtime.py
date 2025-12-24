from datetime import datetime

import pytz
from dateutil import parser


def get_current_time():
    """
    获取当前时区的时间戳，精确到秒。

    :return: 带有当前时区的时间戳字符串
    """
    tz = pytz.timezone('Asia/Shanghai')  # 根据你的时区选择
    current_time = datetime.now(tz)
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


def format_time_string(time_str, target_format="%Y-%m-%d %H:%M:%S"):
    """
    自动检测时间字符串的格式，并转换为目标格式。

    参数:
    - time_str (str): 原始时间字符串。
    - target_format (str): 目标时间格式，默认为 "%Y-%m-%d %H:%M:%S"。

    返回:
    - str: 格式化后的时间字符串。
    """
    # 使用dateutil.parser.parse自动解析时间字符串
    dt = parser.parse(time_str)

    # 格式化输出
    formatted_time = dt.strftime(target_format)

    return formatted_time


def convert_to_standard_format(date_str):
    # 如果输入的不是字符串类型，先转换为字符串
    if not isinstance(date_str, str):
        date_str = str(date_str)
    # 定义常见的日期格式
    formats = [
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y.%m.%d %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%d.%m.%Y %H:%M:%S',
        '%Y年%m月%d日 %H:%M:%S'
    ]

    # 尝试使用不同的格式进行解析
    for fmt in formats:
        try:
            # 解析成功后，转换为目标格式 'YYYY-MM-DD HH:MM:SS'
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            # 解析失败，继续尝试下一个格式
            continue
    return False
    #raise ValueError(f"未识别的日期格式: {date_str}")
