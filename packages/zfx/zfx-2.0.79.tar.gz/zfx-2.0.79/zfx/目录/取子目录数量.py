import os


def 取子目录数量(目录路径):
    """
    获取指定目录中的子目录数量(包含隐藏的文件也会统计到)。

    参数：
        - 目录路径 (str)：要统计子目录数量的目录路径。

    返回值：
        - 子目录数量 (int)：该目录中的子目录数量。如果路径无效或出现错误，返回 -1。

    使用示例（可以复制并直接修改）：
        子目录数量 = zfx_dir.取子目录数量("E:/my_project")

        # 打印子目录数量
        print("子目录数量:", 子目录数量)
    """
    try:
        # 检查目录路径是否存在
        if not os.path.exists(目录路径):
            print(f"目录 {目录路径} 不存在")
            return -1

        # 列出目录下的所有子目录并统计
        子目录列表 = [name for name in os.listdir(目录路径) if os.path.isdir(os.path.join(目录路径, name))]
        return len(子目录列表)
    except Exception:
        return -1