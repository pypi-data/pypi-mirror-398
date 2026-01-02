"""
mkvmerge 封装模块

封装 mkvmerge 命令行工具，提供视频和字幕合并功能。
"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

from .security_utils import _safe_path_arg

# 配置日志
logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_TIMEOUT = 300  # 5分钟，合并可能需要较长时间


@dataclass
class SubtitleTrack:
    """字幕轨道"""
    file_path: str
    language_code: str
    track_name: str
    is_default: bool = False
    charset: str = "UTF-8"


class MKVMerger:
    """MKV 合并器"""

    def __init__(
        self,
        mkvmerge_path: str = "mkvmerge"
    ):
        """
        Args:
            mkvmerge_path: mkvmerge 可执行文件路径
        """
        self.mkvmerge_path = mkvmerge_path

        # 检查 mkvmerge 是否可用
        if not self.is_mkvmerge_available():
            raise RuntimeError(
                "mkvmerge not found. Please install mkvtoolnix.\n"
                "macOS: brew install mkvtoolnix\n"
                "Linux: apt install mkvtoolnix"
            )

    def is_mkvmerge_available(self) -> bool:
        """检查 mkvmerge 是否可用"""
        return shutil.which(self.mkvmerge_path) is not None

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

    def merge(
        self,
        video_file: str,
        subtitle_tracks: List[SubtitleTrack],
        output_file: str,
        dry_run: bool = False,
        keep_embedded_subtitles: bool = False,
        extra_args: Optional[List[str]] = None,
        track_order: Optional[str] = None
    ) -> bool:
        """
        合并视频和字幕

        Args:
            video_file: 视频文件路径
            subtitle_tracks: 字幕轨道列表
            output_file: 输出文件路径
            dry_run: 是否仅显示命令而不执行
            keep_embedded_subtitles: 是否保留嵌入字幕
            extra_args: 额外的 mkvmerge 参数
            track_order: 轨道顺序（例如：'0:0,0:1,0:2,1:0,2:0'）
                       格式：文件编号:轨道编号（以逗号分隔）
                       0 = 视频文件，1+ = 字幕文件
                       如果不指定，使用默认顺序

        Returns:
            是否成功

        Security:
            ⚠️ CRITICAL: extra_args 参数必须仅包含可信的、经过验证的参数。
            绝对不要将未经验证的用户输入传递给此参数，否则可能导致命令注入。
            此参数应仅用于内部配置或预定义的安全选项。

        Note:
            extra_args 会被自动验证，禁止包含输出参数 (-o/--output) 和其他
            潜在危险的参数。

            track_order 示例：
            - '0:0,0:1,1:0,2:0' - 视频轨0, 音轨1, 第1个字幕, 第2个字幕
            - 不指定时按照默认顺序（视频 -> 音频 -> 字幕）
        """
        # 验证文件存在性
        video_path = Path(video_file)
        if not video_path.is_file():
            logger.error(f"视频文件不存在: {video_file}")
            return False

        for track in subtitle_tracks:
            track_path = Path(track.file_path)
            if not track_path.is_file():
                logger.error(f"字幕文件不存在: {track.file_path}")
                return False

        # 验证输出目录和文件
        output_path = Path(output_file)

        # 检查输出文件是否与输入视频文件相同（避免覆盖输入）
        if not dry_run and output_path.resolve() == video_path.resolve():
            logger.error(
                f"输出文件与输入文件相同，拒绝覆盖: {output_file}"
            )
            return False

        if not dry_run:
            if output_path.parent.exists() and not output_path.parent.is_dir():
                logger.error(f"输出目录不是有效目录: {output_path.parent}")
                return False

            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"创建输出目录失败: {output_path.parent}, {e}")
                return False

        # 构建命令
        cmd = [
            self.mkvmerge_path,
            "-o", _safe_path_arg(output_file)
        ]

        # 根据是否保留嵌入字幕决定是否添加 -S 参数
        if not keep_embedded_subtitles:
            cmd.append("-S")  # 不复制原视频中的字幕

        cmd.extend([
            "--no-global-tags",  # 不包含全局标签
            _safe_path_arg(video_file)
        ])

        # 添加字幕轨道
        for track in subtitle_tracks:
            cmd.extend([
                "--sub-charset", f"0:{track.charset}",
                "--language", f"0:{track.language_code}",
                "--track-name", f"0:{track.track_name}",
                "--default-track-flag", f"0:{'yes' if track.is_default else 'no'}",
                _safe_path_arg(track.file_path)
            ])

        # 添加额外参数
        if extra_args:
            # 验证 extra_args 不包含危险参数（防止参数注入）
            dangerous_params = [
                '-o', '--output',  # 输出文件参数
                '--command-line-charset',  # 字符集相关（可能执行命令）
                '--ui-language',  # 可能加载外部文件
            ]

            for arg in extra_args:
                # 检查是否以危险参数开头
                for dangerous in dangerous_params:
                    if arg == dangerous or arg.startswith(f"{dangerous}="):
                        logger.error(
                            f"extra_args 包含禁止的参数: {arg}。"
                            f"禁止使用的参数: {', '.join(dangerous_params)}"
                        )
                        return False

            cmd.extend(extra_args)

        # 添加轨道顺序参数
        if track_order:
            # 验证格式：应该是 "0:0,0:1,1:0" 这样的格式
            import re
            if not re.match(r'^(\d+:\d+)(,\d+:\d+)*$', track_order):
                logger.error(
                    f"track_order 格式错误: {track_order}。"
                    f"正确格式示例: '0:0,0:1,1:0' (文件编号:轨道编号)"
                )
                return False
            cmd.extend(['--track-order', track_order])

        if dry_run:
            # 仅显示命令
            print("将执行以下命令:")
            print(" \\\n  ".join(cmd))
            return True

        # 检查输出文件是否预存在（用于决定失败时是否删除）
        output_preexisted = output_path.exists()

        # 执行命令
        try:
            logger.debug(f"执行 mkvmerge 命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT
            )
            logger.info(f"成功合并视频: {video_file} -> {output_file}")
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"mkvmerge 执行超时 ({DEFAULT_TIMEOUT}秒): {video_file}")
            if not output_preexisted:
                self._cleanup_failed_output(output_file)
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"mkvmerge 执行失败: {video_file}, stderr: {e.stderr}")
            if not output_preexisted:
                self._cleanup_failed_output(output_file)
            return False
        except FileNotFoundError:
            logger.error(f"mkvmerge 未找到，请安装 mkvtoolnix")
            if not output_preexisted:
                self._cleanup_failed_output(output_file)
            return False
        except Exception as e:
            logger.error(f"合并视频时发生未知错误: {video_file}, {e}", exc_info=True)
            if not output_preexisted:
                self._cleanup_failed_output(output_file)
            return False

    def batch_merge(
        self,
        tasks: List[Dict],
        dry_run: bool = False,
        keep_embedded_subtitles: bool = False,
        show_progress: bool = True
    ) -> Dict[str, bool]:
        """
        批量合并

        Args:
            tasks: 任务列表，每个任务包含:
                - video_file: 视频文件
                - subtitle_tracks: 字幕轨道列表
                - output_file: 输出文件
                - track_order: (可选) 轨道顺序，例如 '0:0,0:1,1:0'
            dry_run: 是否仅显示命令
            keep_embedded_subtitles: 是否保留嵌入字幕
            show_progress: 是否显示进度

        Returns:
            {视频文件: 是否成功} 字典
        """
        results = {}
        total = len(tasks)

        logger.info(f"开始批量合并，共 {total} 个任务")

        for i, task in enumerate(tasks, 1):
            video_file = None
            try:
                # 验证任务字典必需的键
                required_keys = ['video_file', 'subtitle_tracks', 'output_file']
                missing_keys = [key for key in required_keys if key not in task]

                if missing_keys:
                    logger.error(f"任务 {i} 缺少必需的键: {missing_keys}, 任务内容: {task}")
                    # 尝试获取 video_file 用于记录结果
                    video_key = task.get('video_file', f'task_{i}')
                    results[video_key] = False
                    if show_progress:
                        print(f"\n[{i}/{total}] ✗ 任务格式错误（缺少: {', '.join(missing_keys)}）")
                    continue

                video_file = task['video_file']

                if show_progress:
                    print(f"\n[{i}/{total}] 处理: {Path(video_file).name}")

                success = self.merge(
                    video_file=video_file,
                    subtitle_tracks=task['subtitle_tracks'],
                    output_file=task['output_file'],
                    dry_run=dry_run,
                    keep_embedded_subtitles=keep_embedded_subtitles,
                    track_order=task.get('track_order')  # 可选参数
                )

                results[video_file] = success

                if show_progress:
                    status = "✓ 成功" if success else "✗ 失败"
                    print(f"  {status}")

            except KeyError as e:
                logger.error(f"任务 {i} 字典键错误: {e}, 任务内容: {task}")
                if video_file:
                    results[video_file] = False
                if show_progress:
                    print(f"  ✗ 失败（字典键错误）")
            except Exception as e:
                logger.error(f"处理任务时发生异常: {task.get('video_file', f'task_{i}')}, {e}", exc_info=True)
                if video_file:
                    results[video_file] = False
                if show_progress:
                    print(f"  ✗ 失败（异常）")

        # 统计结果
        success_count = sum(1 for v in results.values() if v)
        failed_count = total - success_count
        logger.info(f"批量合并完成: 成功 {success_count}/{total}, 失败 {failed_count}")

        return results
