"""mtool - 一个实用的Python工具集合

这个包提供了以下实用工具函数：
- 数据转换工具
- 时间处理工具
- 路径处理工具
"""

# 版本信息


# 导出公共API
from .convert import to_rounded_decimal
from .mtime import get_current_time, format_time_string, convert_to_standard_format
from .path import get_app_dir, get_resource_path, get_data_directory

# 定义公开接口
__all__ = [
    # 转换工具
    "to_rounded_decimal",
    # 时间处理工具
    "get_current_time",
    "format_time_string",
    "convert_to_standard_format",
    # 路径处理工具
    "get_app_dir",
    "get_resource_path",
    "get_data_directory",
]
