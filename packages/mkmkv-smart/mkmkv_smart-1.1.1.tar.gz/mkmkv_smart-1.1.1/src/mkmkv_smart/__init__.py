"""
mkmkv-smart: 智能视频字幕合并工具

主要功能:
- 智能文件名匹配（基于多种模糊匹配算法）
- 自动字幕语言检测
- 批量处理视频和字幕文件
- 干运行模式预览
"""

# 从已安装的包元数据中读取版本号（单一版本源）
try:
    from importlib.metadata import version
    __version__ = version("mkmkv-smart")
except Exception:
    # 开发模式下（未安装）使用默认版本
    __version__ = "dev"

__author__ = "Yaohui"

from .matcher import SmartMatcher
from .normalizer import FileNormalizer
from .merger import MKVMerger
from .config import Config

__all__ = [
    "SmartMatcher",
    "FileNormalizer",
    "MKVMerger",
    "Config",
    "__version__",
]
