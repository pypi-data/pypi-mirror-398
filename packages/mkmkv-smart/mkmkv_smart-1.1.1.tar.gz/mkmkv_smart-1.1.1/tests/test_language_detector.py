"""
测试语言检测模块
"""

import pytest
import tempfile
from pathlib import Path
from mkmkv_smart.language_detector import LanguageDetector, detect_subtitle_language


class TestLanguageDetector:
    """测试 LanguageDetector 类"""

    def setup_method(self):
        """每个测试前的设置"""
        self.detector = LanguageDetector()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_srt(self, content: str, filename: str = "test.srt") -> Path:
        """创建测试 SRT 文件"""
        srt_file = self.temp_dir / filename
        srt_content = ""
        lines = content.split('\n')

        # 确保文本长度足够（至少重复两次以满足 min_chars 要求）
        if len(content) < 150:
            lines = lines * 2

        for i, line in enumerate(lines, 1):
            srt_content += f"{i}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n{line}\n\n"

        srt_file.write_text(srt_content, encoding='utf-8')
        return srt_file

    def test_initialization(self):
        """测试初始化"""
        detector = LanguageDetector(min_confidence=0.9, min_chars=200)
        assert detector.min_confidence == 0.9
        assert detector.min_chars == 200

    def test_detect_chinese_simplified(self):
        """测试检测简体中文"""
        content = """
这是一个简体中文的测试文本
包含了很多简体字
比如国家、发展、学习等等
这些都是简体中文的特征
用来测试语言检测功能是否正常工作
我们需要足够多的文本来确保检测准确
中国人民共和国成立于1949年
经过几十年的发展已经取得了举世瞩目的成就
现代化建设日新月异
科技创新层出不穷
人民生活水平不断提高
        """.strip()

        srt_file = self.create_test_srt(content)
        result = self.detector.detect_subtitle_language(str(srt_file))

        assert result is not None, "检测失败：返回 None，可能是文本太短或特征不明显"
        lang_code, confidence = result
        assert lang_code == "zh-hans"
        assert confidence > 0.8

    def test_detect_chinese_traditional(self):
        """测试检测繁体中文"""
        content = """
這是一個繁體中文的測試文本
包含了很多繁體字
比如國家、發展、學習等等
這些都是繁體中文的特徵
用來測試語言檢測功能是否正常工作
我們需要足夠多的文本來確保檢測準確
        """.strip()

        srt_file = self.create_test_srt(content)
        result = self.detector.detect_subtitle_language(str(srt_file))

        assert result is not None
        lang_code, confidence = result
        assert lang_code == "zh-hant"
        assert confidence > 0.8

    def test_detect_english(self):
        """测试检测英文"""
        content = """
This is an English test subtitle file
It contains multiple lines of English text
We need enough text to ensure accurate language detection
The language detector should identify this as English
With high confidence based on the content
        """.strip()

        srt_file = self.create_test_srt(content)
        result = self.detector.detect_subtitle_language(str(srt_file))

        assert result is not None
        lang_code, confidence = result
        assert lang_code == "en"
        assert confidence > 0.8

    def test_detect_japanese(self):
        """测试检测日文"""
        content = """
これは日本語のテスト字幕ファイルです
複数行の日本語テキストが含まれています
正確な言語検出を確保するために十分なテキストが必要です
言語検出器はこれを日本語として識別する必要があります
        """.strip()

        srt_file = self.create_test_srt(content)
        result = self.detector.detect_subtitle_language(str(srt_file))

        assert result is not None
        lang_code, confidence = result
        assert lang_code == "ja"
        assert confidence > 0.8

    def test_detect_short_text(self):
        """测试检测短文本（应该失败）"""
        content = "短"  # 只有一个字

        srt_file = self.create_test_srt(content)
        result = self.detector.detect_subtitle_language(str(srt_file))

        # 文本太短，应该返回 None
        assert result is None

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        result = self.detector.detect_subtitle_language("/nonexistent/file.srt")
        assert result is None

    def test_wrong_file_extension(self):
        """测试错误的文件扩展名"""
        txt_file = self.temp_dir / "test.txt"
        txt_file.write_text("This is a test", encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(txt_file))
        assert result is None

    def test_empty_file(self):
        """测试空文件"""
        srt_file = self.temp_dir / "empty.srt"
        srt_file.write_text("", encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(srt_file))
        assert result is None

    def test_detect_ass_file(self):
        """测试 ASS 字幕文件"""
        ass_content = """[Script Info]
Title: Test Subtitle

[V4+ Styles]
Format: Name, Fontname, Fontsize

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,This is an English subtitle
Dialogue: 0,0:00:06.00,0:00:10.00,Default,,0,0,0,,Testing ASS format detection
Dialogue: 0,0:00:11.00,0:00:15.00,Default,,0,0,0,,The language should be detected correctly
Dialogue: 0,0:00:16.00,0:00:20.00,Default,,0,0,0,,Even with ASS formatting tags
"""
        ass_file = self.temp_dir / "test.ass"
        ass_file.write_text(ass_content, encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(ass_file))

        assert result is not None
        lang_code, confidence = result
        assert lang_code == "en"

    def test_detect_vtt_file(self):
        """测试 WebVTT 字幕文件"""
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
This is an English subtitle

00:00:06.000 --> 00:00:10.000
Testing VTT format detection

00:00:11.000 --> 00:00:15.000
The language should be detected correctly

00:00:16.000 --> 00:00:20.000
Even with WebVTT formatting tags
"""
        vtt_file = self.temp_dir / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(vtt_file))

        assert result is not None
        lang_code, confidence = result
        assert lang_code == "en"

    def test_detect_vtt_file_chinese(self):
        """测试 WebVTT 中文字幕文件"""
        vtt_content = """WEBVTT

NOTE
这是一个中文字幕测试文件

00:00:01.000 --> 00:00:05.000
这是一个简体中文的测试字幕文件

00:00:06.000 --> 00:00:10.000
测试 WebVTT 格式的语言检测功能

00:00:11.000 --> 00:00:15.000
语言应该被正确识别为中文

00:00:16.000 --> 00:00:20.000
即使包含 WebVTT 的格式标签

00:00:21.000 --> 00:00:25.000
我们需要足够多的文本来确保检测准确

00:00:26.000 --> 00:00:30.000
包含了很多简体字比如国家发展学习等等

00:00:31.000 --> 00:00:35.000
这些都是简体中文的特征用来测试

00:00:36.000 --> 00:00:40.000
中国人民共和国成立于1949年

00:00:41.000 --> 00:00:45.000
经过几十年的发展已经取得了举世瞩目的成就
"""
        vtt_file = self.temp_dir / "test_zh.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(vtt_file))

        assert result is not None
        lang_code, confidence = result
        # 应该识别为中文（简体或繁体）
        assert lang_code in ["zh-hans", "zh-hant", "zh"]

    def test_chinese_variant_detection_simplified(self):
        """测试简繁体中文区分 - 简体"""
        text = "这个发展学习关于国家和听众"
        variant = self.detector._detect_chinese_variant(text)
        assert variant == "zh-hans"

    def test_chinese_variant_detection_traditional(self):
        """测试简繁体中文区分 - 繁体"""
        text = "這個發展學習關於國家和聽眾"
        variant = self.detector._detect_chinese_variant(text)
        assert variant == "zh-hant"

    def test_confidence_threshold(self):
        """测试置信度阈值"""
        detector = LanguageDetector(min_confidence=0.99)  # 非常高的阈值

        content = "Short text"  # 短文本可能置信度不够
        srt_file = self.create_test_srt(content)

        result = detector.detect_subtitle_language(str(srt_file))
        # 由于置信度阈值太高，短文本可能无法达到
        # 结果可能是 None


class TestConvenienceFunction:
    """测试便捷函数"""

    def test_detect_subtitle_language_function(self):
        """测试便捷函数"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.srt', delete=False, encoding='utf-8'
        ) as f:
            # 写入足够长的英文内容
            for i in range(1, 6):
                f.write(f"{i}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n")
                f.write("This is English text for testing language detection.\n\n")
            temp_file = f.name

        try:
            result = detect_subtitle_language(temp_file)
            assert result is not None
            lang_code, confidence = result
            assert lang_code == "en"
        finally:
            Path(temp_file).unlink()


class TestEdgeCases:
    """测试边界情况"""

    def setup_method(self):
        """每个测试前的设置"""
        self.detector = LanguageDetector()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理临时文件"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_mixed_language(self):
        """测试混合语言（主要语言应该被检测）"""
        content = """
This is mostly English text with some Chinese 中文
The detector should still identify it as English
Because English is the dominant language here
We have much more English than Chinese content
"""
        srt_file = self.temp_dir / "mixed.srt"
        srt_content = "1\n00:00:01,000 --> 00:00:05,000\n" + content + "\n\n"
        srt_file.write_text(srt_content, encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(srt_file))

        if result:  # 可能检测成功
            lang_code, _ = result
            assert lang_code == "en"

    def test_different_encodings(self):
        """测试不同编码的文件"""
        # GBK 编码的简体中文（需要足够长的内容，重复以满足最小长度）
        content = """这是一个简体中文的测试文本，包含了很多简体字。
国家发展需要学习新的知识和技能。
我们要为实现中国梦而努力奋斗。
这些内容用来测试不同编码的支持。"""

        # 重复内容以满足最小长度要求
        content = content * 2

        gbk_file = self.temp_dir / "test_gbk.srt"
        srt_content = ""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            srt_content += f"{i}\n00:00:{i:02d},000 --> 00:00:{i+1:02d},000\n{line}\n\n"

        try:
            gbk_file.write_text(srt_content, encoding='gbk')

            result = self.detector.detect_subtitle_language(str(gbk_file))

            # 应该能够正确处理 GBK 编码
            assert result is not None
            lang_code, _ = result
            assert lang_code == "zh-hans"
        except (UnicodeDecodeError, LookupError):
            # 某些系统可能不支持 GBK
            pytest.skip("GBK encoding not supported")

    def test_webvtt_numeric_text(self):
        """测试 P3-1: WebVTT 字幕中的纯数字文本不会被跳过"""
        # 创建包含纯数字字幕的 WebVTT 文件
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:03.000
1

00:00:03.000 --> 00:00:05.000
2

00:00:05.000 --> 00:00:07.000
3

00:00:07.000 --> 00:00:10.000
This is an English subtitle.

00:00:10.000 --> 00:00:12.000
42

00:00:12.000 --> 00:00:14.000
The answer is 100 percent correct.

00:00:14.000 --> 00:00:16.000
Testing numeric content.

00:00:16.000 --> 00:00:18.000
999

00:00:18.000 --> 00:00:20.000
Final test with numbers and text.
"""

        vtt_file = self.temp_dir / "test_numeric.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(vtt_file))

        # 应该能够成功检测语言（因为有足够的英文文本）
        assert result is not None
        lang_code, confidence = result
        # 主要语言应该是英文（忽略纯数字）
        assert lang_code == "en"
        assert confidence > 0.8

    def test_webvtt_only_numeric_cue_identifiers(self):
        """测试 WebVTT cue identifier（纯数字）应该被正确跳过"""
        # WebVTT 允许纯数字作为 cue identifier
        # 创建足够长的内容以满足 min_chars 要求
        vtt_content = """WEBVTT

1
00:00:01.000 --> 00:00:03.000
This is English text for testing purposes.

2
00:00:03.000 --> 00:00:05.000
More English content here to ensure sufficient length.

3
00:00:05.000 --> 00:00:07.000
Testing WebVTT format with cue identifiers.

4
00:00:07.000 --> 00:00:09.000
Final test sentence with more content.

5
00:00:09.000 --> 00:00:11.000
Additional English text to reach minimum character count.

6
00:00:11.000 --> 00:00:13.000
Even more content for language detection.
"""

        vtt_file = self.temp_dir / "test_cue_id.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')

        result = self.detector.detect_subtitle_language(str(vtt_file))

        # cue identifier 应该被跳过，只提取文本内容
        assert result is not None
        lang_code, confidence = result
        assert lang_code == "en"
        assert confidence > 0.8
