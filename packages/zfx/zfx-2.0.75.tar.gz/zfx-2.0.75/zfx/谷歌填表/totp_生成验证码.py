import pyotp
import time


def totp_生成验证码(密钥):
    """
    生成当前时间的 TOTP 验证码，并估算剩余有效时间。

    参数：
        - 密钥 (str)：用于生成 TOTP 验证码的密钥，通常是基于共享密钥的字符串。

    返回值：
        - tuple：包含生成的验证码和剩余有效时间的元组 (验证码, 剩余有效时间)。
        - 如果生成失败，返回 (None, None)。

    使用示例：
        验证码, 剩余时间 = zfx_totp.totp_生成验证码('JBSWY3DPEHPK3PXP')
        if 验证码:
            print(f"生成的验证码是 {验证码}, 剩余有效时间为 {剩余时间} 秒")
        else:
            print("生成验证码失败")

    注意：
        - 密钥将自动去除空格并转为大写，确保符合规范。
        - 剩余有效时间表示当前验证码的有效时间，单位为秒。
    """
    try:
        # 移除空格并将密钥转为大写
        密钥 = 密钥.replace(' ', '').upper()

        # 创建一个 TOTP 对象
        totp = pyotp.TOTP(密钥)

        # 生成当前的 TOTP 验证码
        验证码 = totp.now()

        # 计算剩余有效时间
        剩余有效时间 = totp.interval - (int(time.time()) % totp.interval)

        return 验证码, 剩余有效时间
    except Exception:
        return None, None