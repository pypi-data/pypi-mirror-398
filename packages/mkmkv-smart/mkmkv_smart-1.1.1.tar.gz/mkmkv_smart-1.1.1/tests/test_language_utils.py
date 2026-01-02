"""
测试 language_utils 模块

测试语言代码映射和工具函数。
"""

import pytest
from mkmkv_smart.language_utils import get_language_name, LANGUAGE_NAMES


class TestLanguageNames:
    """测试 LANGUAGE_NAMES 字典"""

    def test_language_names_not_empty(self):
        """测试语言映射表不为空"""
        assert len(LANGUAGE_NAMES) > 0

    def test_language_names_has_common_languages(self):
        """测试包含常见语言"""
        common_languages = ["zh", "en", "ja", "ko", "fr", "de", "es", "it", "ru"]
        for lang in common_languages:
            assert lang in LANGUAGE_NAMES

    def test_language_names_has_3letter_codes(self):
        """测试包含 3 字母代码"""
        three_letter_codes = ["chi", "eng", "jpn", "kor", "fra", "deu", "spa", "ita", "rus"]
        for code in three_letter_codes:
            assert code in LANGUAGE_NAMES

    def test_language_names_has_extended_codes(self):
        """测试包含扩展代码"""
        extended_codes = ["zh-hans", "zh-hant", "en-us", "en-gb", "fr-ca", "de-ch"]
        for code in extended_codes:
            assert code in LANGUAGE_NAMES

    def test_language_names_has_aliases(self):
        """测试包含常用别名"""
        aliases = ["chs", "cht", "gb", "big5"]
        for alias in aliases:
            assert alias in LANGUAGE_NAMES

    def test_newly_added_languages(self):
        """测试第 8 轮添加的语言"""
        newly_added = [
            "ne",   # 尼泊尔语
            "si",   # 僧伽罗语
            "ps",   # 普什图语
            "ku",   # 库尔德语
            "az",   # 阿塞拜疆语
            "ka",   # 格鲁吉亚语
            "hy",   # 亚美尼亚语
            "bs",   # 波斯尼亚语
        ]
        for lang in newly_added:
            assert lang in LANGUAGE_NAMES, f"Language {lang} not found"

    def test_korean_variants(self):
        """测试韩语/朝鲜语变体"""
        assert LANGUAGE_NAMES["ko-kr"] == "한국어（대한민국）"
        assert LANGUAGE_NAMES["ko-kp"] == "조선어（조선）"


class TestGetLanguageName:
    """测试 get_language_name 函数"""

    def test_get_language_name_known(self):
        """测试获取已知语言名称"""
        assert get_language_name("zh-hans") == "简体中文"
        assert get_language_name("en") == "English"
        assert get_language_name("ja") == "日本語"

    def test_get_language_name_unknown(self):
        """测试获取未知语言名称"""
        # 未知语言代码应该返回大写的原始代码
        assert get_language_name("unknown") == "UNKNOWN"
        assert get_language_name("xxx") == "XXX"

    def test_get_language_name_case_insensitive(self):
        """测试语言代码大小写不敏感"""
        assert get_language_name("ZH-HANS") == "简体中文"
        assert get_language_name("En") == "English"
        assert get_language_name("JA") == "日本語"

    def test_get_language_name_aliases(self):
        """测试语言别名"""
        assert get_language_name("chs") == "简体中文"
        assert get_language_name("cht") == "繁體中文"
        assert get_language_name("gb") == "简体中文"
        assert get_language_name("big5") == "繁體中文"
        # 大小写不敏感
        assert get_language_name("CHS") == "简体中文"
        assert get_language_name("CHT") == "繁體中文"

    def test_get_language_name_with_underscore(self):
        """测试带下划线的语言代码"""
        # 下划线应该被规范化为连字符
        assert get_language_name("zh_hans") == "简体中文"
        assert get_language_name("en_us") == "English (United States)"

    def test_get_language_name_base_code_fallback(self):
        """测试扩展代码回退到基础代码"""
        # 未知的扩展代码应该回退到基础代码
        assert get_language_name("zh-unknown") == "中文"
        assert get_language_name("en-unknown") == "English"

    def test_get_language_name_3letter_codes(self):
        """测试 3 字母代码"""
        assert get_language_name("chi") == "中文"
        assert get_language_name("eng") == "English"
        assert get_language_name("jpn") == "日本語"
        assert get_language_name("kor") == "한국어"

    def test_get_language_name_newly_added(self):
        """测试新添加的语言名称"""
        assert get_language_name("ne") == "नेपाली"
        assert get_language_name("si") == "සිංහල"
        assert get_language_name("ps") == "پښتو"
        assert get_language_name("ku") == "Kurdî"
        assert get_language_name("az") == "Azərbaycan"
        assert get_language_name("ka") == "ქართული"
        assert get_language_name("hy") == "Հայերեն"
        assert get_language_name("bs") == "Bosanski"

    def test_get_language_name_korean_variants(self):
        """测试韩语/朝鲜语变体名称"""
        assert get_language_name("ko-kr") == "한국어（대한민국）"
        assert get_language_name("ko-kp") == "조선어（조선）"

    def test_get_language_name_multi_subtag_bcp47(self):
        """测试多子标签 BCP-47 标签的渐进式回退"""
        # 完整标签不存在，应回退到 language-script
        # zh-hans-cn → zh-hans (简体中文) 而不是 zh (中文)
        assert get_language_name("zh-hans-cn") == "简体中文"
        assert get_language_name("zh-hant-tw") == "繁體中文"

        # 如果 language-script 也不存在，尝试 language-region
        # 假设 en-latn-us 不存在，应尝试 en-us
        assert get_language_name("en-latn-us") == "English (United States)"

        # 如果都不存在，回退到基础语言
        # xx-yyyy-zz → xx（如果 xx 存在）
        assert get_language_name("ja-jpan-jp") == "日本語（日本）"  # ja-jp 存在

        # 完全未知的标签
        assert get_language_name("xx-yyyy-zz") == "XX-YYYY-ZZ"

        # 大小写不敏感
        assert get_language_name("ZH-HANS-CN") == "简体中文"
        assert get_language_name("Zh-Hant-TW") == "繁體中文"
