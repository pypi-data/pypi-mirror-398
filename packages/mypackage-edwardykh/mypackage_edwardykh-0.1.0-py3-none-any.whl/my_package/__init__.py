# mypackage/__init__.py
"""mypackage：提供基础数学运算功能"""

__version__ = "0.1.0"  # 包版本号（必加，发布用）

# 导出核心功能，简化用户导入
from .core import add, divide
from .utils.helper import format_result  # 若有工具函数