"""
MKV 音轨元数据编辑模块

使用 mkvpropedit 修改 MKV 文件的音轨语言信息
"""

import json
import logging
import os
import re
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any, Union, TYPE_CHECKING

from . import language_utils
from .security_utils import _safe_path_arg, _validate_output_path

if TYPE_CHECKING:
    from .language_detector import LanguageDetector

# 配置日志
logger = logging.getLogger(__name__)

# 常量定义
UNDEFINED_LANGUAGE = 'und'
DEFAULT_TIMEOUT = 60  # 秒
SUBPROCESS_TIMEOUT = 120  # 提取字幕可能需要更长时间

# ISO 639-1 -> IETF BCP-47 默认标签映射
IETF_DEFAULTS = {
    'zh': 'zh-Hans',     # 中文 -> 简体中文
    'en': 'en-US',       # 英语 -> 美式英语
    'ja': 'ja-JP',       # 日语 -> 日本日语
    'ko': 'ko-KR',       # 韩语 -> 韩国韩语
    'fr': 'fr-FR',       # 法语 -> 法国法语
    'de': 'de-DE',       # 德语 -> 德国德语
    'es': 'es-ES',       # 西班牙语 -> 西班牙西语
    'pt': 'pt-BR',       # 葡萄牙语 -> 巴西葡语
}


def convert_to_ietf_tag(language_code: str) -> str:
    """
    将语言代码转换为 IETF BCP-47 格式

    Args:
        language_code: 语言代码（支持 ISO 639-1/2/3 及扩展代码）

    Returns:
        IETF BCP-47 标签（如 zh-Hans, en-US）

    Examples:
        >>> convert_to_ietf_tag('zh')
        'zh-Hans'
        >>> convert_to_ietf_tag('en')
        'en-US'
        >>> convert_to_ietf_tag('zh-hans')
        'zh-Hans'
        >>> convert_to_ietf_tag('en-gb')
        'en-GB'
    """
    if not language_code:
        return ""

    code = language_code.lower().replace('_', '-')

    # 已经是完整的 IETF 标签（包含 - 的）
    if '-' in code:
        parts = code.split('-')
        language = parts[0].lower()
        subtags = []
        for part in parts[1:]:
            # Script subtag (4 letters): Title case (如 Hans, Hant)
            if len(part) == 4 and part.isalpha():
                subtags.append(part.title())
            # Region subtag (2 letters): Upper case (如 US, GB, CN)
            elif len(part) == 2 and part.isalpha():
                subtags.append(part.upper())
            # Variant subtag (5-8 chars or 4 chars starting with digit)
            else:
                subtags.append(part)
        return '-'.join([language] + subtags)

    # 简单语言代码，使用默认映射
    return IETF_DEFAULTS.get(code, code)


class AudioTrackEditor:
    """MKV 音轨和字幕元数据编辑器"""

    def __init__(self, mkvpropedit_path: Optional[str] = None):
        """
        初始化编辑器

        Args:
            mkvpropedit_path: mkvpropedit 可执行文件路径（可选）
        """
        self.mkvpropedit_path = mkvpropedit_path or "mkvpropedit"

        # 检查 mkvpropedit 是否可用
        if not self.is_mkvpropedit_available():
            raise RuntimeError(
                "mkvpropedit 未安装或不在 PATH 中\n"
                "请安装 mkvtoolnix: brew install mkvtoolnix (macOS) "
                "或 apt install mkvtoolnix (Linux)"
            )

    def is_mkvpropedit_available(self) -> bool:
        """
        检查 mkvpropedit 是否可用

        Returns:
            True 如果 mkvpropedit 可用
        """
        return shutil.which(self.mkvpropedit_path) is not None

    def _cleanup_failed_output(self, output_file: str) -> None:
        """
        清理失败的输出文件

        Args:
            output_file: 输出文件路径
        """
        output_path = Path(output_file)
        if output_path.exists():
            try:
                output_path.unlink()
                logger.info(f"已清理失败的输出文件: {output_file}")
            except Exception as e:
                logger.warning(f"清理输出文件失败: {output_file}, {e}")

    def set_audio_track_language(
        self,
        video_file: str,
        track_index: int,
        language_code: str,
        track_name: Optional[str] = None,
        original_code: Optional[str] = None
    ) -> bool:
        """
        设置音轨的语言信息

        Args:
            video_file: MKV 视频文件路径
            track_index: 音轨索引（从 0 开始）
            language_code: ISO 639-2 语言代码（如 'jpn', 'eng', 'chi'）
            track_name: 可选的音轨名称（如 '日语', 'Japanese'）
            original_code: 可选的原始语言代码（ISO 639-1 或 BCP-47），用于生成准确的 IETF 标签

        Returns:
            True 如果成功

        Note:
            mkvpropedit 使用的音轨编号从 1 开始，需要转换
        """
        # 验证轨道索引
        if track_index < 0:
            logger.warning(f"无效的音轨索引: {track_index}")
            return False

        video_path = Path(video_file)

        if not video_path.is_file():
            logger.warning(f"视频文件不存在: {video_file}")
            return False

        if not video_path.suffix.lower() == '.mkv':
            logger.warning(f"不是 MKV 文件: {video_file}")
            return False

        # mkvpropedit 的音轨编号从 1 开始
        track_number = track_index + 1

        # 构建命令
        cmd = [
            self.mkvpropedit_path,
            _safe_path_arg(video_path),
            '--edit', f'track:a{track_number}',
            '--set', f'language={language_code}'
        ]

        # 自动设置 IETF BCP-47 标签
        # 优先使用原始代码（ISO 639-1 或 BCP-47）以生成准确的 IETF 标签
        # 如果未提供原始代码，则尝试从 ISO 639-2 生成（向后兼容）
        code_for_ietf = original_code if original_code else language_code
        ietf_tag = convert_to_ietf_tag(code_for_ietf)
        if ietf_tag:
            cmd.extend(['--set', f'language-ietf={ietf_tag}'])

        # 如果提供了轨道名称，也一起设置
        if track_name:
            cmd.extend(['--set', f'name={track_name}'])

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=DEFAULT_TIMEOUT
            )
            logger.info(f"成功设置音轨语言: {video_file} track:{track_index} -> {language_code}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"设置音轨语言超时: {video_file}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvpropedit 执行失败: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error(f"mkvpropedit 未找到，请安装 mkvtoolnix")
            return False
        except Exception as e:
            logger.error(f"设置音轨语言时发生未知错误: {e}", exc_info=True)
            return False

    def set_subtitle_track_language(
        self,
        video_file: str,
        track_index: int,
        language_code: str,
        track_name: Optional[str] = None,
        original_code: Optional[str] = None
    ) -> bool:
        """
        设置字幕轨道的语言信息

        Args:
            video_file: MKV 视频文件路径
            track_index: 字幕轨道索引（从 0 开始）
            language_code: ISO 639-2 语言代码（如 'jpn', 'eng', 'chi'）
            track_name: 可选的字幕轨道名称（如 '日本語', 'English'）
            original_code: 可选的原始语言代码（ISO 639-1 或 BCP-47），用于生成准确的 IETF 标签

        Returns:
            True 如果成功

        Note:
            mkvpropedit 使用的字幕轨道编号从 1 开始，需要转换
        """
        # 验证轨道索引
        if track_index < 0:
            logger.warning(f"无效的字幕轨道索引: {track_index}")
            return False

        video_path = Path(video_file)

        if not video_path.is_file():
            logger.warning(f"视频文件不存在: {video_file}")
            return False

        if not video_path.suffix.lower() == '.mkv':
            logger.warning(f"不是 MKV 文件: {video_file}")
            return False

        # mkvpropedit 的字幕轨道编号从 1 开始
        track_number = track_index + 1

        # 构建命令
        cmd = [
            self.mkvpropedit_path,
            _safe_path_arg(video_path),
            '--edit', f'track:s{track_number}',
            '--set', f'language={language_code}'
        ]

        # 自动设置 IETF BCP-47 标签
        # 优先使用原始代码（ISO 639-1 或 BCP-47）以生成准确的 IETF 标签
        # 如果未提供原始代码，则尝试从 ISO 639-2 生成（向后兼容）
        code_for_ietf = original_code if original_code else language_code
        ietf_tag = convert_to_ietf_tag(code_for_ietf)
        if ietf_tag:
            cmd.extend(['--set', f'language-ietf={ietf_tag}'])

        # 如果提供了轨道名称，也一起设置
        if track_name:
            cmd.extend(['--set', f'name={track_name}'])

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=DEFAULT_TIMEOUT
            )
            logger.info(f"成功设置字幕语言: {video_file} track:{track_index} -> {language_code}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"设置字幕语言超时: {video_file}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvpropedit 执行失败: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error(f"mkvpropedit 未找到，请安装 mkvtoolnix")
            return False
        except Exception as e:
            logger.error(f"设置字幕语言时发生未知错误: {e}", exc_info=True)
            return False

    def set_subtitle_track_name_only(
        self,
        video_file: str,
        track_index: int,
        track_name: str
    ) -> bool:
        """
        仅设置字幕轨道的名称（保留原有语言代码）

        Args:
            video_file: MKV 视频文件路径
            track_index: 字幕轨道索引（从 0 开始）
            track_name: 字幕轨道名称（如 '日本語', 'English'）

        Returns:
            True 如果成功

        Note:
            此方法只设置 track name，不修改 language 或 language-ietf
            用于补充缺失的轨道名称而不影响已正确的语言标签
        """
        # 验证轨道索引
        if track_index < 0:
            logger.warning(f"无效的字幕轨道索引: {track_index}")
            return False

        video_path = Path(video_file)

        if not video_path.is_file():
            logger.warning(f"视频文件不存在: {video_file}")
            return False

        if not video_path.suffix.lower() == '.mkv':
            logger.warning(f"不是 MKV 文件: {video_file}")
            return False

        # mkvpropedit 的字幕轨道编号从 1 开始
        track_number = track_index + 1

        # 构建命令（只设置名称）
        cmd = [
            self.mkvpropedit_path,
            _safe_path_arg(video_path),
            '--edit', f'track:s{track_number}',
            '--set', f'name={track_name}'
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=DEFAULT_TIMEOUT
            )
            logger.info(f"成功设置字幕名称: {video_file} track:{track_index} -> {track_name}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"设置字幕名称超时: {video_file}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvpropedit 执行失败: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error(f"mkvpropedit 未找到，请安装 mkvtoolnix")
            return False
        except Exception as e:
            logger.error(f"设置字幕名称时发生未知错误: {e}", exc_info=True)
            return False

    def get_audio_tracks_info(self, video_file: str) -> List[Dict[str, Any]]:
        """
        获取视频文件的音轨信息

        Args:
            video_file: 视频文件路径

        Returns:
            音轨信息列表，每个字典包含:
            - track_id: 轨道 ID
            - codec: 编码格式
            - language: 语言代码 (可能为 'und')
            - track_name: 轨道名称 (可能为空)

        Note:
            使用 mkvmerge -J 获取 JSON 格式信息
        """
        try:
            cmd = [
                'mkvmerge',
                '-J',
                _safe_path_arg(video_file)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=DEFAULT_TIMEOUT
            )

            # 解析 JSON
            data = json.loads(result.stdout)
            tracks = []

            for track in data.get('tracks', []):
                if track.get('type') == 'audio':
                    properties = track.get('properties') or {}
                    tracks.append({
                        'track_id': track.get('id'),
                        'codec': track.get('codec', ''),
                        'language': properties.get('language', UNDEFINED_LANGUAGE),
                        'track_name': properties.get('track_name', '')
                    })

            return tracks

        except json.JSONDecodeError as e:
            logger.error(f"解析 mkvmerge JSON 输出失败: {video_file}, {e}")
            return []
        except subprocess.TimeoutExpired:
            logger.error(f"获取音轨信息超时: {video_file}")
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvmerge 执行失败: {e.stderr}")
            return []
        except FileNotFoundError:
            logger.error("mkvmerge 未找到，请安装 mkvtoolnix")
            return []
        except Exception as e:
            logger.error(f"获取音轨信息时发生未知错误: {e}", exc_info=True)
            return []

    def get_subtitle_tracks_info(self, video_file: str) -> List[Dict[str, Any]]:
        """
        获取视频文件的字幕轨道信息

        Args:
            video_file: 视频文件路径

        Returns:
            字幕轨道信息列表，每个字典包含:
            - track_id: 轨道 ID
            - codec: 编码格式
            - language: 语言代码 (可能为 'und')
            - track_name: 轨道名称 (可能为空)

        Note:
            使用 mkvmerge -J 获取 JSON 格式信息
        """
        try:
            cmd = [
                'mkvmerge',
                '-J',
                _safe_path_arg(video_file)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=DEFAULT_TIMEOUT
            )

            # 解析 JSON
            data = json.loads(result.stdout)
            tracks = []

            for track in data.get('tracks', []):
                if track.get('type') != 'subtitles':
                    continue

                properties = track.get('properties') or {}
                track_info = {
                    'track_id': track.get('id'),
                    'codec': track.get('codec', ''),
                    'language': properties.get('language', UNDEFINED_LANGUAGE),
                    'track_name': properties.get('track_name', '')
                }
                tracks.append(track_info)

            logger.debug(f"找到 {len(tracks)} 个字幕轨道: {video_file}")
            return tracks

        except json.JSONDecodeError as e:
            logger.error(f"解析 mkvmerge JSON 输出失败: {video_file}, {e}")
            return []
        except subprocess.TimeoutExpired:
            logger.error(f"获取字幕轨道信息超时: {video_file}")
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvmerge 执行失败: {e.stderr}")
            return []
        except FileNotFoundError:
            logger.error("mkvmerge 未找到，请安装 mkvtoolnix")
            return []
        except Exception as e:
            logger.error(f"获取字幕轨道信息时发生未知错误: {e}", exc_info=True)
            return []

    @staticmethod
    def _get_subtitle_suffix(codec: Optional[str]) -> str:
        """
        根据字幕编解码器格式返回合适的文件扩展名

        Args:
            codec: 字幕编解码器格式（例如 'SubRip/SRT', 'SubStationAlpha', 'S_TEXT/WEBVTT'）

        Returns:
            文件扩展名（带点号，例如 '.srt', '.ass', '.vtt'）

        Note:
            默认返回 '.srt' 以保持向后兼容性
        """
        if not codec:
            return '.srt'

        codec_lower = codec.lower()

        # ASS/SSA 格式
        # 移除空格后再检查，以支持 "SubStation Alpha" 等变体
        codec_normalized = codec_lower.replace(' ', '')
        if 'ass' in codec_normalized or 'substationalpha' in codec_normalized or 'ssa' in codec_normalized:
            return '.ass'

        # WebVTT 格式
        if 'webvtt' in codec_lower or 'vtt' in codec_lower:
            return '.vtt'

        # SRT 格式（默认）
        return '.srt'

    def extract_subtitle_content(
        self,
        video_file: str,
        track_id: int,
        output_file: Optional[str] = None,
        codec: Optional[str] = None
    ) -> Optional[str]:
        """
        提取字幕内容用于语言检测

        Args:
            video_file: 视频文件路径
            track_id: 字幕轨道 ID
            output_file: 可选的输出文件路径，如果不提供则使用临时文件
            codec: 字幕编解码器格式（用于确定文件扩展名）

        Returns:
            字幕文件路径，失败返回 None

        Note:
            使用 mkvextract 提取字幕
        """
        # 检查 mkvextract 是否可用
        if not shutil.which('mkvextract'):
            logger.error(
                "mkvextract 未找到，请安装 mkvtoolnix。\\n"
                "macOS: brew install mkvtoolnix\\n"
                "Linux: apt install mkvtoolnix"
            )
            return None

        video_path = Path(video_file)
        if not video_path.is_file():
            logger.warning(f"视频文件不存在: {video_file}")
            return None

        # 创建临时文件（如果需要）
        temp_file_created = False
        temp_fd = None

        try:
            if output_file is None:
                # 根据 codec 决定文件扩展名
                suffix = self._get_subtitle_suffix(codec)
                temp_fd, output_file = tempfile.mkstemp(suffix=suffix)
                os.close(temp_fd)
                temp_fd = None
                temp_file_created = True
            else:
                # 验证用户提供的输出路径（防止路径遍历攻击）
                if not _validate_output_path(Path(output_file)):
                    logger.error(f"输出路径不在安全目录内，拒绝写入: {output_file}")
                    return None

                # 检查用户提供的输出文件是否已存在
                if os.path.exists(output_file):
                    logger.warning(f"输出文件已存在，拒绝覆盖: {output_file}")
                    return None

            cmd = [
                'mkvextract',
                'tracks',
                _safe_path_arg(video_path),
                f'{track_id}:{output_file}'
            ]

            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT
            )

            logger.debug(f"成功提取字幕: track_id={track_id} -> {output_file}")
            return output_file

        except subprocess.TimeoutExpired:
            logger.error(f"提取字幕超时: {video_file} track_id={track_id}")
            # 清理失败时创建的临时文件
            if temp_file_created and output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {output_file}, {e}")
            return None

        except subprocess.CalledProcessError as e:
            logger.error(f"mkvextract 执行失败: {e.stderr}")
            # 清理失败时创建的临时文件
            if temp_file_created and output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {output_file}, {e}")
            return None

        except FileNotFoundError:
            logger.error("mkvextract 未找到，请安装 mkvtoolnix")
            # 清理失败时创建的临时文件
            if temp_file_created and output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {output_file}, {e}")
            return None

        except Exception as e:
            logger.error(f"提取字幕时发生未知错误: {e}", exc_info=True)
            # 清理失败时创建的临时文件
            if temp_file_created and output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {output_file}, {cleanup_error}")
            return None

        finally:
            # 确保文件描述符被关闭
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except Exception:
                    pass

    def _should_process_subtitle_track(self, track: Dict[str, Any]) -> bool:
        """
        判断该字幕轨道是否是可处理的文本字幕

        Args:
            track: 字幕轨道信息

        Returns:
            True 如果是文本字幕（可以检测语言）
        """
        codec = track.get('codec')
        if not codec:
            logger.debug("字幕轨道缺少 codec 信息，跳过处理")
            return False

        codec_lower = codec.lower()

        # 检查是否是文本字幕（可以检测语言）
        text_subtitle_codecs = [
            'subrip/srt', 'srt', 'subrip',
            'substationalpha', 'ssa', 'ass',
            'utf-8', 'ascii',
            's_text/utf8', 's_text/ass', 's_text/ssa',  # mkvmerge 标准编解码器
            's_text/webvtt'  # WebVTT 格式（已支持）
            # 注意：不支持 S_TEXT/USF（XML 格式，较少见）
        ]

        is_text_subtitle = any(codec_name in codec_lower for codec_name in text_subtitle_codecs)

        if not is_text_subtitle:
            logger.debug(f"跳过图形字幕: {codec}")
            return False

        return True

    def _detect_track_language(
        self,
        video_file: str,
        track: Dict[str, Any],
        language_detector: 'LanguageDetector'
    ) -> Optional[Dict[str, Any]]:
        """
        检测单个字幕轨道的语言

        Args:
            video_file: 视频文件路径
            track: 字幕轨道信息
            language_detector: 语言检测器实例

        Returns:
            检测结果字典，包含 detected_code, language_code, track_name, confidence
            失败返回 None
        """
        track_id = track['track_id']
        codec = track.get('codec')

        # 提取字幕内容（传递 codec 以确定正确的文件扩展名）
        temp_file = self.extract_subtitle_content(video_file, track_id, codec=codec)
        if not temp_file:
            return None

        try:
            # 检测语言
            result = language_detector.detect_subtitle_language(temp_file)
            if not result:
                return None

            detected_lang, confidence = result

            # 转换为 ISO 639-2 格式
            iso639_2_code = convert_to_iso639_2(detected_lang)
            native_name = get_language_name(detected_lang)

            return {
                'detected_code': detected_lang,
                'language_code': iso639_2_code,
                'track_name': native_name,
                'confidence': confidence
            }

        except Exception as e:
            logger.warning(f"检测字幕语言失败: track_id={track_id}, {e}")
            return None

        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {temp_file}, {e}")

    def detect_and_set_embedded_subtitle_languages(
        self,
        video_file: str,
        language_detector: Optional['LanguageDetector'] = None,
        dry_run: bool = False
    ) -> Dict[int, Dict[str, Any]]:
        """
        检测并设置嵌入字幕的语言信息

        Args:
            video_file: 视频文件路径
            language_detector: 可选的语言检测器实例
            dry_run: 是否仅检测不实际设置

        Returns:
            字典，键为轨道索引（从0开始），值包含 language_code 和 track_name

        Note:
            智能处理逻辑：
            - 如果语言正确但缺名称：直接用原语言代码生成名称（不检测）
            - 如果语言缺失但有名称：只设置语言，保留原名称
            - 如果语言和名称都缺失：同时设置语言和名称
            - 自动跳过图形字幕（PGS, VobSub 等）
        """
        video_path = Path(video_file)
        if not video_path.is_file():
            logger.warning(f"视频文件不存在: {video_file}")
            return {}

        if not video_path.suffix.lower() == '.mkv':
            logger.warning(f"不是 MKV 文件: {video_file}")
            return {}

        # 获取字幕轨道信息
        subtitle_tracks = self.get_subtitle_tracks_info(str(video_path))
        if not subtitle_tracks:
            logger.debug(f"未找到字幕轨道: {video_file}")
            return {}

        # 如果没有提供语言检测器，尝试导入
        if language_detector is None:
            try:
                from .language_detector import LanguageDetector
                language_detector = LanguageDetector()
            except ImportError:
                logger.error("无法导入 LanguageDetector，请安装 langdetect")
                return {}
            except Exception as e:
                logger.error(f"初始化语言检测器失败: {e}")
                return {}

        # 创建 track_id 到索引的映射（修复索引转换逻辑）
        track_id_to_index = {
            track['track_id']: idx
            for idx, track in enumerate(subtitle_tracks)
        }

        results = {}

        for track in subtitle_tracks:
            original_language = track['language']
            original_track_name = track['track_name']

            # 规范化空值：将 None 或空字符串统一处理为 'und'（未确定）
            if not original_language:
                original_language = UNDEFINED_LANGUAGE
                logger.debug(f"字幕轨道 {track['track_id']} 的语言字段为空，规范化为 '{UNDEFINED_LANGUAGE}'")

            # 检查是否是可处理的文本字幕
            if not self._should_process_subtitle_track(track):
                continue

            # 判断需要处理的内容
            needs_language = (original_language == UNDEFINED_LANGUAGE)
            needs_track_name = (not original_track_name)

            # 如果语言和名称都已存在，跳过
            if not needs_language and not needs_track_name:
                logger.debug(f"跳过已完整标记的字幕: track_id={track['track_id']}, language={original_language}, name={original_track_name}")
                continue

            # 获取正确的字幕索引
            track_id = track['track_id']
            subtitle_index = track_id_to_index[track_id]

            # === 场景 1: 语言正确，只缺名称 ===
            if not needs_language and needs_track_name:
                # 先尝试直接获取 BCP-47 名称（保留脚本/区域特殊性，如 zh-hans → "简体中文"）
                track_name = get_language_name(original_language)
                # 如果返回的是大写代码（说明没找到映射），转换为 ISO 639-2 再试
                if track_name == original_language.upper():
                    iso639_2_code = convert_to_iso639_2(original_language)
                    track_name = get_language_name(iso639_2_code)

                results[subtitle_index] = {
                    'detected_code': original_language,
                    'language_code': convert_to_iso639_2(original_language),
                    'track_name': track_name,
                    'confidence': 1.0  # 使用原语言，置信度100%
                }

                # 如果不是干运行，设置名称
                if not dry_run:
                    success = self.set_subtitle_track_name_only(
                        str(video_path),
                        subtitle_index,
                        track_name
                    )
                    if success:
                        logger.info(
                            f"已补充字幕名称（保留原语言）: {video_file} track:{subtitle_index} "
                            f"language={original_language}(保留), name={track_name}"
                        )
                    else:
                        logger.warning(
                            f"设置字幕名称失败: {video_file} track:{subtitle_index}"
                        )
                continue

            # === 场景 2 和 3: 语言缺失（需要检测） ===
            # 检测语言（用于获取语言代码和/或轨道名称）
            detected_info = self._detect_track_language(
                str(video_path),
                track,
                language_detector
            )

            if not detected_info:
                continue

            # 跳过无效的语言检测结果（转换后仍为 'und'）
            if detected_info['language_code'] == UNDEFINED_LANGUAGE:
                logger.debug(f"跳过无效语言检测结果: track_id={track_id}, 转换后仍为 'und'")
                continue

            results[subtitle_index] = detected_info

            # 如果不是干运行，设置语言/名称
            if not dry_run:
                # 决定要设置的 track_name
                if needs_track_name:
                    # 场景 3: 语言和名称都缺失，使用检测到的名称
                    new_track_name = detected_info['track_name']
                else:
                    # 场景 2: 语言缺失但有名称，保留原名称
                    new_track_name = original_track_name

                # 同时设置语言和名称
                success = self.set_subtitle_track_language(
                    str(video_path),
                    subtitle_index,
                    detected_info['language_code'],
                    new_track_name,
                    original_code=detected_info['detected_code']
                )
                if success:
                    logger.info(
                        f"已设置字幕语言: {video_file} track:{subtitle_index} "
                        f"{original_language}->{detected_info['language_code']}, "
                        f"name={new_track_name}"
                        f"{' (保留原名称)' if not needs_track_name else ''}"
                    )
                else:
                    logger.warning(
                        f"设置字幕语言失败: {video_file} track:{subtitle_index}"
                    )

        return results


    def convert_to_mkv_with_language(
        self,
        video_file: str,
        output_file: str,
        audio_track_index: int,
        language_code: str,
        track_name: Optional[str] = None
    ) -> bool:
        """
        将非 MKV 视频转换为 MKV 并设置音轨语言

        Args:
            video_file: 源视频文件路径
            output_file: 输出 MKV 文件路径
            audio_track_index: 音轨索引（从 0 开始，对于典型视频文件：0=第一个音轨）
            language_code: ISO 639-2 语言代码
            track_name: 可选的音轨名称

        Returns:
            True 如果成功

        Note:
            使用 mkvmerge 转换并设置语言信息
            对于典型的视频文件结构：
            - Track 0: video
            - Track 1: audio (第一个音轨)
            - Track 2: audio (第二个音轨，如果有)
        """
        video_path = Path(video_file)
        output_path = Path(output_file)

        if not video_path.is_file():
            logger.warning(f"源视频文件不存在: {video_file}")
            return False

        # 检查输出文件是否与输入文件相同（避免覆盖输入）
        if output_path.resolve() == video_path.resolve():
            logger.error(
                f"输出文件与输入文件相同，拒绝覆盖: {output_file}"
            )
            return False

        # 检查输出文件是否已存在（避免覆盖现有文件）
        if output_path.exists():
            logger.warning(
                f"输出文件已存在，拒绝覆盖: {output_file}"
            )
            return False

        # 确保输出目录存在
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"创建输出目录失败: {output_path.parent}, {e}")
            return False

        # 使用 mkvmerge 的音轨选择器 'a{N}' 来指定第 N 个音频轨道
        # 这比假设绝对轨道编号更可靠
        # audio_track_index=0 表示第一个音轨 (a0)，1 表示第二个音轨 (a1)
        audio_selector = f'a{audio_track_index}'

        # 构建 mkvmerge 命令
        cmd = [
            'mkvmerge',
            '-o', _safe_path_arg(output_path),
            '--language', f'{audio_selector}:{language_code}'
        ]

        # 如果提供了轨道名称，也一起设置
        if track_name:
            cmd.extend(['--track-name', f'{audio_selector}:{track_name}'])

        # 添加源文件
        cmd.append(_safe_path_arg(video_path))

        # 检查输出文件是否预存在（用于决定失败时是否删除）
        output_preexisted = output_path.exists()

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=SUBPROCESS_TIMEOUT
            )
            logger.info(f"成功转换视频为 MKV: {video_file} -> {output_file}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"转换视频超时: {video_file}")
            if not output_preexisted:
                self._cleanup_failed_output(str(output_path))
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvmerge 转换失败: {e.stderr}")
            if not output_preexisted:
                self._cleanup_failed_output(str(output_path))
            return False
        except FileNotFoundError:
            logger.error("mkvmerge 未找到，请安装 mkvtoolnix")
            if not output_preexisted:
                self._cleanup_failed_output(str(output_path))
            return False
        except Exception as e:
            logger.error(f"转换视频时发生未知错误: {e}", exc_info=True)
            if not output_preexisted:
                self._cleanup_failed_output(str(output_path))
            return False


def convert_to_iso639_2(language_code: str) -> str:
    """
    将语言代码转换为 ISO 639-2 格式（mkvpropedit 要求）

    Args:
        language_code: 输入语言代码（可能是 ISO 639-1、扩展代码或其他格式）
                      支持: zh, en, zh-hans, zh-hant, en-us, fil-ph 等

    Returns:
        优先返回 ISO 639-2 语言代码（3 字母），
        对于无法映射的三字母代码直接传递（可能是 ISO 639-3）

    Note:
        - Whisper 返回的是 ISO 639-1 (2字母)
        - LanguageDetector 返回的可能是扩展代码（如 zh-hans, zh-hant）
        - 优先转换为 ISO 639-2 (3字母)
        - ISO 639-3 方言代码（如 yue）会映射到 ISO 639-2（如 chi）
        - 其他三字母代码（如 fil, ast）直接传递
    """
    # ISO 639-1 到 ISO 639-2 的映射（常用语言）
    iso639_1_to_2 = {
        # 中文
        'zh': 'chi',  # Chinese（实际 ISO 639-2 使用 zho，但 MKV 工具常用 chi）
        # 英语
        'en': 'eng',
        # 日语
        'ja': 'jpn',
        # 韩语
        'ko': 'kor',
        # 法语
        'fr': 'fre',
        # 德语
        'de': 'ger',
        # 西班牙语
        'es': 'spa',
        # 俄语
        'ru': 'rus',
        # 意大利语
        'it': 'ita',
        # 葡萄牙语
        'pt': 'por',
        # 阿拉伯语
        'ar': 'ara',
        # 印地语
        'hi': 'hin',
        # 泰语
        'th': 'tha',
        # 越南语
        'vi': 'vie',
        # 土耳其语
        'tr': 'tur',
        # 波兰语
        'pl': 'pol',
        # 荷兰语
        'nl': 'dut',
        # 瑞典语
        'sv': 'swe',
        # 挪威语
        'no': 'nor',
        # 丹麦语
        'da': 'dan',
        # 芬兰语
        'fi': 'fin',
        # 希腊语
        'el': 'gre',
        # 捷克语
        'cs': 'cze',
        # 匈牙利语
        'hu': 'hun',
        # 罗马尼亚语
        'ro': 'rum',
        # 乌克兰语
        'uk': 'ukr',
        # 印尼语
        'id': 'ind',
        # 马来语
        'ms': 'may',
        # 波斯语
        'fa': 'per',
        # 希伯来语
        'he': 'heb',
        # 他加禄语
        'tl': 'tgl',
    }

    # ISO 639-3 特殊语言映射（主要是中文方言）
    iso639_3_mapping = {
        'yue': 'chi',  # 粤语 (Cantonese) -> Chinese
        'wuu': 'chi',  # 吴语 (Wu Chinese) -> Chinese
        'nan': 'chi',  # 闽南语 (Min Nan Chinese) -> Chinese
    }

    # 转为小写统一处理
    lang_code_lower = language_code.lower()

    # 如果包含连字符或下划线（扩展语言代码，如 zh-hans, zh-hant, en-us, fil-ph）
    # 提取基础语言代码（连字符/下划线前的部分）
    if '-' in lang_code_lower or '_' in lang_code_lower:
        # 分割并取第一部分
        base_code = lang_code_lower.replace('_', '-').split('-')[0]

        # 如果是三字母代码
        if len(base_code) == 3:
            # 优先检查 ISO 639-3 到 ISO 639-2 的映射（如 yue → chi）
            if base_code in iso639_3_mapping:
                return iso639_3_mapping[base_code]
            # 其他情况直接传递三字母代码（保持一致性）
            # 包括：在 LANGUAGE_NAMES 中的代码（如 fil）和其他有效的 ISO 639-2/3 代码
            return base_code

        # 如果是两字母代码，使用映射转换
        return iso639_1_to_2.get(base_code, 'und')

    # 如果是 2 字母代码，转换为 3 字母
    if len(lang_code_lower) == 2:
        return iso639_1_to_2.get(lang_code_lower, 'und')

    # 如果是 3 字母代码，检查特殊映射
    if len(lang_code_lower) == 3:
        return iso639_3_mapping.get(lang_code_lower, lang_code_lower)

    # 未知格式，返回 und (undefined)
    return 'und'


def get_language_name(language_code: str) -> str:
    """
    获取语言的原生名称（导入自 language_utils 模块）

    Args:
        language_code: 语言代码（支持基础代码和扩展代码，如 zh, en, zh-hans, en-us）

    Returns:
        语言的原生名称（使用该语言的文字）
    """
    return language_utils.get_language_name(language_code)
