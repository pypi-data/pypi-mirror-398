from typing import Any, Dict


def 到字典(输入值: Any) -> Dict[str, Any]:
    """
    将输入值转换为字典（dict）。

    Args:
        输入值 (Any):
            需要转换为字典的值。

    Returns:
        dict:
            转换后的字典。

            - 如果输入值本身是字典，则直接返回。
            - 如果输入值是可转换为字典的结构（如键值对序列或可迭代对象），则自动转换。
              例如：
                  [("a", 1), ("b", 2)] → {"a": 1, "b": 2}
                  zip(["x", "y"], [10, 20]) → {"x": 10, "y": 20}
            - 如果输入值不是可转换结构（如整数、字符串、None 等），
              则包装为 {"value": 输入值}。
            - 如果发生异常，则返回空字典 {}。
    """
    try:
        # 如果本身就是字典，直接返回副本
        if isinstance(输入值, dict):
            return dict(输入值)

        # 尝试标准方式转换
        return dict(输入值)

    except (TypeError, ValueError):
        # 无法直接转换时包装为单值字典
        return {"value": 输入值}

    except Exception:
        # 不抛出异常，返回安全空字典
        return {}