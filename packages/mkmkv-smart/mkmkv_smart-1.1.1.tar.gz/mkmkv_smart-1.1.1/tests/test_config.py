"""
测试配置管理模块
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from mkmkv_smart.config import (
    MatchConfig,
    LanguageConfig,
    OutputConfig,
    LanguageDetectionConfig,
    AudioDetectionConfig,
    Config,
    create_default_config
)


class TestMatchConfig:
    """测试 MatchConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = MatchConfig()
        assert config.threshold == 30.0
        assert config.method == "hybrid"
        assert config.keep_year is True
        assert config.keep_episode is True

    def test_custom_values(self):
        """测试自定义值"""
        config = MatchConfig(
            threshold=50.0,
            method="token_set",
            keep_year=False,
            keep_episode=False
        )
        assert config.threshold == 50.0
        assert config.method == "token_set"
        assert config.keep_year is False
        assert config.keep_episode is False


class TestLanguageConfig:
    """测试 LanguageConfig 数据类"""

    def test_default_priority(self):
        """测试默认优先级"""
        config = LanguageConfig()
        assert config.priority == ["zh-hans", "zh-hant", "zh", "en", "ja", "ko"]

    def test_custom_priority(self):
        """测试自定义优先级"""
        config = LanguageConfig(priority=["en", "zh"])
        assert config.priority == ["en", "zh"]


class TestOutputConfig:
    """测试 OutputConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = OutputConfig()
        assert config.default_charset == "UTF-8"

    def test_custom_values(self):
        """测试自定义值"""
        config = OutputConfig(
            default_charset="GBK"
        )
        assert config.default_charset == "GBK"


class TestLanguageDetectionConfig:
    """测试 LanguageDetectionConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = LanguageDetectionConfig()
        assert config.enabled is True
        assert config.min_confidence == 0.8
        assert config.min_chars == 100

    def test_custom_values(self):
        """测试自定义值"""
        config = LanguageDetectionConfig(
            enabled=False,
            min_confidence=0.9,
            min_chars=200
        )
        assert config.enabled is False
        assert config.min_confidence == 0.9
        assert config.min_chars == 200


class TestAudioDetectionConfig:
    """测试 AudioDetectionConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = AudioDetectionConfig()
        assert config.enabled is False
        assert config.model_size == "small"
        assert config.device == "cpu"
        assert config.compute_type == "int8"
        assert config.min_confidence == 0.7
        assert config.max_duration == 30
        assert config.smart_sampling is True
        assert config.max_attempts == 3

    def test_custom_values(self):
        """测试自定义值"""
        config = AudioDetectionConfig(
            enabled=True,
            model_size="large",
            device="cuda",
            compute_type="float16",
            min_confidence=0.8,
            max_duration=60,
            smart_sampling=False,
            max_attempts=5
        )
        assert config.enabled is True
        assert config.model_size == "large"
        assert config.device == "cuda"
        assert config.compute_type == "float16"
        assert config.min_confidence == 0.8
        assert config.max_duration == 60
        assert config.smart_sampling is False
        assert config.max_attempts == 5


class TestConfig:
    """测试 Config 主配置类"""

    def test_default_initialization(self):
        """测试默认初始化"""
        config = Config()
        assert isinstance(config.match, MatchConfig)
        assert isinstance(config.language, LanguageConfig)
        assert isinstance(config.output, OutputConfig)

    def test_custom_initialization(self):
        """测试自定义初始化"""
        match = MatchConfig(threshold=40.0)
        language = LanguageConfig(priority=["en"])
        output = OutputConfig(default_charset="GBK")

        config = Config(match=match, language=language, output=output)
        assert config.match.threshold == 40.0
        assert config.language.priority == ["en"]
        assert config.output.default_charset == "GBK"

    def test_to_dict(self):
        """测试转换为字典"""
        config = Config()
        data = config.to_dict()

        assert "match" in data
        assert "language" in data
        assert "output" in data
        assert data["match"]["threshold"] == 30.0
        assert data["language"]["priority"] == ["zh-hans", "zh-hant", "zh", "en", "ja", "ko"]

    def test_save_and_load(self):
        """测试保存和加载配置"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name

        try:
            # 创建并保存配置
            config1 = Config()
            config1.match.threshold = 50.0
            config1.language.priority = ["en", "zh"]
            config1.save(temp_file)

            # 加载配置
            config2 = Config.load(temp_file)

            # 验证
            assert config2.match.threshold == 50.0
            assert config2.language.priority == ["en", "zh"]

        finally:
            # 清理
            Path(temp_file).unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        # 新的验证行为：应该抛出 FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            Config.load("/tmp/nonexistent_config_12345.yaml")

        assert "配置文件不存在" in str(exc_info.value)

    def test_load_partial_config(self):
        """测试加载部分配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # 只写入部分配置
            yaml.dump({
                'match': {'threshold': 60.0}
            }, f)
            temp_file = f.name

        try:
            config = Config.load(temp_file)

            # 验证部分覆盖
            assert config.match.threshold == 60.0
            # 其他应该是默认值
            assert config.match.method == "hybrid"
            assert config.language.priority == ["zh-hans", "zh-hant", "zh", "en", "ja", "ko"]

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_load_empty_config(self):
        """测试加载空配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # 写入空内容
            temp_file = f.name

        try:
            config = Config.load(temp_file)

            # 应该是默认值
            assert config.match.threshold == 30.0

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_save_creates_valid_yaml(self):
        """测试保存创建有效的 YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name

        try:
            config = Config()
            config.save(temp_file)

            # 读取并验证 YAML
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            assert 'match' in data
            assert 'language' in data
            assert 'output' in data
            assert data['match']['threshold'] == 30.0

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_config_with_chinese_content(self):
        """测试包含中文内容的配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            temp_file = f.name

        try:
            config = Config()
            config.save(temp_file)

            # 验证文件可以用 UTF-8 读取
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content  # 不应该为空

        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestCreateDefaultConfig:
    """测试创建默认配置函数"""

    def test_create_default_config(self, capsys):
        """测试创建默认配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name

        try:
            # 删除临时文件，让函数创建
            Path(temp_file).unlink()

            create_default_config(temp_file)

            # 验证文件存在
            assert Path(temp_file).exists()

            # 验证内容
            config = Config.load(temp_file)
            assert config.match.threshold == 30.0

            # 验证打印输出
            captured = capsys.readouterr()
            assert "已创建默认配置文件" in captured.out

        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestConfigIntegration:
    """测试配置集成场景"""

    def test_full_config_workflow(self):
        """测试完整配置工作流"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name

        try:
            # 1. 创建配置
            config1 = Config()
            config1.match.threshold = 45.0
            config1.match.method = "token_set"
            config1.language.priority = ["zh-hans", "en"]
            config1.output.default_charset = "UTF-8"

            # 2. 保存
            config1.save(temp_file)

            # 3. 加载
            config2 = Config.load(temp_file)

            # 4. 验证所有字段
            assert config2.match.threshold == 45.0
            assert config2.match.method == "token_set"
            assert config2.language.priority == ["zh-hans", "en"]
            assert config2.output.default_charset == "UTF-8"

            # 5. 修改并再次保存
            config2.match.threshold = 55.0
            config2.save(temp_file)

            # 6. 再次加载验证
            config3 = Config.load(temp_file)
            assert config3.match.threshold == 55.0

        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_config_with_all_methods(self):
        """测试所有匹配方法"""
        methods = ["token_set", "token_sort", "partial", "hybrid"]

        for method in methods:
            config = Config()
            config.match.method = method
            assert config.match.method == method

    def test_config_with_various_thresholds(self):
        """测试各种阈值"""
        thresholds = [0.0, 25.0, 50.0, 75.0, 100.0]

        for threshold in thresholds:
            config = Config()
            config.match.threshold = threshold
            assert config.match.threshold == threshold

    def test_config_language_priority_order(self):
        """测试语言优先级顺序"""
        priority = ["ja", "ko", "en", "zh"]
        config = Config()
        config.language.priority = priority

        assert config.language.priority == priority
        # 顺序应该保持
        for i, lang in enumerate(priority):
            assert config.language.priority[i] == lang
