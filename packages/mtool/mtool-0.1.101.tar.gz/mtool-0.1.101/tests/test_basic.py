#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic tests for mtools package.
"""

import pytest
import os
import sys
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入mtools包
import mtool


class TestBasic:
    """测试mtools包的基本功能"""
    
    def test_version(self):
        """测试版本信息"""
        assert mtool.__version__ == "0.1.0"
    
    def test_author(self):
        """测试作者信息"""
        assert mtool.__author__ == "Your Name"
    
    def test_email(self):
        """测试邮箱信息"""
        assert mtool.__email__ == "your.email@example.com"


class TestTimeFunctions:
    """测试时间处理函数"""
    
    def test_get_current_time(self):
        """测试获取当前时间"""
        current_time = mtool.get_current_time()
        assert isinstance(current_time, str)
        # 检查格式是否正确 (YYYY-MM-DD HH:MM:SS)
        assert len(current_time) == 19
        assert current_time[4] == "-"
        assert current_time[7] == "-"
        assert current_time[10] == " "
        assert current_time[13] == ":"
        assert current_time[16] == ":"
    
    def test_format_time_string(self):
        """测试时间格式化"""
        # 使用一个已知格式的时间字符串进行测试
        test_time = "2024-01-01 12:00:00"
        time_str = mtool.format_time_string(test_time)
        assert isinstance(time_str, str)
        # 检查格式是否正确 (YYYY-MM-DD HH:MM:SS)
        assert len(time_str) == 19
        assert time_str[4] == "-"
        assert time_str[7] == "-"
        assert time_str[10] == " "
        assert time_str[13] == ":"
        assert time_str[16] == ":"


class TestPathFunctions:
    """测试路径处理函数"""
    
    def test_get_program_dir(self):
        """测试获取程序目录"""
        program_dir = mtool.get_app_dir()
        assert isinstance(program_dir, str)
        # 在pytest环境中，这个路径可能指向pytest可执行文件，所以我们只检查路径是否存在
        assert os.path.exists(program_dir) or os.path.isfile(program_dir)
    
    def test_resource_path(self):
        """测试资源路径函数"""
        # 测试一个不存在的资源文件路径
        resource = mtool.get_resource_path("non_existent_file.txt")
        # get_resource_path返回Path对象，所以我们检查它的类型
        assert hasattr(resource, 'exists')  # 检查是否是Path对象


class TestConvertFunctions:
    """测试数据转换函数"""
    
    def test_to_rounded_decimal(self):
        """测试十进制数四舍五入"""
        # 测试正数
        result = mtool.to_rounded_decimal(123.456789)
        assert result == Decimal('123.46')
        
        # 测试负数
        result = mtool.to_rounded_decimal(-123.456789)
        assert result == Decimal('-123.46')
        
        # 测试零
        result = mtool.to_rounded_decimal(0)
        assert result == Decimal('0.00')


if __name__ == "__main__":
    pytest.main([__file__])