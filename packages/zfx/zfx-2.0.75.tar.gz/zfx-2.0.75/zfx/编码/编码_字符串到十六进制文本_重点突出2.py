def 编码_字符串到十六进制文本_重点突出2(完整字符串, 重点字符串1, 重点字符串2):
    """
    将字符串转换为16进制文本，并将属于重点字符的十六进制字节以红色和绿色显示。

    参数:
        - 完整字符串 (str): 要转换的字符串。
        - 重点字符串1 (str): 需要重点突出的第一个字符串。
        - 重点字符串2 (str): 需要重点突出的第二个字符串。

    返回:
        - str: 转换后的16进制文本，每个字节用两个字符表示，中间用空格分隔。如果输入无效或出现异常，返回 None。

    示例:
        完整字符串 = "Hello, World!"
        重点字符串1 = "Hello"
        重点字符串2 = "World"
        编码_字符串到十六进制文本_重点突出2(完整字符串, 重点字符串1, 重点字符串2)
        # 输出: 48 65 6c 6c 6f 2c 20 57 6f 72 6c 64 21
        # 并且 "Hello" 的十六进制文本以红色输出，"World" 的十六进制文本以绿色输出
    """
    try:
        byte_text = 完整字符串.encode()
        highlight_bytes1 = 重点字符串1.encode()
        highlight_bytes2 = 重点字符串2.encode()
        hex_text_list = []
        i = 0

        while i < len(byte_text):
            if byte_text[i:i+len(highlight_bytes1)] == highlight_bytes1:
                # 如果匹配到重点字符串1
                hex_str = ' '.join(f"{b:02x}" for b in byte_text[i:i+len(highlight_bytes1)])
                hex_text_list.append(f"\033[91m{hex_str}\033[0m")
                i += len(highlight_bytes1)
            elif byte_text[i:i+len(highlight_bytes2)] == highlight_bytes2:
                # 如果匹配到重点字符串2
                hex_str = ' '.join(f"{b:02x}" for b in byte_text[i:i+len(highlight_bytes2)])
                hex_text_list.append(f"\033[92m{hex_str}\033[0m")
                i += len(highlight_bytes2)
            else:
                # 处理单字节和多字节字符
                if byte_text[i] < 128:
                    # 单字节字符
                    char_bytes = [byte_text[i]]
                    i += 1
                else:
                    # 多字节字符，根据UTF-8编码进行处理
                    if byte_text[i] & 0b11110000 == 0b11110000:
                        # 4字节字符
                        char_bytes = byte_text[i:i + 4]
                        i += 4
                    elif byte_text[i] & 0b11100000 == 0b11100000:
                        # 3字节字符
                        char_bytes = byte_text[i:i + 3]
                        i += 3
                    elif byte_text[i] & 0b11000000 == 0b11000000:
                        # 2字节字符
                        char_bytes = byte_text[i:i + 2]
                        i += 2

                hex_str = ' '.join(f"{b:02x}" for b in char_bytes)
                hex_text_list.append(hex_str)

        hex_text = ' '.join(hex_text_list)
        return hex_text
    except Exception:
        return None