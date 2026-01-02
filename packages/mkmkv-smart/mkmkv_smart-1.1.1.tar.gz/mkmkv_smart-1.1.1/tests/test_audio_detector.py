"""
测试音频语言检测模块
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestAudioLanguageDetector:
    """测试 AudioLanguageDetector 类"""

    def test_initialization(self):
        """测试初始化"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        detector = AudioLanguageDetector(
            model_size="small",
            device="cpu",
            compute_type="int8",
            min_confidence=0.7
        )

        assert detector.model_size == "small"
        assert detector.device == "cpu"
        assert detector.compute_type == "int8"
        assert detector.min_confidence == 0.7
        assert detector._model is None  # 模型未加载

    def test_load_model_without_faster_whisper(self):
        """测试在没有安装 faster-whisper 时加载模型"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        detector = AudioLanguageDetector()

        # 使用 patch 模拟导入失败
        with patch.dict('sys.modules', {'faster_whisper': None}):
            # 应该抛出 ImportError
            with pytest.raises(ImportError, match="faster-whisper 未安装"):
                detector._load_model()

    @pytest.mark.skipif(
        True,
        reason="需要安装 faster-whisper: pip install mkmkv-smart[audio]"
    )
    def test_load_model_with_faster_whisper(self):
        """测试成功加载模型（需要 faster-whisper）"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        detector = AudioLanguageDetector(model_size="tiny")
        detector._load_model()

        assert detector._model is not None

    def test_extract_audio_track_nonexistent_file(self):
        """测试提取不存在的文件的音轨"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        detector = AudioLanguageDetector()
        result = detector.extract_audio_track("/nonexistent/video.mp4")

        assert result is None

    @patch('subprocess.run')
    def test_extract_audio_track_success(self, mock_run):
        """测试成功提取音轨"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        # 创建临时视频文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            video_file = f.name
            f.write(b"fake video data")

        try:
            detector = AudioLanguageDetector()

            # 模拟成功的 ffmpeg 调用
            mock_run.return_value = Mock(returncode=0)

            result = detector.extract_audio_track(video_file, track_index=0, duration=30)

            # 应该返回临时音频文件路径
            assert result is not None
            assert Path(result).suffix == '.wav'

            # 清理临时文件
            if result and Path(result).exists():
                Path(result).unlink()

        finally:
            # 清理临时视频文件
            if Path(video_file).exists():
                Path(video_file).unlink()

    @patch('subprocess.run')
    def test_extract_audio_track_failure(self, mock_run):
        """测试提取音轨失败"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        # 创建临时视频文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            video_file = f.name
            f.write(b"fake video data")

        try:
            detector = AudioLanguageDetector()

            # 模拟失败的 ffmpeg 调用
            mock_run.side_effect = Exception("ffmpeg error")

            result = detector.extract_audio_track(video_file)

            # 应该返回 None
            assert result is None

        finally:
            # 清理临时视频文件
            if Path(video_file).exists():
                Path(video_file).unlink()

    def test_detect_audio_language_nonexistent_file(self):
        """测试检测不存在的音频文件"""
        from mkmkv_smart.audio_detector import AudioLanguageDetector

        detector = AudioLanguageDetector()
        result = detector.detect_audio_language("/nonexistent/audio.wav")

        assert result is None

    @pytest.mark.skipif(
        True,
        reason="需要安装 faster-whisper: pip install mkmkv-smart[audio]"
    )
    def test_detect_audio_language_with_model(self):
        """测试使用模型检测音频语言（需要 faster-whisper）"""
        # 这个测试需要真实的音频文件和 faster-whisper
        pass

    def test_convenience_function(self):
        """测试便捷函数"""
        from mkmkv_smart.audio_detector import detect_video_audio_language

        # 测试不存在的文件
        result = detect_video_audio_language("/nonexistent/video.mp4")
        assert result is None


class TestAudioDetectorConfiguration:
    """测试音频检测配置"""

    def test_config_audio_detection(self):
        """测试音频检测配置"""
        from mkmkv_smart.config import AudioDetectionConfig

        config = AudioDetectionConfig(
            enabled=True,
            model_size="medium",
            device="cuda",
            compute_type="float16",
            min_confidence=0.8,
            max_duration=60
        )

        assert config.enabled is True
        assert config.model_size == "medium"
        assert config.device == "cuda"
        assert config.compute_type == "float16"
        assert config.min_confidence == 0.8
        assert config.max_duration == 60

    def test_config_load_with_audio_detection(self):
        """测试加载包含音频检测配置的 YAML"""
        from mkmkv_smart.config import Config
        import yaml

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8'
        ) as f:
            yaml_content = """
audio_detection:
  enabled: true
  model_size: small
  device: cpu
  compute_type: int8
  min_confidence: 0.7
  max_duration: 30
"""
            f.write(yaml_content)
            config_file = f.name

        try:
            config = Config.load(config_file)

            assert config.audio_detection.enabled is True
            assert config.audio_detection.model_size == "small"
            assert config.audio_detection.device == "cpu"
            assert config.audio_detection.compute_type == "int8"
            assert config.audio_detection.min_confidence == 0.7
            assert config.audio_detection.max_duration == 30

        finally:
            Path(config_file).unlink()
