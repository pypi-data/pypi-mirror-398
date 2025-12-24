# mypackage/core.py
"""核心功能模块：提供加法、除法运算"""

def add(a: int | float, b: int | float) -> int | float:
    """两数相加"""
    return a + b

def divide(a: int | float, b: int | float) -> int | float:
    """两数相除，除数不能为0"""
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b