# mtools

一个实用的Python工具集合，提供常用功能的封装，方便在Python项目中使用。

## 功能特性

- **时间处理**：获取当前时间、格式化时间字符串、转换为标准格式
- **路径处理**：跨平台路径处理，兼容打包环境
- **数据转换**：数字转换工具



## 安装方法

### 使用pip从Git仓库安装

```bash
pip install git+https://gitcode.com/pymod/mtools.git
```

### 使用pip从Git仓库更新

```bash
pip install --upgrade git+https://gitcode.com/pymod/mtools.git
```

### 使用uv从Git仓库安装

```bash
uv add git+https://gitcode.com/pymod/mtools.git
```

### 使用uv从Git仓库更新

```
uv sync --upgrade-package mtools
```



## 使用示例

### 时间处理

```python
from mtools import get_current_time, format_time_string, convert_to_standard_format

# 获取当前时间
current_time = get_current_time()
print(current_time)  # 输出类似: 2023-05-15 14:30:45

# 格式化时间字符串
formatted = format_time_string("2023-05-15T14:30:45", "%Y年%m月%d日 %H:%M:%S")
print(formatted)  # 输出: 2023年05月15日 14:30:45

# 转换为标准格式
standard = convert_to_standard_format("15/05/2023 14:30:45")
print(standard)  # 输出: 2023-05-15 14:30:45
```

### 路径处理

```python
from mtools import get_program_dir, get_universal_program_dir, resource_path, get_data_directory

# 获取程序目录
program_dir = get_program_dir()

# 获取通用程序目录（兼容打包环境）
iversal_dir = get_universal_program_dir()

# 获取资源文件路径
resource = resource_path("images/logo.png")

# 获取数据目录
input_dir = get_data_directory("input")
output_dir = get_data_directory("output")
```

### 数据转换

```python
from mtools import to_rounded_decimal

# 转换为四舍五入的Decimal
decimal_value = to_rounded_decimal("10.125")
print(decimal_value)  # 输出: 10.13
```

## 许可证

MIT License