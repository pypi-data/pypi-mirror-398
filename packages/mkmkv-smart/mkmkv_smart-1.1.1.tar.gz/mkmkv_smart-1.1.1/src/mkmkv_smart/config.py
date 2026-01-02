"""
配置管理模块

支持 YAML 配置文件和命令行参数。
"""

import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

# 导入权威的匹配方法列表
from .matcher import VALID_MATCH_METHODS

VALID_AUDIO_MODELS = ("tiny", "base", "small", "medium", "large")
VALID_AUDIO_DEVICES = ("cpu", "cuda", "auto")
VALID_AUDIO_COMPUTE_TYPES = ("int8", "int16", "float16", "float32")


@dataclass
class MatchConfig:
    """匹配配置"""
    threshold: float = 30.0
    method: str = "hybrid"
    keep_year: bool = True
    keep_episode: bool = True


@dataclass
class LanguageConfig:
    """语言配置"""
    priority: List[str] = field(default_factory=lambda: [
        "zh-hans", "zh-hant", "zh", "en", "ja", "ko"
    ])


@dataclass
class OutputConfig:
    """输出配置"""
    default_charset: str = "UTF-8"


@dataclass
class LanguageDetectionConfig:
    """语言检测配置"""
    enabled: bool = True  # 默认启用自动语言检测
    min_confidence: float = 0.8
    min_chars: int = 100  # 最小文本长度要求


@dataclass
class AudioDetectionConfig:
    """音频语言检测配置"""
    enabled: bool = False
    model_size: str = "small"  # tiny, base, small, medium, large
    device: str = "cpu"  # cpu, cuda, auto
    compute_type: str = "int8"  # int8, int16, float16, float32
    min_confidence: float = 0.7
    max_duration: int = 30  # 提取音频的最大长度（秒）
    smart_sampling: bool = True  # 智能多点采样（推荐）
    max_attempts: int = 3  # 非智能模式下的最大重试次数


@dataclass
class Config:
    """主配置"""
    match: MatchConfig = field(default_factory=MatchConfig)
    language: LanguageConfig = field(default_factory=LanguageConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    language_detection: LanguageDetectionConfig = field(
        default_factory=LanguageDetectionConfig
    )
    audio_detection: AudioDetectionConfig = field(
        default_factory=AudioDetectionConfig
    )

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "Config":
        """
        加载配置

        Args:
            config_file: 配置文件路径（可选）

        Returns:
            Config 实例
        """
        # 默认配置
        config = cls()

        if config_file:
            config_path = Path(config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {config_file}")
            if not config_path.is_file():
                raise ValueError(f"配置文件不是普通文件: {config_file}")

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(
                    f"配置文件 YAML 格式错误: {config_file}\n"
                    f"详细错误: {str(e)}"
                ) from e
            except UnicodeDecodeError as e:
                raise ValueError(
                    f"配置文件编码错误: {config_file}\n"
                    f"请确保文件使用 UTF-8 编码\n"
                    f"详细错误: {str(e)}"
                ) from e

            if data is None:
                return config
            if not isinstance(data, dict):
                raise ValueError(f"配置文件内容必须是字典: {config_file}")

            # 更新配置
            try:
                if 'match' in data:
                    if not isinstance(data['match'], dict):
                        raise ValueError("match 配置必须是字典")
                    config.match = MatchConfig(**data['match'])
            except TypeError as e:
                raise ValueError(
                    f"match 配置项参数错误\n"
                    f"有效字段: threshold (float), method (str), keep_year (bool), keep_episode (bool)\n"
                    f"详细错误: {str(e)}"
                ) from e

            try:
                if 'language' in data:
                    if not isinstance(data['language'], dict):
                        raise ValueError("language 配置必须是字典")
                    config.language = LanguageConfig(**data['language'])

                    # 验证 priority 字段
                    if not isinstance(config.language.priority, list):
                        raise ValueError(
                            f"language.priority 必须是列表，当前类型: {type(config.language.priority).__name__}"
                        )

                    # 验证列表中的每个元素
                    for i, lang_code in enumerate(config.language.priority):
                        if not isinstance(lang_code, str):
                            raise ValueError(
                                f"language.priority[{i}] 必须是字符串，当前类型: {type(lang_code).__name__}"
                            )
                        if not lang_code or not lang_code.strip():
                            raise ValueError(
                                f"language.priority[{i}] 不能为空字符串"
                            )

                    # 规范化为小写（就地修改）
                    config.language.priority = [
                        code.strip().lower() for code in config.language.priority
                    ]
            except TypeError as e:
                raise ValueError(
                    f"language 配置项参数错误\n"
                    f"有效字段: priority (list)\n"
                    f"详细错误: {str(e)}"
                ) from e

            try:
                if 'output' in data:
                    if not isinstance(data['output'], dict):
                        raise ValueError("output 配置必须是字典")
                    config.output = OutputConfig(**data['output'])
            except TypeError as e:
                raise ValueError(
                    f"output 配置项参数错误\n"
                    f"有效字段: default_charset (str)\n"
                    f"详细错误: {str(e)}"
                ) from e

            try:
                if 'language_detection' in data:
                    if not isinstance(data['language_detection'], dict):
                        raise ValueError("language_detection 配置必须是字典")
                    config.language_detection = LanguageDetectionConfig(
                        **data['language_detection']
                    )
            except TypeError as e:
                raise ValueError(
                    f"language_detection 配置项参数错误\n"
                    f"有效字段: enabled (bool), min_confidence (float), min_chars (int)\n"
                    f"详细错误: {str(e)}"
                ) from e

            try:
                if 'audio_detection' in data:
                    if not isinstance(data['audio_detection'], dict):
                        raise ValueError("audio_detection 配置必须是字典")
                    config.audio_detection = AudioDetectionConfig(
                        **data['audio_detection']
                    )
            except TypeError as e:
                raise ValueError(
                    f"audio_detection 配置项参数错误\n"
                    f"有效字段: enabled (bool), model_size (str), device (str), "
                    f"compute_type (str), min_confidence (float), max_duration (int), "
                    f"smart_sampling (bool), max_attempts (int)\n"
                    f"详细错误: {str(e)}"
                ) from e

            # 配置值验证
            try:
                threshold = float(config.match.threshold)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"match.threshold 必须是 0-100 的数字，当前值: {config.match.threshold}"
                ) from e

            if not 0 <= threshold <= 100:
                raise ValueError(
                    f"match.threshold 必须在 0-100 之间，当前值: {config.match.threshold}"
                )
            config.match.threshold = threshold

            if config.match.method not in VALID_MATCH_METHODS:
                raise ValueError(
                    "match.method 必须是以下之一: "
                    f"{', '.join(VALID_MATCH_METHODS)}，当前值: {config.match.method}"
                )

            if config.audio_detection.model_size not in VALID_AUDIO_MODELS:
                raise ValueError(
                    "audio_detection.model 必须是以下之一: "
                    f"{', '.join(VALID_AUDIO_MODELS)}，当前值: {config.audio_detection.model_size}"
                )

            if config.audio_detection.device not in VALID_AUDIO_DEVICES:
                raise ValueError(
                    "audio_detection.device 必须是以下之一: "
                    f"{', '.join(VALID_AUDIO_DEVICES)}，当前值: {config.audio_detection.device}"
                )

            if config.audio_detection.compute_type not in VALID_AUDIO_COMPUTE_TYPES:
                raise ValueError(
                    "audio_detection.compute_type 必须是以下之一: "
                    f"{', '.join(VALID_AUDIO_COMPUTE_TYPES)}，当前值: {config.audio_detection.compute_type}"
                )

        return config

    def save(self, config_file: str) -> None:
        """
        保存配置到文件

        Args:
            config_file: 配置文件路径
        """
        data = {
            'match': asdict(self.match),
            'language': asdict(self.language),
            'output': asdict(self.output),
            'language_detection': asdict(self.language_detection),
            'audio_detection': asdict(self.audio_detection)
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'match': asdict(self.match),
            'language': asdict(self.language),
            'output': asdict(self.output),
            'language_detection': asdict(self.language_detection),
            'audio_detection': asdict(self.audio_detection)
        }


def create_default_config(output_file: str = "config.yaml") -> None:
    """
    创建默认配置文件

    Args:
        output_file: 输出文件路径
    """
    config = Config()
    config.save(output_file)
    print(f"已创建默认配置文件: {output_file}")


if __name__ == '__main__':
    # 创建示例配置
    create_default_config("config.example.yaml")
