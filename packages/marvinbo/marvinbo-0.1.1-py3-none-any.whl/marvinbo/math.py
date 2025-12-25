def square(number):
    """
    计算输入数字的平方。
    """
    if not isinstance(number, (int, float)):
        raise TypeError("输入必须是数字。")
    return number * number

def cube(number):
    """
    计算输入数字的立方。
    """
    return number ** 3