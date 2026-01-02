"""
命令行界面

提供用户友好的命令行交互。
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
import yaml
from rich.console import Console
from rich.table import Table

from .matcher import SmartMatcher, MatchResult, VALID_MATCH_METHODS
from .normalizer import FileNormalizer
from .merger import MKVMerger, SubtitleTrack
from .language_utils import get_language_name
from .audio_editor import convert_to_iso639_2
from .config import Config
from .language_detector import LanguageDetector
from . import __version__

logger = logging.getLogger(__name__)
console = Console()


def _get_language_priority(lang_code: str) -> int:
    """
    获取语言代码的优先级（数字越小优先级越高）

    Args:
        lang_code: 语言代码

    Returns:
        优先级数字：0=简体中文, 1=繁体中文, 2=英文, 999=其他

    Note:
        用于确保 MKV 文件中字幕轨道的顺序：
        1. 简体中文（zh-hans, zh-cn, zh, chs, chi, zho）
        2. 繁体中文（zh-hant, zh-tw, zh-hk, cht）
        3. 英文（en, en-us, en-gb, eng）
        4. 其他语言
    """
    lang_lower = lang_code.lower()

    # 简体中文变体
    simplified_chinese = [
        'zh-hans', 'zh-cn', 'zh-sg',  # 标准代码
        'zh', 'zho', 'chi',  # ISO 639-2/3
        'chs', 'sc', 'cn',  # 常见别名
    ]
    if lang_lower in simplified_chinese:
        return 0

    # 繁体中文变体
    traditional_chinese = [
        'zh-hant', 'zh-tw', 'zh-hk', 'zh-mo',  # 标准代码
        'cht', 'tc', 'tw', 'hk',  # 常见别名
    ]
    if lang_lower in traditional_chinese:
        return 1

    # 英文变体
    english = [
        'en', 'en-us', 'en-gb', 'en-au', 'en-ca',  # 标准代码
        'eng',  # ISO 639-2/3
    ]
    if lang_lower in english:
        return 2

    # 其他语言
    return 999


def sanitize_language_code(lang_code: str) -> str:
    """
    消毒语言代码，确保可以安全用于文件名

    Args:
        lang_code: 原始语言代码

    Returns:
        消毒后的语言代码，如果不符合规则则返回 'und'

    Note:
        只允许小写字母、数字和连字符
    """
    if not lang_code:
        return 'und'

    normalized = lang_code.lower()
    # 只允许小写字母、数字和连字符
    if re.match(r'^[a-z0-9-]+$', normalized):
        return normalized

    # 不符合规则，返回 'und'
    logger.warning(f"语言代码包含不安全字符，使用 'und' 替代: {lang_code}")
    return 'und'


def collect_files(directory: Path) -> tuple[List[Path], List[Path]]:
    """
    收集视频和字幕文件

    Args:
        directory: 目录路径

    Returns:
        (视频文件列表, 字幕文件列表)
    """
    normalizer = FileNormalizer()

    videos = []
    subtitles = []

    for file in directory.iterdir():
        if file.is_file():
            if normalizer.is_video_file(file.name):
                videos.append(file)
            elif normalizer.is_subtitle_file(file.name):
                subtitles.append(file)

    return sorted(videos), sorted(subtitles)


def display_matches(
    video: Path,
    lang_matches: Dict[str, MatchResult],
    normalizer: FileNormalizer
) -> None:
    """显示匹配结果"""
    console.print(f"\n[green]视频:[/green] {video.name}")
    console.print(f"  [dim]规范化: {normalizer.normalize(video.name)}[/dim]")

    if not lang_matches:
        console.print("  [yellow]⚠️  未找到匹配的字幕[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("语言", style="cyan")
    table.add_column("字幕文件", style="white")
    table.add_column("相似度", justify="right", style="yellow")

    for lang, match in lang_matches.items():
        table.add_row(
            lang,
            Path(match.subtitle_file).name,
            f"{match.similarity:.1f}%"
        )

    console.print(table)


def _setup_components(args: argparse.Namespace, config: Config) -> tuple[FileNormalizer, SmartMatcher]:
    """
    初始化文件规范化器和匹配器

    Args:
        args: 命令行参数
        config: 配置对象

    Returns:
        (规范化器, 匹配器)
    """
    # 覆盖命令行参数
    if args.threshold is not None:
        config.match.threshold = args.threshold
    if args.method:
        config.match.method = args.method

    # 创建文件名规范化器
    normalizer = FileNormalizer(
        keep_year=config.match.keep_year,
        keep_episode=config.match.keep_episode
    )

    # 创建匹配器
    matcher = SmartMatcher(
        threshold=config.match.threshold,
        method=config.match.method,
        normalizer=normalizer
    )

    return normalizer, matcher


def _validate_directories(source_dir: Path, output_dir: Optional[Path], dry_run: bool) -> Optional[int]:
    """
    验证源目录和输出目录

    Args:
        source_dir: 源目录
        output_dir: 输出目录（可选）
        dry_run: 是否为干运行模式

    Returns:
        错误代码（1 表示错误），None 表示成功
    """
    # 验证源目录
    if not source_dir.exists():
        console.print(f"[red]错误: 源目录不存在: {source_dir}[/red]")
        return 1
    if not source_dir.is_dir():
        console.print(f"[red]错误: 源路径不是目录: {source_dir}[/red]")
        return 1

    # 验证输出目录
    if output_dir:
        if output_dir.exists() and not output_dir.is_dir():
            console.print(f"[red]错误: 输出路径不是目录: {output_dir}[/red]")
            return 1
        if not output_dir.exists():
            if dry_run:
                console.print(f"[yellow]警告: 输出目录不存在，将在真实执行时创建: {output_dir}[/yellow]")
            else:
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    console.print(f"[green]已创建输出目录: {output_dir}[/green]")
                except OSError as e:
                    console.print(f"[red]错误: 无法创建输出目录: {output_dir} ({e})[/red]")
                    return 1

    return None


def _auto_detect_subtitle_languages(
    subtitles: List[Path],
    config: Config,
    normalizer: FileNormalizer,
    dry_run: bool
) -> int:
    """
    自动检测并重命名无语言代码的字幕文件

    Args:
        subtitles: 字幕文件列表（将被就地修改）
        config: 配置对象
        normalizer: 文件名规范化器
        dry_run: 是否为干运行模式

    Returns:
        检测并重命名的文件数量
    """
    if not subtitles or not config.language_detection.enabled:
        return 0

    detector = LanguageDetector(
        min_confidence=config.language_detection.min_confidence,
        min_chars=config.language_detection.min_chars
    )

    detected_count = 0

    # 创建路径到索引的映射以优化更新性能
    subtitle_index = {path: idx for idx, path in enumerate(subtitles)}

    for subtitle in list(subtitles):  # 使用 list() 复制列表
        idx = subtitle_index.get(subtitle)
        if idx is None:
            continue
        try:
            # 检查文件名是否已有语言代码
            lang_code = normalizer.extract_language_code(subtitle.name)

            if not lang_code:
                # 尝试从内容检测语言
                result = detector.detect_subtitle_language(str(subtitle))

                if result:
                    detected_lang, confidence = result
                    detected_count += 1

                    # 消毒语言代码以确保文件名安全
                    safe_lang_code = sanitize_language_code(detected_lang)

                    # 自动重命名
                    new_name = f"{subtitle.stem}.{safe_lang_code}{subtitle.suffix}"
                    new_path = subtitle.parent / new_name

                    # 检查目标文件是否已存在
                    if new_path.exists() and new_path != subtitle:
                        logger.warning(f"目标文件已存在，跳过重命名: {new_path}")
                        console.print(
                            f"[yellow]检测到语言但目标文件已存在，跳过:[/yellow] "
                            f"{subtitle.name} → {detected_lang}"
                        )
                        continue

                    # 在 dry_run 模式下只显示，不实际重命名
                    if dry_run:
                        console.print(
                            f"[cyan]将重命名:[/cyan] {subtitle.name} → {new_name} "
                            f"({detected_lang}, {confidence:.1%})"
                        )
                        # 更新列表中的引用为虚拟重命名后的路径，以便匹配时使用
                        subtitles[idx] = new_path
                        subtitle_index.pop(subtitle, None)
                        subtitle_index[new_path] = idx
                    else:
                        try:
                            subtitle.rename(new_path)
                            console.print(
                                f"[green]✓[/green] {subtitle.name} → {new_name} "
                                f"({detected_lang}, {confidence:.1%})"
                            )

                            # 更新列表中的引用
                            subtitles[idx] = new_path
                            subtitle_index.pop(subtitle, None)
                            subtitle_index[new_path] = idx
                        except OSError as e:
                            logger.error(f"重命名文件失败: {subtitle} -> {new_path}, {e}")
                            console.print(f"[red]重命名失败:[/red] {subtitle.name} ({e})")

        except FileNotFoundError as e:
            logger.error(f"字幕文件未找到: {subtitle}, {e}")
            console.print(f"[red]文件未找到，跳过:[/red] {subtitle.name}")
        except PermissionError as e:
            logger.error(f"权限不足: {subtitle}, {e}")
            console.print(f"[red]权限不足，跳过:[/red] {subtitle.name}")
        except Exception as e:
            logger.error(f"处理字幕文件失败: {subtitle}, {e}", exc_info=True)
            console.print(f"[red]处理失败，跳过:[/red] {subtitle.name}")

    if detected_count > 0:
        if dry_run:
            console.print(f"\n[cyan]将自动识别并重命名 {detected_count} 个字幕文件[/cyan]\n")
        else:
            console.print(f"\n[green]已自动识别并重命名 {detected_count} 个字幕文件[/green]\n")

    return detected_count


def _detect_audio_languages(
    videos: List[Path],
    args: argparse.Namespace,
    config: Config
) -> tuple[int, int]:
    """
    检测视频音轨语言并可选设置

    Args:
        videos: 视频文件列表
        args: 命令行参数
        config: 配置对象

    Returns:
        (检测数量, 更新数量)
    """
    # CLI 参数优先，如果未指定则使用配置
    should_detect_audio = args.detect_audio_language or config.audio_detection.enabled
    if not should_detect_audio or not videos or args.dry_run:
        return 0, 0

    console.print("\n[bold cyan]音频语言检测模式[/bold cyan]")

    # 尝试导入 audio_detector
    try:
        from .audio_detector import AudioLanguageDetector
    except ImportError:
        console.print(
            "[red]错误: faster-whisper 未安装[/red]\n"
            "[yellow]请运行: pip install mkmkv-smart[audio][/yellow]"
        )
        return 0, 0

    # 如果需要设置语言信息，初始化编辑器
    editor = None
    if args.set_audio_language:
        try:
            from .audio_editor import AudioTrackEditor
            editor = AudioTrackEditor()
            console.print("[green]✓ 将自动设置检测到的音轨语言信息[/green]")
        except RuntimeError as e:
            console.print(f"[yellow]警告: {e}[/yellow]")
            console.print("[yellow]将只显示检测结果，不修改文件[/yellow]")
            editor = None

    # 初始化检测器（使用配置参数）
    try:
        # 模型大小：CLI 参数优先，否则使用配置
        model_size = args.audio_model if args.audio_model is not None else config.audio_detection.model_size

        detector = AudioLanguageDetector(
            model_size=model_size,
            device=config.audio_detection.device,
            compute_type=config.audio_detection.compute_type,
            min_confidence=config.audio_detection.min_confidence
        )

        console.print(f"使用模型: {model_size}")
        console.print("[yellow]注意: 首次使用会自动下载模型，可能需要几分钟[/yellow]")

        detected_count = 0
        updated_count = 0

        for video in videos:
            try:
                console.print(f"\n[cyan]检测:[/cyan] {video.name}")

                # 检测第一个音轨（使用配置的采样参数）
                result = detector.detect_video_audio_language(
                    str(video),
                    track_index=0,
                    duration=config.audio_detection.max_duration,
                    smart_sampling=config.audio_detection.smart_sampling,
                    max_attempts=config.audio_detection.max_attempts
                )

                if result:
                    lang_code, confidence = result
                    detected_count += 1
                    console.print(
                        f"  [green]音轨 0:[/green] {lang_code} "
                        f"(置信度: {confidence:.2%})"
                    )

                    # 如果需要设置语言信息
                    if editor and not args.dry_run:
                        # 转换为 ISO 639-2 格式
                        iso639_2_code = convert_to_iso639_2(lang_code)
                        track_name = get_language_name(lang_code)

                        if video.suffix.lower() == '.mkv':
                            # MKV 文件：直接设置语言
                            success = editor.set_audio_track_language(
                                str(video),
                                track_index=0,
                                language_code=iso639_2_code,
                                track_name=track_name,
                                original_code=lang_code
                            )

                            if success:
                                updated_count += 1
                                console.print(
                                    f"  [green]✓ 已设置音轨语言:[/green] "
                                    f"{iso639_2_code} ({track_name})"
                                )
                            else:
                                console.print("  [yellow]⚠ 设置音轨语言失败[/yellow]")
                        else:
                            # 非 MKV 文件：转换为 MKV 并设置语言
                            output_file = video.with_suffix('.mkv')
                            console.print(f"  [cyan]→ 转换为 MKV 格式...[/cyan]")

                            success = editor.convert_to_mkv_with_language(
                                str(video),
                                str(output_file),
                                audio_track_index=0,
                                language_code=iso639_2_code,
                                track_name=track_name
                            )

                            if success:
                                updated_count += 1
                                console.print(
                                    f"  [green]✓ 已转换并设置音轨语言:[/green] "
                                    f"{iso639_2_code} ({track_name})"
                                )
                                console.print(f"  [green]输出文件:[/green] {output_file.name}")
                            else:
                                console.print("  [yellow]⚠ 转换失败[/yellow]")

                    elif editor and args.dry_run:
                        iso639_2_code = convert_to_iso639_2(lang_code)
                        track_name = get_language_name(lang_code)

                        if video.suffix.lower() == '.mkv':
                            console.print(
                                f"  [dim]→ 将设置音轨语言: {iso639_2_code} ({track_name})[/dim]"
                            )
                        else:
                            output_file = video.with_suffix('.mkv')
                            console.print(
                                f"  [dim]→ 将转换为 MKV 并设置音轨语言: {iso639_2_code} ({track_name})[/dim]"
                            )
                            console.print(f"  [dim]   输出文件: {output_file.name}[/dim]")

                else:
                    console.print("  [yellow]音轨 0: 检测失败[/yellow]")

            except FileNotFoundError as e:
                logger.error(f"视频文件未找到: {video}, {e}")
                console.print(f"  [red]文件未找到，跳过[/red]")
            except PermissionError as e:
                logger.error(f"权限不足: {video}, {e}")
                console.print(f"  [red]权限不足，跳过[/red]")
            except Exception as e:
                logger.error(f"处理视频文件失败: {video}, {e}", exc_info=True)
                console.print(f"  [red]处理失败，跳过[/red]")

        if detected_count > 0:
            console.print(f"\n[green]成功检测 {detected_count} 个视频的音轨语言[/green]")
            if updated_count > 0:
                console.print(f"[green]已设置 {updated_count} 个视频的音轨语言信息[/green]")
        else:
            console.print("[yellow]未检测到音轨语言[/yellow]")

        return detected_count, updated_count

    except Exception as e:
        console.print(f"[red]音频检测失败: {e}[/red]")
        if args.dry_run:
            import traceback
            traceback.print_exc()
        return 0, 0


def _prepare_merge_tasks(
    videos: List[Path],
    all_matches: Dict[str, Dict[str, MatchResult]],
    matcher: SmartMatcher,
    source_dir: Path,
    output_dir: Path,
    config: Config,
    track_order: Optional[str] = None
) -> tuple[List[Dict], int]:
    """
    准备合并任务

    Args:
        videos: 视频文件列表
        all_matches: 匹配结果字典
        matcher: 匹配器实例
        source_dir: 源目录
        output_dir: 输出目录
        config: 配置对象
        track_order: 轨道顺序（可选）

    Returns:
        (合并任务列表, 跳过数量)
    """
    merge_tasks = []
    skipped = 0

    for video in videos:
        lang_matches = all_matches.get(video.name, {})
        display_matches(video, lang_matches, matcher.normalizer)

        if lang_matches:
            # 准备字幕轨道
            subtitle_tracks = []
            first = True

            # 按照优先级排序：简体中文 > 繁体中文 > 英文 > 其他
            sorted_langs = sorted(
                lang_matches.items(),
                key=lambda item: _get_language_priority(item[0])
            )

            for lang, match in sorted_langs:
                track = SubtitleTrack(
                    file_path=str(source_dir / match.subtitle_file),
                    language_code=lang,
                    track_name=get_language_name(lang),
                    is_default=first,  # 第一个字幕设为默认
                    charset=config.output.default_charset  # 使用配置的字符集
                )
                subtitle_tracks.append(track)
                first = False

            # 输出文件路径
            output_file = output_dir / f"{video.stem}.mkv"

            # 检查输出文件是否与输入文件相同（避免覆盖输入文件）
            if output_file.resolve() == video.resolve():
                # 输入文件本身就是 MKV，且输出到同一目录，使用不同的文件名
                output_file = output_dir / f"{video.stem}-merged.mkv"
                logger.warning(
                    f"输出文件与输入文件相同，使用新文件名: {output_file.name}"
                )

            # 检查输出文件是否已存在（避免覆盖现有文件）
            if output_file.exists():
                # 添加数字后缀直到找到不存在的文件名
                counter = 1
                found_unique = False
                while counter <= 1000:
                    candidate = output_dir / f"{video.stem}-{counter}.mkv"
                    if not candidate.exists():
                        output_file = candidate
                        logger.warning(
                            f"输出文件已存在，使用新文件名: {output_file.name}"
                        )
                        found_unique = True
                        break
                    counter += 1

                # 如果找不到唯一的文件名，跳过这个视频
                if not found_unique:
                    logger.error(f"无法生成唯一的输出文件名: {video.name}")
                    skipped += 1
                    continue

            task = {
                'video_file': str(video),
                'subtitle_tracks': subtitle_tracks,
                'output_file': str(output_file)
            }

            # 如果指定了轨道顺序，添加到任务字典
            if track_order:
                task['track_order'] = track_order

            merge_tasks.append(task)
        else:
            skipped += 1

    return merge_tasks, skipped


def _detect_embedded_subtitles(
    merge_tasks: List[Dict],
    config: Config
) -> tuple[int, int]:
    """
    检测并设置嵌入字幕语言

    Args:
        merge_tasks: 合并任务列表
        config: 配置对象

    Returns:
        (处理数量, 检测数量)
    """
    console.print("\n[bold cyan]检测嵌入字幕语言...[/bold cyan]")
    logger.info("开始嵌入字幕语言检测")

    try:
        from .audio_editor import AudioTrackEditor
        editor = AudioTrackEditor()
        language_detector = LanguageDetector(
            min_confidence=config.language_detection.min_confidence,
            min_chars=config.language_detection.min_chars
        )

        processed_count = 0
        detected_count = 0

        for task in merge_tasks:
            video_file = task['video_file']
            video_path = Path(video_file)

            # 只处理 MKV 文件
            if video_path.suffix.lower() != '.mkv':
                logger.debug(f"跳过非 MKV 文件: {video_file}")
                continue

            processed_count += 1
            console.print(f"\n检测: {video_path.name}")

            try:
                detected = editor.detect_and_set_embedded_subtitle_languages(
                    video_file,
                    language_detector=language_detector,
                    dry_run=False
                )

                if detected:
                    detected_count += len(detected)
                    for idx, info in detected.items():
                        console.print(
                            f"  字幕轨道 {idx}: {info['detected_code']} "
                            f"(置信度: {info['confidence']:.1%})"
                        )
                        console.print(
                            f"  ✓ 已设置语言: {info['language_code']} "
                            f"({info['track_name']})"
                        )
                else:
                    console.print("  所有嵌入字幕均已标记语言")

            except FileNotFoundError as e:
                logger.error(f"文件未找到: {video_file}, {e}")
                console.print(f"[yellow]  警告: 文件未找到，跳过[/yellow]")
            except PermissionError as e:
                logger.error(f"权限错误: {video_file}, {e}")
                console.print(f"[yellow]  警告: 权限不足，跳过[/yellow]")
            except Exception as e:
                logger.error(f"检测单个文件失败: {video_file}, {e}", exc_info=True)
                console.print(f"[yellow]  警告: 检测失败，跳过[/yellow]")

        logger.info(f"嵌入字幕检测完成: 处理 {processed_count} 个文件, 检测 {detected_count} 个字幕")
        return processed_count, detected_count

    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        console.print(f"[yellow]警告: 无法加载嵌入字幕检测模块: {e}[/yellow]")
        return 0, 0
    except Exception as e:
        logger.error(f"嵌入字幕检测流程失败: {e}", exc_info=True)
        console.print(f"[yellow]警告: 嵌入字幕检测失败: {e}[/yellow]")
        return 0, 0


def _execute_merge(
    merge_tasks: List[Dict],
    args: argparse.Namespace,
    config: Config
) -> Dict[str, bool]:
    """
    执行合并操作

    Args:
        merge_tasks: 合并任务列表
        args: 命令行参数
        config: 配置对象

    Returns:
        合并结果字典
    """
    # 如果需要保留嵌入字幕，并且启用了语言检测，先检测并设置嵌入字幕的语言
    if args.keep_embedded_subtitles and config.language_detection.enabled:
        _detect_embedded_subtitles(merge_tasks, config)

    console.print("\n[bold]开始合并...[/bold]")
    merger = MKVMerger()
    results = merger.batch_merge(
        merge_tasks,
        dry_run=args.dry_run,
        keep_embedded_subtitles=args.keep_embedded_subtitles,
        show_progress=True
    )

    # 最终统计
    success_count = sum(1 for v in results.values() if v)
    console.print("\n" + "=" * 70)
    console.print("[bold]处理完成:[/bold]")
    console.print(f"[green]成功: {success_count} 个文件[/green]")
    if success_count < len(results):
        console.print(f"[red]失败: {len(results) - success_count} 个文件[/red]")

    return results


def run_match(args: argparse.Namespace, config: Config) -> int:
    """
    执行匹配流程

    这是一个高级编排函数，协调各个子任务的执行。

    Args:
        args: 命令行参数
        config: 配置对象

    Returns:
        退出码（0 表示成功，1 表示失败）
    """
    # 1. 初始化组件
    normalizer, matcher = _setup_components(args, config)

    # 2. 验证目录
    source_dir = Path(args.source)
    output_dir = Path(args.output) if args.output else source_dir

    error_code = _validate_directories(source_dir, output_dir, args.dry_run)
    if error_code:
        return error_code

    # 3. 收集文件
    videos, subtitles = collect_files(source_dir)

    # 4. 自动检测字幕语言并重命名
    _auto_detect_subtitle_languages(subtitles, config, normalizer, args.dry_run)

    # 5. 检测音频语言（非干运行模式）
    _detect_audio_languages(videos, args, config)

    # 6. 显示匹配信息
    console.print("\n[bold cyan]智能匹配模式[/bold cyan]")
    if args.dry_run:
        console.print("[yellow][ 干运行 - 不会实际执行 ][/yellow]")
    console.print(f"源目录: {source_dir}")
    console.print(f"找到 {len(videos)} 个视频文件")
    console.print(f"找到 {len(subtitles)} 个字幕文件")

    if not videos:
        console.print("[yellow]未找到视频文件[/yellow]")
        return 0

    # 7. 批量匹配
    video_names = [v.name for v in videos]
    subtitle_names = [s.name for s in subtitles]

    all_matches = matcher.batch_match(
        video_names,
        subtitle_names,
        language_priority=config.language.priority
    )

    # 8. 显示匹配结果并准备合并任务
    console.print("\n[bold]匹配结果:[/bold]")
    console.print("=" * 70)

    merge_tasks, skipped = _prepare_merge_tasks(
        videos,
        all_matches,
        matcher,
        source_dir,
        output_dir,
        config,
        track_order=args.track_order  # 传递轨道顺序参数
    )

    # 9. 统计
    console.print("\n" + "=" * 70)
    console.print(f"总计: {len(videos)} 个文件")
    console.print(f"[green]可处理: {len(merge_tasks)} 个文件[/green]")
    if skipped > 0:
        console.print(f"[yellow]跳过: {skipped} 个文件（无匹配字幕）[/yellow]")

    # 10. 执行合并或显示干运行信息
    if merge_tasks and not args.dry_run:
        _execute_merge(merge_tasks, args, config)
    elif args.dry_run:
        console.print("\n[yellow]这是干运行模式，未实际执行任何操作[/yellow]")
        if args.keep_embedded_subtitles:
            console.print("\n[bold cyan][ 嵌入字幕检测预览 ][/bold cyan]")
            console.print("将保留并检测视频中的嵌入字幕语言")

    return 0


def main() -> int:
    """主入口"""
    parser = argparse.ArgumentParser(
        description="mkmkv-smart: 智能视频字幕合并工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览匹配结果（干运行）
  mkmkv-smart --dry-run ~/Downloads

  # 执行合并
  mkmkv-smart ~/Downloads ~/Movies

  # 自定义阈值
  mkmkv-smart --threshold 40 ~/Downloads

  # 使用配置文件
  mkmkv-smart --config config.yaml ~/Downloads
        """
    )

    parser.add_argument(
        "source",
        help="源目录（包含视频和字幕文件）"
    )

    parser.add_argument(
        "output",
        nargs="?",
        help="输出目录（可选，默认为源目录）"
    )

    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="干运行模式：只显示匹配结果，不实际执行"
    )

    parser.add_argument(
        "-t", "--threshold",
        type=float,
        help="相似度阈值 (0-100，默认: 30)"
    )

    parser.add_argument(
        "-m", "--method",
        choices=sorted(VALID_MATCH_METHODS),
        help="匹配方法（默认: hybrid）"
    )

    parser.add_argument(
        "-c", "--config",
        help="配置文件路径"
    )

    parser.add_argument(
        "--detect-audio-language",
        action="store_true",
        help="自动检测视频音轨语言（需要安装: pip install mkmkv-smart[audio]）"
    )

    parser.add_argument(
        "--audio-model",
        choices=["tiny", "base", "small", "medium", "large"],
        default=None,
        help="音频检测模型大小（默认从配置文件读取，配置默认: small）"
    )

    parser.add_argument(
        "--set-audio-language",
        action="store_true",
        help="自动设置检测到的音轨语言信息（需要 --detect-audio-language，仅支持 MKV 格式）"
    )

    parser.add_argument(
        "--keep-embedded-subtitles",
        action="store_true",
        help="保留视频中的嵌入字幕，并自动检测未标记语言的字幕"
    )

    parser.add_argument(
        "--track-order",
        type=str,
        help="轨道顺序（例如：'0:0,0:1,1:0,2:0'，0=视频文件，1+=字幕文件）"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    # 加载配置（用于参数验证和后续处理）
    try:
        config = Config.load(args.config) if args.config else Config()
    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
        console.print(
            f"[red]错误: 配置文件加载失败[/red]\n"
            f"  文件: {args.config or '默认配置'}\n"
            f"  原因: {str(e)}"
        )
        logger.error(f"配置加载失败: {e}")
        return 1
    except Exception as e:
        console.print(
            f"[red]错误: 配置文件加载时发生未知错误[/red]\n"
            f"  详细信息: {str(e)}"
        )
        logger.error(f"配置加载时发生未知错误: {e}", exc_info=True)
        return 1

    # 参数验证
    if args.threshold is not None and (args.threshold < 0 or args.threshold > 100):
        console.print(
            f"[red]错误: --threshold 参数必须在 0-100 范围内，当前值: {args.threshold}[/red]"
        )
        return 1

    if args.set_audio_language and not (args.detect_audio_language or config.audio_detection.enabled):
        console.print(
            "[yellow]警告: --set-audio-language 需要启用音频检测才有效（使用 --detect-audio-language 或在配置中设置 audio_detection.enabled）[/yellow]"
        )
        logger.warning(
            "--set-audio-language 参数被忽略（未启用音频检测）"
        )

    try:
        return run_match(args, config)
    except KeyboardInterrupt:
        console.print("\n[yellow]已取消[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]错误: {e}[/red]")
        if args.dry_run:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
