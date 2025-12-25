from typing import SupportsFloat, List, Tuple, Optional


def 因数分解_可限定(
        数值: SupportsFloat,
        最小值: Optional[int] = None,
        最大值: Optional[int] = None
) -> List[Tuple[int, int]]:
    """
    寻找所有两数相乘等于目标值的因数对，可选择性限制因数范围。

    功能说明：
        - 将输入转换为整数后进行因数分解。
        - 若未提供最小值或最大值，则不限制因数范围：
              返回所有 (a, b) 且 a * b == n 的组合。
        - 若开发者传入最小/最大值，则只返回满足：
              最小值 <= a <= 最大值
              最小值 <= b <= 最大值
          的因数对。
        - 输入无效、无法转换为整数、零或负数 → 返回空列表。
        - 函数绝不抛异常。

    Args:
        数值 (SupportsFloat): 需要进行因数分解的目标值。
        最小值 (int | None): 限定因数的下限，None 表示不限制。
        最大值 (int | None): 限定因数的上限，None 表示不限制。

    Returns:
        list[tuple[int, int]]:
            - 成功：所有合格的因数组合 (a, b)。
            - 失败：返回空列表。

    Notes:
        - 无限制模式下，因数搜索范围为 1 到 n。
        - 返回列表按 a 从小到大排序。
    """
    try:
        n = int(float(数值))
        if n <= 0:
            return []
    except Exception:
        return []

    结果: List[Tuple[int, int]] = []

    # 搜索范围：如果未指定，就从 1 到 n
    a起点 = 最小值 if 最小值 is not None else 1
    a终点 = 最大值 if 最大值 is not None else n

    # 确保范围有效
    if a起点 <= 0 or a终点 <= 0 or a起点 > a终点:
        return []

    for a in range(a起点, a终点 + 1):
        if n % a == 0:
            b = n // a

            # 若有限定范围，则需要满足 b 也在范围内
            if 最小值 is not None and b < 最小值:
                continue
            if 最大值 is not None and b > 最大值:
                continue

            结果.append((a, b))

    return 结果

