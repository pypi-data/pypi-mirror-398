import hashlib


def 取硬盘特征字():
    """
    调用函数来获取系统硬盘特征字。

    返回:
        int: 系统硬盘特征字的整数表示。如果获取失败，则返回 None。

    使用示例:
        disk_feature = 系统_取硬盘特征字()
        print("系统硬盘特征字:", disk_feature)
    """
    try:
        with open('C:\\Windows\\explorer.exe', 'rb') as f:
            data = f.read(4096)
        hash_value = hashlib.md5(data).hexdigest()
        feature_code = int(hash_value, 16)
        return feature_code
    except Exception:
        return None