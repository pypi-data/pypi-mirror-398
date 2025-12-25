"""
计算器模块 - 提供加法运算功能
"""

from typing import Union

Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """
    计算两个数的和
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        两个数字的和
    
    Examples:
        >>> add(1, 2)
        3
        >>> add(1.5, 2.5)
        4.0
    """
    return a + b


class Calculator:
    """
    计算器类 - 支持链式加法运算
    
    Examples:
        >>> calc = Calculator()
        >>> calc.add(1).add(2).add(3).result
        6
    """
    
    def __init__(self, initial_value: Number = 0):
        """
        初始化计算器
        
        Args:
            initial_value: 初始值，默认为0
        """
        self._value = initial_value
    
    def add(self, value: Number) -> "Calculator":
        """
        加法运算
        
        Args:
            value: 要加的数字
        
        Returns:
            返回自身，支持链式调用
        """
        self._value = self._value + value
        return self
    
    @property
    def result(self) -> Number:
        """获取当前计算结果"""
        return self._value
    
    def reset(self, value: Number = 0) -> "Calculator":
        """
        重置计算器
        
        Args:
            value: 重置后的值，默认为0
        
        Returns:
            返回自身，支持链式调用
        """
        self._value = value
        return self
    
    def __repr__(self) -> str:
        return f"Calculator(value={self._value})"
