"""
语言工具模块

提供语言代码到语言名称的映射和相关工具函数。

支持的语言代码格式：
1. ISO 639-1 (2字母代码): zh, en, ja, ko, etc.
2. ISO 639-2/3 (3字母代码): chi, eng, jpn, kor, etc.
3. BCP-47 扩展标签 (语言-脚本/地区): zh-hans, zh-hant, en-us, fr-ca, fil-ph, etc.
4. 常用别名: chs, cht, gb, big5 (为兼容性保留)

语言名称使用各语言的原生名称（如：中文、English、日本語）。
"""

from typing import Dict

# 语言代码到语言名称的映射（使用语言原生名称）
# 包含多种格式的语言代码：
#   - ISO 639-1 (2字母代码): zh, en, ja, ko, etc.
#   - ISO 639-2/3 (3字母代码): chi, eng, jpn, kor, fil, etc.
#   - BCP-47 扩展标签 (语言-脚本/区域): zh-hans, zh-hant, en-us, fr-ca, fil-ph, etc.
#   - 常用别名 (为兼容性保留): chs, cht, gb, big5
# 注意：本映射表支持 ISO 639-2/3 和 BCP-47 混合格式，
#       convert_to_iso639_2 函数会在必要时进行标准化转换
LANGUAGE_NAMES: Dict[str, str] = {
    # === 中文及方言 ===
    "zh": "中文",
    "chi": "中文",
    "zho": "中文",
    "zh-hans": "简体中文",
    "zh-hant": "繁體中文",
    "zh-cn": "中文（中国）",
    "zh-hk": "中文（香港）",
    "zh-tw": "中文（台灣）",
    "zh-sg": "中文（新加坡）",
    "zh-mo": "中文（澳門）",
    # 中文别名
    "chs": "简体中文",
    "cht": "繁體中文",
    "gb": "简体中文",
    "big5": "繁體中文",
    # 中文方言 (ISO 639-3)
    "yue": "粵語",          # 粤语
    "wuu": "吳語",          # 吴语
    "nan": "閩南語",        # 闽南语
    "hsn": "湘語",          # 湘语
    "hak": "客家話",        # 客家话
    "gan": "贛語",          # 赣语

    # === 英语 ===
    "en": "English",
    "eng": "English",
    "en-us": "English (United States)",
    "en-gb": "English (United Kingdom)",
    "en-au": "English (Australia)",
    "en-ca": "English (Canada)",
    "en-nz": "English (New Zealand)",
    "en-ie": "English (Ireland)",
    "en-za": "English (South Africa)",
    "en-in": "English (India)",

    # === 日语 ===
    "ja": "日本語",
    "jpn": "日本語",
    "ja-jp": "日本語（日本）",

    # === 韩语 ===
    "ko": "한국어",
    "kor": "한국어",
    "ko-kr": "한국어（대한민국）",
    "ko-kp": "조선어（조선）",

    # === 欧洲语言 ===
    # 法语
    "fr": "Français",
    "fre": "Français",
    "fra": "Français",
    "fr-fr": "Français (France)",
    "fr-ca": "Français (Canada)",
    "fr-be": "Français (Belgique)",
    "fr-ch": "Français (Suisse)",

    # 德语
    "de": "Deutsch",
    "ger": "Deutsch",
    "deu": "Deutsch",
    "de-de": "Deutsch (Deutschland)",
    "de-at": "Deutsch (Österreich)",
    "de-ch": "Deutsch (Schweiz)",

    # 西班牙语
    "es": "Español",
    "spa": "Español",
    "es-es": "Español (España)",
    "es-mx": "Español (México)",
    "es-ar": "Español (Argentina)",
    "es-co": "Español (Colombia)",
    "es-419": "Español (Latinoamérica)",  # 拉丁美洲西班牙语
    "es-cl": "Español (Chile)",
    "es-pe": "Español (Perú)",
    "es-ve": "Español (Venezuela)",
    "es-us": "Español (Estados Unidos)",

    # 意大利语
    "it": "Italiano",
    "ita": "Italiano",
    "it-it": "Italiano (Italia)",
    "it-ch": "Italiano (Svizzera)",

    # 葡萄牙语
    "pt": "Português",
    "por": "Português",
    "pt-pt": "Português (Portugal)",
    "pt-br": "Português (Brasil)",

    # 俄语
    "ru": "Русский",
    "rus": "Русский",
    "ru-ru": "Русский (Россия)",
    "ru-ua": "Русский (Украина)",

    # 波兰语
    "pl": "Polski",
    "pol": "Polski",

    # 荷兰语
    "nl": "Nederlands",
    "dut": "Nederlands",
    "nld": "Nederlands",
    "nl-nl": "Nederlands (Nederland)",
    "nl-be": "Nederlands (België)",

    # 瑞典语
    "sv": "Svenska",
    "swe": "Svenska",

    # 挪威语
    "no": "Norsk",
    "nor": "Norsk",
    "nb": "Norsk bokmål",
    "nob": "Norsk bokmål",
    "nn": "Norsk nynorsk",
    "nno": "Norsk nynorsk",

    # 丹麦语
    "da": "Dansk",
    "dan": "Dansk",

    # 芬兰语
    "fi": "Suomi",
    "fin": "Suomi",

    # 冰岛语
    "is": "Íslenska",
    "ice": "Íslenska",
    "isl": "Íslenska",

    # 希腊语
    "el": "Ελληνικά",
    "gre": "Ελληνικά",
    "ell": "Ελληνικά",

    # 捷克语
    "cs": "Čeština",
    "cze": "Čeština",
    "ces": "Čeština",

    # 斯洛伐克语
    "sk": "Slovenčina",
    "slo": "Slovenčina",
    "slk": "Slovenčina",

    # 匈牙利语
    "hu": "Magyar",
    "hun": "Magyar",

    # 罗马尼亚语
    "ro": "Română",
    "rum": "Română",
    "ron": "Română",

    # 保加利亚语
    "bg": "Български",
    "bul": "Български",

    # 塞尔维亚语
    "sr": "Српски",
    "srp": "Српски",

    # 克罗地亚语
    "hr": "Hrvatski",
    "hrv": "Hrvatski",

    # 波斯尼亚语
    "bs": "Bosanski",
    "bos": "Bosanski",

    # 斯洛文尼亚语
    "sl": "Slovenščina",
    "slv": "Slovenščina",

    # 乌克兰语
    "uk": "Українська",
    "ukr": "Українська",

    # 白俄罗斯语
    "be": "Беларуская",
    "bel": "Беларуская",

    # 立陶宛语
    "lt": "Lietuvių",
    "lit": "Lietuvių",

    # 拉脱维亚语
    "lv": "Latviešu",
    "lav": "Latviešu",

    # 爱沙尼亚语
    "et": "Eesti",
    "est": "Eesti",

    # 爱尔兰语
    "ga": "Gaeilge",
    "gle": "Gaeilge",

    # 威尔士语
    "cy": "Cymraeg",
    "wel": "Cymraeg",
    "cym": "Cymraeg",

    # 苏格兰盖尔语
    "gd": "Gàidhlig",
    "gla": "Gàidhlig",

    # 巴斯克语
    "eu": "Euskara",
    "baq": "Euskara",
    "eus": "Euskara",

    # 加泰罗尼亚语
    "ca": "Català",
    "cat": "Català",

    # 加利西亚语
    "gl": "Galego",
    "glg": "Galego",

    # 马耳他语
    "mt": "Malti",
    "mlt": "Malti",

    # 阿尔巴尼亚语
    "sq": "Shqip",
    "alb": "Shqip",
    "sqi": "Shqip",

    # 马其顿语
    "mk": "Македонски",
    "mac": "Македонски",
    "mkd": "Македонски",

    # === 亚洲语言 ===
    # 阿拉伯语
    "ar": "العربية",
    "ara": "العربية",
    "ar-sa": "العربية (السعودية)",
    "ar-eg": "العربية (مصر)",
    "ar-ae": "العربية (الإمارات)",

    # 希伯来语
    "he": "עברית",
    "heb": "עברית",

    # 波斯语
    "fa": "فارسی",
    "per": "فارسی",
    "fas": "فارسی",

    # 土耳其语
    "tr": "Türkçe",
    "tur": "Türkçe",
    "tr-tr": "Türkçe (Türkiye)",

    # 阿塞拜疆语
    "az": "Azərbaycan",
    "aze": "Azərbaycan",

    # 库尔德语
    "ku": "Kurdî",
    "kur": "Kurdî",

    # 格鲁吉亚语
    "ka": "ქართული",
    "geo": "ქართული",
    "kat": "ქართული",

    # 亚美尼亚语
    "hy": "Հայերեն",
    "arm": "Հայերեն",
    "hye": "Հայերեն",

    # 印地语
    "hi": "हिन्दी",
    "hin": "हिन्दी",
    "hi-in": "हिन्दी (भारत)",

    # 尼泊尔语
    "ne": "नेपाली",
    "nep": "नेपाली",

    # 乌尔都语
    "ur": "اردو",
    "urd": "اردو",

    # 普什图语
    "ps": "پښتو",
    "pus": "پښتو",

    # 孟加拉语
    "bn": "বাংলা",
    "ben": "বাংলা",

    # 僧伽罗语
    "si": "සිංහල",
    "sin": "සිංහල",

    # 泰米尔语
    "ta": "தமிழ்",
    "tam": "தமிழ்",

    # 泰卢固语
    "te": "తెలుగు",
    "tel": "తెలుగు",

    # 马拉雅拉姆语
    "ml": "മലയാളം",
    "mal": "മലയാളം",

    # 卡纳达语
    "kn": "ಕನ್ನಡ",
    "kan": "ಕನ್ನಡ",

    # 旁遮普语
    "pa": "ਪੰਜਾਬੀ",
    "pan": "ਪੰਜਾਬੀ",

    # 马拉地语
    "mr": "मराठी",
    "mar": "मराठी",

    # 古吉拉特语
    "gu": "ગુજરાતી",
    "guj": "ગુજરાતી",

    # 泰语
    "th": "ไทย",
    "tha": "ไทย",
    "th-th": "ไทย (ประเทศไทย)",

    # 老挝语
    "lo": "ລາວ",
    "lao": "ລາວ",

    # 缅甸语
    "my": "မြန်မာ",
    "bur": "မြန်မာ",
    "mya": "မြန်မာ",

    # 高棉语
    "km": "ខ្មែរ",
    "khm": "ខ្មែរ",

    # 越南语
    "vi": "Tiếng Việt",
    "vie": "Tiếng Việt",
    "vi-vn": "Tiếng Việt (Việt Nam)",

    # 印度尼西亚语
    "id": "Bahasa Indonesia",
    "ind": "Bahasa Indonesia",
    "id-id": "Bahasa Indonesia (Indonesia)",

    # 马来语
    "ms": "Bahasa Melayu",
    "may": "Bahasa Melayu",
    "msa": "Bahasa Melayu",
    "ms-my": "Bahasa Melayu (Malaysia)",
    "ms-sg": "Bahasa Melayu (Singapura)",

    # 菲律宾语
    "fil": "Filipino",
    "fil-ph": "Filipino (Pilipinas)",  # 菲律宾语（菲律宾）
    "tl": "Tagalog",
    "tgl": "Tagalog",

    # 蒙古语
    "mn": "Монгол",
    "mon": "Монгол",

    # 哈萨克语
    "kk": "Қазақ",
    "kaz": "Қазақ",

    # 乌兹别克语
    "uz": "Oʻzbek",
    "uzb": "Oʻzbek",

    # === 非洲语言 ===
    # 斯瓦希里语
    "sw": "Kiswahili",
    "swa": "Kiswahili",

    # 南非荷兰语
    "af": "Afrikaans",
    "afr": "Afrikaans",

    # 祖鲁语
    "zu": "isiZulu",
    "zul": "isiZulu",

    # 科萨语
    "xh": "isiXhosa",
    "xho": "isiXhosa",

    # 豪萨语
    "ha": "Hausa",
    "hau": "Hausa",

    # 约鲁巴语
    "yo": "Yorùbá",
    "yor": "Yorùbá",

    # 伊博语
    "ig": "Igbo",
    "ibo": "Igbo",

    # 阿姆哈拉语
    "am": "አማርኛ",
    "amh": "አማርኛ",

    # === 美洲语言 ===
    # 克丘亚语
    "qu": "Runa Simi",
    "que": "Runa Simi",

    # 瓜拉尼语
    "gn": "Guarani",
    "grn": "Guarani",

    # === 其他语言 ===
    # 世界语
    "eo": "Esperanto",
    "epo": "Esperanto",

    # 拉丁语
    "la": "Latina",
    "lat": "Latina",

    # 梵语
    "sa": "संस्कृतम्",
    "san": "संस्कृतम्",

    # === 未定义 ===
    "und": "Undetermined",
}


def get_language_name(language_code: str) -> str:
    """
    获取语言的原生名称

    Args:
        language_code: 语言代码（支持基础代码和扩展代码，如 zh, en, zh-hans, zh-hans-cn）

    Returns:
        语言的原生名称（使用该语言的文字）

    Note:
        使用渐进式回退策略来保留脚本/区域特异性：
        1. 尝试完整标签（如 zh-hans-cn）
        2. 尝试 language-script（如 zh-hans）
        3. 尝试 language-region（如 zh-cn）
        4. 尝试基础语言（如 zh）
        5. 返回大写代码
    """
    # 规范化：转小写并将下划线替换为连字符
    lang_code_lower = language_code.lower().replace('_', '-')

    # 首先尝试直接匹配（包括扩展代码）
    if lang_code_lower in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[lang_code_lower]

    # 如果是扩展代码（包含连字符），使用渐进式回退
    if '-' in lang_code_lower:
        parts = lang_code_lower.split('-')

        # 如果有多个子标签（如 zh-hans-cn），尝试各种组合
        if len(parts) >= 3:
            # 尝试 language-script (如 zh-hans)
            lang_script = f"{parts[0]}-{parts[1]}"
            if lang_script in LANGUAGE_NAMES:
                return LANGUAGE_NAMES[lang_script]

            # 尝试 language-region (如 zh-cn)
            lang_region = f"{parts[0]}-{parts[2]}"
            if lang_region in LANGUAGE_NAMES:
                return LANGUAGE_NAMES[lang_region]

        # 最后尝试基础语言代码
        base_code = parts[0]
        if base_code in LANGUAGE_NAMES:
            return LANGUAGE_NAMES[base_code]

    # 未找到映射，返回大写的语言代码
    return language_code.upper()
