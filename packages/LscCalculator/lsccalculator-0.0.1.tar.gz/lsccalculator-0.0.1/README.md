# 强大的计算工具（整合decimal）

### 解决de问题
* 使用decimal库，防止0.1+0.2=0.30...4的局面
* 每个方法皆可输入多个数字，拒绝addition(1, addition(2, 3))

### 多功能
* 额外添加StringsCalculator

### 调用方法
```
from LscCalculator import *

"""
nc / NC / NumbersCalculator : 计算数字运算的类
addition : 加法
subtraction : 减法
multiplication : 乘法
division : 除法
power : 乘方
factorial : 阶乘
sqrt : 开根号
"""

print(nc().addition(1, 2, 3, 4)) 
```