# Calc SDK

一个简单的加法运算 Python SDK，用于测试 PyPI 发布流程。

## 安装

```bash
pip install calc-test-sdk
```

## 使用方法

### 简单加法

```python
from calc_sdk import add

result = add(1, 2)
print(result)  # 输出: 3
```

### 链式计算

```python
from calc_sdk import Calculator

calc = Calculator()
result = calc.add(1).add(2).add(3).result
print(result)  # 输出: 6

# 重置计算器
calc.reset()
result = calc.add(10).add(20).result
print(result)  # 输出: 30
```

## License

MIT License
