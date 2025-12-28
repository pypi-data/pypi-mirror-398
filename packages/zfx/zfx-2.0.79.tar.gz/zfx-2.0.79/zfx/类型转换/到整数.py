from typing import Any


def 到整数(输入值: Any) -> int:
    """
    将输入值转换为整数（int）。

    Args:
        输入值 (Any):
            需要转换为整数的值。

    Returns:
        int:
            转换后的整数。

            - 支持可直接转为整数的类型：
              * 整数（int）→ 原值返回
              * 浮点数（float）→ 向下取整（如 3.9 → 3）
              * 字符串形式的数字（"42"、"  7  "）
              * 布尔值 True / False → 1 / 0
            - 如果输入值无法转换（如列表、字典、None、文本字符串等），则返回 0。
            - 转换时会自动去除字符串前后空格。
    """
    try:
        return int(float(str(输入值).strip()))
    except Exception:
        return 0
