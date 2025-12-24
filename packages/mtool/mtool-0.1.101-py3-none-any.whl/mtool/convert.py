import decimal
from decimal import Decimal

def to_rounded_decimal(value):
    """
    将数字或字符串类型的数字转换为 Decimal 类型，结果四舍五入保留两位小数。

    :param value: 输入值，可以是数字或字符串类型的数字
    :return: 四舍五入保留两位小数的 Decimal 类型结果，如果无法转换则返回 None
    """
    try:
        # 尝试将输入值转换为 Decimal 对象
        decimal_value = Decimal(str(value))

        # 返回四舍五入保留两位小数的 Decimal 对象
        return decimal_value.quantize(Decimal('0.00'))
    except (ValueError, TypeError, decimal.InvalidOperation):
        # 如果输入值无法转换为 Decimal，返回 None 或根据需求抛出异常
        return None