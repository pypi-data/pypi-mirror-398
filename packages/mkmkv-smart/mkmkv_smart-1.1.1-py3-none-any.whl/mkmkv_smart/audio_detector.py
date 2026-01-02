"""
音频语言检测模块

使用 faster-whisper 自动识别音轨的语言
"""

import subprocess
import tempfile
import os
import shutil
import logging
from typing import Optional, Tuple, List, Union, TYPE_CHECKING
from pathlib import Path

from .security_utils import _safe_path_arg

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class AudioLanguageDetector:
    """音频语言检测器"""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        min_confidence: float = 0.7
    ):
        """
        初始化音频语言检测器

        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
                - tiny: 39MB, 快速但准确率较低
                - base: 142MB, 平衡速度和准确率
                - small: 466MB, 高精度（推荐）
                - medium: 1.5GB, 更高精度
                - large: 2.9GB, 最高精度
            device: 设备类型 (cpu, cuda)
            compute_type: 计算类型 (int8, float16, float32)
                - int8: 最快，内存占用最少（推荐 CPU）
                - float16: GPU 推荐
                - float32: 最高精度
            min_confidence: 最小置信度阈值 (0.0-1.0)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.min_confidence = min_confidence
        self._model: Optional["WhisperModel"] = None

    def _load_model(self) -> None:
        """延迟加载模型（首次使用时）"""
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "faster-whisper 未安装。请运行: pip install mkmkv-smart[audio]"
            )

        try:
            # 加载模型（首次会自动下载）
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        except ImportError as e:
            # 捕获 SOCKS 代理相关错误
            if "socksio" in str(e):
                raise ImportError(
                    "检测到 SOCKS 代理但缺少依赖。请运行: pip install httpx[socks]"
                ) from e
            raise
        except Exception as e:
            # 其他下载/加载错误
            error_msg = str(e)
            if "Failed to reach" in error_msg or "ConnectError" in error_msg:
                raise RuntimeError(
                    f"无法下载模型（网络问题）: {e}\n"
                    "请检查网络连接或代理设置"
                ) from e
            raise

    def extract_audio_track(
        self,
        video_file: str,
        track_index: int = 0,
        duration: int = 30,
        start_time: int = 0
    ) -> Optional[str]:
        """
        从视频文件提取音轨

        Args:
            video_file: 视频文件路径
            track_index: 音轨索引（0 为第一个音轨）
            duration: 提取音频长度（秒），默认 30 秒
            start_time: 开始时间（秒），默认从 0 开始

        Returns:
            临时音频文件路径，失败返回 None
        """
        video_path = Path(video_file)

        # 先检查文件存在性
        if not video_path.is_file():
            return None

        # 再检查 ffmpeg 是否可用
        if not shutil.which('ffmpeg'):
            raise RuntimeError(
                "ffmpeg 未找到，请安装 ffmpeg。\\n"
                "macOS: brew install ffmpeg\\n"
                "Linux: apt install ffmpeg 或 yum install ffmpeg"
            )

        # 创建临时音频文件
        temp_audio = tempfile.NamedTemporaryFile(
            suffix='.wav',
            delete=False
        )
        temp_audio.close()

        try:
            # 使用 ffmpeg 提取音轨
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),  # 从指定时间开始
                '-i', _safe_path_arg(video_path),
                '-t', str(duration),  # 只取 N 秒
                '-map', f'0:a:{track_index}',  # 选择指定音轨
                '-ac', '1',  # 转为单声道
                '-ar', '16000',  # 采样率 16kHz (Whisper 推荐)
                '-y',  # 覆盖输出文件
                temp_audio.name
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=300  # 5 分钟超时（处理大文件）
            )

            return temp_audio.name

        except subprocess.TimeoutExpired as e:
            # 超时错误
            logger.error(
                f"ffmpeg 提取音轨超时: {video_file}, 音轨索引={track_index}, "
                f"超时时间=300秒"
            )
            if os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)
            return None
        except subprocess.CalledProcessError as e:
            # ffmpeg 失败，删除临时文件
            stderr_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            logger.error(
                f"ffmpeg 提取音轨失败: {video_file}, 音轨索引={track_index}, "
                f"错误: {stderr_output}"
            )
            if os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)

            # 检查是否是流不存在的错误
            if any(pattern in stderr_output.lower() for pattern in [
                'matches no streams',
                'invalid stream specifier',
                'stream #0:a:',
                'does not contain any stream'
            ]):
                # 抛出特定异常表示流不存在
                raise ValueError(f"音轨 {track_index} 不存在") from e

            return None
        except Exception as e:
            logger.error(f"提取音轨时发生意外错误: {video_file}, 错误: {e}", exc_info=True)
            if os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)
            return None

    def detect_audio_language(
        self,
        audio_file: str
    ) -> Optional[Tuple[str, float]]:
        """
        检测音频文件的语言

        Args:
            audio_file: 音频文件路径

        Returns:
            (语言代码, 置信度) 或 None
            语言代码格式: zh, en, ja, ko 等
        """
        audio_path = Path(audio_file)

        if not audio_path.is_file():
            return None

        try:
            # 加载模型
            self._load_model()

            # 检测语言（不进行完整转录，只检测语言）
            # beam_size=5 提高准确率
            segments, info = self._model.transcribe(
                str(audio_path),
                beam_size=5,
                language=None  # 自动检测
            )

            detected_language = info.language
            confidence = info.language_probability

            # 检查置信度
            if confidence < self.min_confidence:
                return None

            return (detected_language, confidence)

        except Exception as e:
            logger.error(f"检测音频语言失败: {audio_file}, 错误: {e}", exc_info=True)
            return None

    def detect_video_audio_language(
        self,
        video_file: str,
        track_index: int = 0,
        duration: int = 30,
        smart_sampling: bool = True,
        max_attempts: int = 3
    ) -> Optional[Tuple[str, float]]:
        """
        检测视频音轨的语言

        Args:
            video_file: 视频文件路径
            track_index: 音轨索引（0 为第一个音轨）
            duration: 每次采样的音频长度（秒），默认 30 秒
            smart_sampling: 是否启用智能多点采样（默认 True）
            max_attempts: 最大尝试次数（smart_sampling=False 时有效）

        Returns:
            (语言代码, 置信度) 或 None

        智能采样策略:
            - 如果 smart_sampling=True: 在多个位置采样（开头、1/4、1/2、3/4），取最佳结果
            - 如果 smart_sampling=False: 从开头开始，失败后向后移动重试
        """
        if smart_sampling:
            return self._detect_with_smart_sampling(video_file, track_index, duration)
        else:
            return self._detect_with_retry(video_file, track_index, duration, max_attempts)

    def _get_video_duration(self, video_file: str) -> Optional[float]:
        """
        获取视频总时长（秒）

        Args:
            video_file: 视频文件路径

        Returns:
            时长（秒）或 None
        """
        # 检查 ffprobe 是否可用
        if not shutil.which('ffprobe'):
            raise RuntimeError(
                "ffprobe 未找到，请安装 ffmpeg。\\n"
                "macOS: brew install ffmpeg\\n"
                "Linux: apt install ffmpeg 或 yum install ffmpeg"
            )

        try:
            import json

            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                _safe_path_arg(video_file)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                timeout=30  # 30 秒超时（元数据查询通常很快）
            )

            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration

        except subprocess.TimeoutExpired as e:
            # 超时错误
            logger.error(
                f"ffprobe 获取视频时长超时: {video_file}, 超时时间=30秒"
            )
            return None
        except subprocess.CalledProcessError as e:
            logger.error(
                f"ffprobe 获取视频时长失败: {video_file}, "
                f"错误: {e.stderr if e.stderr else str(e)}"
            )
            return None
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"解析 ffprobe 输出失败: {video_file}, 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取视频时长时发生意外错误: {video_file}, 错误: {e}", exc_info=True)
            return None

    def _detect_with_smart_sampling(
        self,
        video_file: str,
        track_index: int = 0,
        sample_duration: int = 30
    ) -> Optional[Tuple[str, float]]:
        """
        智能多点采样检测

        在视频的多个位置采样，选择置信度最高的结果。
        跳过视频首尾各 5% 以避开片头片尾曲。

        Args:
            video_file: 视频文件路径
            track_index: 音轨索引
            sample_duration: 每个采样点的时长

        Returns:
            (语言代码, 置信度) 或 None
        """
        # 获取视频总时长
        total_duration = self._get_video_duration(video_file)

        if total_duration is None or total_duration < sample_duration:
            # 无法获取时长，回退到简单模式
            return self._detect_with_retry(video_file, track_index, sample_duration, 1)

        # 跳过首尾各 5% 以避开片头片尾曲
        start_margin = total_duration * 0.05
        end_margin = total_duration * 0.95

        # 确保不会采样超出视频范围
        max_start = end_margin - sample_duration
        if max_start < start_margin:
            # 视频太短，只采样中间位置
            sample_positions = [total_duration / 2]
        else:
            # 计算有效采样范围
            effective_duration = max_start - start_margin

            if effective_duration < sample_duration:
                # 有效范围很短，只采样一个位置（中间）
                sample_positions = [start_margin + effective_duration / 2]
            elif effective_duration < sample_duration * 2:
                # 有效范围较短，采样 2 个点
                sample_positions = [
                    start_margin,
                    start_margin + effective_duration / 2
                ]
            else:
                # 正常情况，采样 4 个点：均匀分布在有效范围内
                sample_positions = [
                    start_margin,
                    start_margin + effective_duration / 3,
                    start_margin + effective_duration * 2 / 3,
                    max_start
                ]

        results = []

        for position in sample_positions:
            try:
                # 提取该位置的音频
                audio_file = self.extract_audio_track(
                    video_file,
                    track_index,
                    sample_duration,
                    start_time=int(position)
                )
            except ValueError:
                # 音轨不存在，直接传播异常
                raise

            if audio_file is None:
                continue

            try:
                # 检测语言
                result = self.detect_audio_language(audio_file)

                if result:
                    lang_code, confidence = result
                    results.append({
                        'language': lang_code,
                        'confidence': confidence,
                        'position': int(position)
                    })

            finally:
                # 清理临时文件
                if audio_file and os.path.exists(audio_file):
                    os.unlink(audio_file)

        # 如果没有任何结果
        if not results:
            return None

        # 选择置信度最高的结果
        best_result = max(results, key=lambda x: x['confidence'])

        return (best_result['language'], best_result['confidence'])

    def _detect_with_retry(
        self,
        video_file: str,
        track_index: int = 0,
        duration: int = 30,
        max_attempts: int = 3
    ) -> Optional[Tuple[str, float]]:
        """
        增量重试检测

        从开头开始，如果失败则向后移动继续尝试。

        Args:
            video_file: 视频文件路径
            track_index: 音轨索引
            duration: 采样时长
            max_attempts: 最大尝试次数

        Returns:
            (语言代码, 置信度) 或 None
        """
        for attempt in range(max_attempts):
            start_time = attempt * duration

            try:
                # 提取音轨
                audio_file = self.extract_audio_track(
                    video_file,
                    track_index,
                    duration,
                    start_time=start_time
                )
            except ValueError:
                # 音轨不存在，直接传播异常
                raise

            if audio_file is None:
                continue

            try:
                # 检测语言
                result = self.detect_audio_language(audio_file)

                if result:
                    return result

            finally:
                # 清理临时文件
                if audio_file and os.path.exists(audio_file):
                    os.unlink(audio_file)

        return None

    def detect_all_audio_tracks(
        self,
        video_file: str,
        max_tracks: int = 5
    ) -> List[Tuple[int, Optional[str], Optional[float]]]:
        """
        检测视频文件中所有音轨的语言

        Args:
            video_file: 视频文件路径
            max_tracks: 最多检测的音轨数量

        Returns:
            [(音轨索引, 语言代码, 置信度), ...]
            语言代码或置信度可能为 None（检测失败）
        """
        results = []

        for i in range(max_tracks):
            try:
                result = self.detect_video_audio_language(video_file, i)

                if result is None:
                    results.append((i, None, None))
                else:
                    lang_code, confidence = result
                    results.append((i, lang_code, confidence))
            except ValueError as e:
                # 音轨不存在，停止检测
                logger.info(f"音轨 {i} 不存在，停止检测: {e}")
                break

        return results


def detect_video_audio_language(
    video_file: str,
    track_index: int = 0,
    model_size: str = "small"
) -> Optional[Tuple[str, float]]:
    """
    便捷函数：检测视频音轨语言

    Args:
        video_file: 视频文件路径
        track_index: 音轨索引
        model_size: 模型大小

    Returns:
        (语言代码, 置信度) 或 None
    """
    detector = AudioLanguageDetector(model_size=model_size)
    return detector.detect_video_audio_language(video_file, track_index)
