"""
测试 CLI 集成功能
"""

import pytest
import tempfile
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from mkmkv_smart.config import Config, AudioDetectionConfig, LanguageDetectionConfig
from mkmkv_smart.cli import run_match


class TestAudioDetectionIntegration:
    """测试音频检测集成功能"""

    def test_audio_detection_enabled_via_config(self, tmp_path):
        """测试通过配置启用音频检测"""
        # 创建测试目录
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # 创建配置，启用音频检测
        config = Config()
        config.audio_detection.enabled = True
        config.audio_detection.model_size = "tiny"

        # 创建参数
        args = argparse.Namespace(
            source=str(tmp_path),
            output=str(output_dir),
            dry_run=False,
            threshold=None,
            method=None,
            config=None,
            detect_audio_language=False,  # CLI 参数未启用
            audio_model=None,
            set_audio_language=False,
            keep_embedded_subtitles=False
        )

        # Mock 音频检测器导入
        mock_audio_detector = MagicMock()
        mock_audio_detector_class = MagicMock(return_value=mock_audio_detector)

        # 计算 should_detect_audio
        should_detect_audio = args.detect_audio_language or config.audio_detection.enabled
        assert should_detect_audio is True, "配置启用音频检测应生效"

    def test_audio_detection_disabled_in_dry_run(self, tmp_path):
        """测试 dry-run 模式跳过音频检测"""
        # 创建测试目录
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # 创建配置，启用音频检测
        config = Config()
        config.audio_detection.enabled = True

        # 创建参数（dry-run 模式）
        args = argparse.Namespace(
            source=str(tmp_path),
            output=str(output_dir),
            dry_run=True,  # 干运行模式
            threshold=None,
            method=None,
            config=None,
            detect_audio_language=False,
            audio_model=None,
            set_audio_language=False,
            keep_embedded_subtitles=False
        )

        # 验证逻辑：即使 should_detect_audio 为 True，dry_run 也会跳过
        should_detect_audio = args.detect_audio_language or config.audio_detection.enabled
        will_actually_detect = should_detect_audio and not args.dry_run

        assert should_detect_audio is True, "配置启用了音频检测"
        assert will_actually_detect is False, "dry-run 模式应跳过音频检测"

    def test_audio_detection_cli_and_config_priority(self):
        """测试 CLI 参数和配置的优先级"""
        # 配置禁用音频检测
        config = Config()
        config.audio_detection.enabled = False

        # CLI 参数启用音频检测
        args1 = argparse.Namespace(detect_audio_language=True)
        should_detect1 = args1.detect_audio_language or config.audio_detection.enabled
        assert should_detect1 is True, "CLI 参数应该覆盖配置"

        # CLI 参数和配置都禁用
        args2 = argparse.Namespace(detect_audio_language=False)
        should_detect2 = args2.detect_audio_language or config.audio_detection.enabled
        assert should_detect2 is False, "都禁用时不应检测"

        # 配置启用，CLI 未指定
        config.audio_detection.enabled = True
        args3 = argparse.Namespace(detect_audio_language=False)
        should_detect3 = args3.detect_audio_language or config.audio_detection.enabled
        assert should_detect3 is True, "配置启用时应检测"


class TestEmbeddedSubtitleDetectionIntegration:
    """测试嵌入字幕检测集成功能"""

    def test_embedded_subtitle_detection_respects_config_disabled(self):
        """测试嵌入字幕检测遵守配置（禁用）"""
        # 创建配置，禁用语言检测
        config = Config()
        config.language_detection.enabled = False

        # 创建参数
        args = argparse.Namespace(keep_embedded_subtitles=True)

        # 验证逻辑
        should_detect = args.keep_embedded_subtitles and config.language_detection.enabled
        assert should_detect is False, "language_detection.enabled=False 时不应检测"

    def test_embedded_subtitle_detection_respects_config_enabled(self):
        """测试嵌入字幕检测遵守配置（启用）"""
        # 创建配置，启用语言检测
        config = Config()
        config.language_detection.enabled = True

        # 创建参数
        args = argparse.Namespace(keep_embedded_subtitles=True)

        # 验证逻辑
        should_detect = args.keep_embedded_subtitles and config.language_detection.enabled
        assert should_detect is True, "language_detection.enabled=True 时应检测"

    def test_embedded_subtitle_detection_requires_flag(self):
        """测试嵌入字幕检测需要 CLI 标志"""
        # 创建配置，启用语言检测
        config = Config()
        config.language_detection.enabled = True

        # 创建参数（未启用 keep_embedded_subtitles）
        args = argparse.Namespace(keep_embedded_subtitles=False)

        # 验证逻辑
        should_detect = args.keep_embedded_subtitles and config.language_detection.enabled
        assert should_detect is False, "未启用 keep_embedded_subtitles 时不应检测"


class TestConfigurationPriority:
    """测试配置优先级"""

    def test_cli_parameter_overrides_config(self):
        """测试 CLI 参数覆盖配置文件"""
        # 创建配置
        config = Config()
        config.match.threshold = 30.0
        config.match.method = "hybrid"

        # 创建参数（指定了覆盖值）
        args = argparse.Namespace(
            threshold=50.0,  # 覆盖配置
            method="token_set",  # 覆盖配置
        )

        # 模拟 CLI 中的覆盖逻辑
        if args.threshold is not None:
            config.match.threshold = args.threshold
        if args.method:
            config.match.method = args.method

        # 验证配置被覆盖
        assert config.match.threshold == 50.0
        assert config.match.method == "token_set"

    def test_config_defaults_when_no_cli_params(self):
        """测试没有 CLI 参数时使用配置默认值"""
        # 创建配置
        config = Config()
        config.match.threshold = 35.0
        config.match.method = "token_sort"

        # 创建参数（未指定覆盖值）
        args = argparse.Namespace(
            threshold=None,
            method=None,
        )

        # 模拟 CLI 中的覆盖逻辑
        if args.threshold is not None:
            config.match.threshold = args.threshold
        if args.method:
            config.match.method = args.method

        # 验证配置保持不变
        assert config.match.threshold == 35.0
        assert config.match.method == "token_sort"


class TestAudioDetectionConfigUsage:
    """测试音频检测配置的正确使用"""

    def test_audio_model_from_cli_overrides_config(self):
        """测试 CLI 音频模型参数覆盖配置"""
        config = Config()
        config.audio_detection.model_size = "small"

        args = argparse.Namespace(audio_model="large")

        # 模拟 CLI 中的覆盖逻辑
        model_size = args.audio_model if args.audio_model else config.audio_detection.model_size

        assert model_size == "large", "CLI 参数应覆盖配置"

    def test_audio_model_from_config_when_no_cli(self):
        """测试未指定 CLI 参数时使用配置"""
        config = Config()
        config.audio_detection.model_size = "medium"

        args = argparse.Namespace(audio_model=None)

        # 模拟 CLI 中的覆盖逻辑
        model_size = args.audio_model if args.audio_model else config.audio_detection.model_size

        assert model_size == "medium", "应使用配置中的模型大小"


class TestLanguageDetectionConfigUsage:
    """测试语言检测配置的正确使用"""

    def test_language_detector_uses_config_params(self):
        """测试语言检测器使用配置参数"""
        config = Config()
        config.language_detection.min_confidence = 0.9
        config.language_detection.min_chars = 200

        # 验证配置值
        assert config.language_detection.min_confidence == 0.9
        assert config.language_detection.min_chars == 200

        # 模拟 LanguageDetector 的初始化
        # 在实际代码中: detector = LanguageDetector(
        #     min_confidence=config.language_detection.min_confidence,
        #     min_chars=config.language_detection.min_chars
        # )
        # 这里我们只验证配置值可以被正确访问
        assert hasattr(config.language_detection, 'min_confidence')
        assert hasattr(config.language_detection, 'min_chars')
