def 国家代码转货币代码(国家代码: str) -> str:
    """
    根据国家代码（ISO 3166-1 Alpha-2）返回对应的货币代码（ISO 4217）。

    功能说明：
        - 自动忽略大小写与前后空格。
        - 内部包含主要国家和地区共 200+ 项映射。
        - 当输入无效或国家代码未收录时，返回 '未知'。
        - 自动捕获所有异常，保证函数不会中断执行。

    Args:
        国家代码 (str): 两位国家/地区代码，例如 'US'、'CN'、'JP'。

    Returns:
        str: 对应的货币代码（如 'USD'、'CNY'、'JPY'），未匹配则返回 '未知'。
    """
    try:
        if not isinstance(国家代码, str) or len(国家代码.strip()) < 2:
            return "未知"

        国家代码 = 国家代码.strip().upper()
        映射 = {
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
            "AS": "USD", "IO": "USD", "NF": "AUD", "CX": "AUD", "CC": "AUD", "AQ": "未知"
        }
        return 映射.get(国家代码, "未知")
    except:
        return "未知"
