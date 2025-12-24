#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试脚本来验证mtools包的安装和导入
"""

import mtool

# 测试版本信息
print(f"版本信息: {mtool.__version__}")
print(f"作者信息: {mtool.__author__}")
print(f"邮箱信息: {mtool.__email__}")
print()

# 测试核心功能
print("=== 测试核心功能 ===")

# 测试时间处理函数
print("当前时间:", mtool.get_current_time())
print("格式化时间:", mtool.format_time_string("2024-01-01 12:00:00"))
print()

# 测试路径处理函数
print("程序目录:", mtool.get_app_dir())
print()

# 测试数据转换函数
print("四舍五入小数:", mtool.to_rounded_decimal(123.456789))

print("\n所有测试通过！mtools包安装成功并可以正常使用。")

