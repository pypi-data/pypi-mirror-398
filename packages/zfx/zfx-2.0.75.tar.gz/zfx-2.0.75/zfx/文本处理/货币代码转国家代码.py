def 货币代码转国家代码(货币代码: str) -> list[str]:
    """
    根据货币代码（ISO 4217）返回使用该货币的国家/地区代码列表（ISO 3166-1 Alpha-2）。

    功能说明：
        - 忽略大小写与前后空格。
        - 结果包含主权国家与常见属地/地区（例如 USD 覆盖 US、PR、GU、VI、MP、UM 等）。
        - 未匹配时返回空列表 []。
        - 内部异常安全：任何异常都会安全返回 [] 并可选打印告警。

    Args:
        货币代码: 三位货币代码，如 'USD'、'CNY'、'EUR'、'XOF'。

    Returns:
        list[str]: 使用该货币的两位国家/地区码列表（已按字母序排序）。
    """
    try:
        if not isinstance(货币代码, str) or len(货币代码.strip()) < 3:
            return []

        货币代码 =货币代码.strip().upper()

        # —— 数据源：国家 → 货币（与“国家代码转货币代码”一致）——
        国家到货币 = {
            "US": "USD", "CN": "CNY", "JP": "JPY", "KR": "KRW", "HK": "HKD", "TW": "TWD",
            "GB": "GBP", "EU": "EUR", "DE": "EUR", "FR": "EUR", "IT": "EUR", "ES": "EUR",
            "CA": "CAD", "AU": "AUD", "NZ": "NZD", "SG": "SGD", "IN": "INR", "BR": "BRL",
            "MX": "MXN", "AR": "ARS", "TR": "TRY", "ZA": "ZAR", "CH": "CHF", "SE": "SEK",
            "NO": "NOK", "DK": "DKK", "PL": "PLN", "CZ": "CZK", "HU": "HUF", "RO": "RON",
            "BG": "BGN", "RU": "RUB", "AE": "AED", "SA": "SAR", "QA": "QAR", "OM": "OMR",
            "KW": "KWD", "BH": "BHD", "EG": "EGP", "TH": "THB", "ID": "IDR", "MY": "MYR",
            "PH": "PHP", "VN": "VND", "BD": "BDT", "PK": "PKR", "NP": "NPR", "LK": "LKR",
            "BT": "BTN", "MM": "MMK", "KH": "KHR", "LA": "LAK", "IR": "IRR", "IQ": "IQD",
            "IL": "ILS", "JO": "JOD", "LB": "LBP", "SY": "SYP", "YE": "YER", "AF": "AFN",
            "AZ": "AZN", "AM": "AMD", "GE": "GEL", "KZ": "KZT", "KG": "KGS", "UZ": "UZS",
            "TJ": "TJS", "TM": "TMT", "MN": "MNT", "BN": "BND", "TL": "USD", "NG": "NGN",
            "GH": "GHS", "KE": "KES", "TZ": "TZS", "UG": "UGX", "ZM": "ZMW", "ZW": "ZWL",
            "DZ": "DZD", "MA": "MAD", "TN": "TND", "LY": "LYD", "MR": "MRU", "SN": "XOF",
            "ML": "XOF", "BF": "XOF", "NE": "XOF", "TG": "XOF", "BJ": "XOF", "CI": "XOF",
            "CM": "XAF", "TD": "XAF", "CF": "XAF", "GA": "XAF", "CG": "XAF", "GQ": "XAF",
            "AO": "AOA", "MZ": "MZN", "NA": "NAD", "BW": "BWP", "SZ": "SZL", "LS": "LSL",
            "MG": "MGA", "MU": "MUR", "KM": "KMF", "SC": "SCR", "CV": "CVE", "ST": "STN",
            "IS": "ISK", "FI": "EUR", "EE": "EUR", "LV": "EUR", "LT": "EUR", "SK": "EUR",
            "SI": "EUR", "HR": "EUR", "ME": "EUR", "RS": "RSD", "BA": "BAM", "AL": "ALL",
            "MK": "MKD", "XK": "EUR", "IE": "EUR", "NL": "EUR", "BE": "EUR", "LU": "EUR",
            "AT": "EUR", "PT": "EUR", "GR": "EUR", "CY": "EUR", "MT": "EUR", "LI": "CHF",
            "FO": "DKK", "CH": "CHF", "HK": "HKD", "MO": "MOP", "TH": "THB", "SG": "SGD",
            "PH": "PHP", "MY": "MYR", "ID": "IDR", "VN": "VND", "CN": "CNY", "JP": "JPY",
            "KR": "KRW", "TW": "TWD", "AU": "AUD", "NZ": "NZD", "FJ": "FJD", "PG": "PGK",
            "SB": "SBD", "VU": "VUV", "TO": "TOP", "WS": "WST", "TV": "AUD", "NR": "AUD",
            "KI": "AUD", "NC": "XPF", "PF": "XPF", "WF": "XPF", "GU": "USD", "MP": "USD",
            "AS": "USD", "IO": "USD", "NF": "AUD", "CX": "AUD", "CC": "AUD", "AQ": "未知",
            # —— 美洲与加勒比补充（在你上一版单函数中未显式列出的一些常见地区，可按需增减）——
            "PR": "USD", "VI": "USD", "VG": "USD", "KY": "KYD", "TT": "TTD", "BB": "BBD",
            "BS": "BSD", "BZ": "BZD", "GD": "XCD", "LC": "XCD", "DM": "XCD", "KN": "XCD",
            "AG": "XCD", "AI": "XCD", "CW": "ANG", "SX": "ANG", "AW": "AWG", "BQ": "USD",
            "JM": "JMD", "DO": "DOP", "HT": "HTG", "PA": "PAB", "CR": "CRC", "GT": "GTQ",
            "HN": "HNL", "NI": "NIO", "SV": "USD", "EC": "USD", "UY": "UYU", "PY": "PYG",
            "BO": "BOB", "PE": "PEN", "CL": "CLP", "CO": "COP", "VE": "VES", "AR": "ARS",
            "BR": "BRL", "GY": "GYD", "SR": "SRD", "FK": "FKP",
            # —— 北欧/极地/法属海外等 ——
            "GL": "DKK", "SJ": "NOK", "RE": "EUR", "YT": "EUR", "TF": "EUR", "GF": "EUR",
            "MQ": "EUR", "GP": "EUR",
        }

        # —— 单函数内构建“货币 → 国家列表”的倒排表，并做缓存（函数属性）——
        if not hasattr(货币代码转国家代码, "_缓存_货币到国家"):
            倒排 = {}
            for 国家, 币种 in 国家到货币.items():
                if 币种 == "未知":
                    continue
                倒排.setdefault(币种, []).append(国家)
            for 币种 in 倒排:
                倒排[币种].sort()
            货币代码转国家代码._缓存_货币到国家 = 倒排  # type: ignore[attr-defined]

        return 货币代码转国家代码._缓存_货币到国家.get(货币代码, [])  # type: ignore[attr-defined]

    except Exception as e:
        return []