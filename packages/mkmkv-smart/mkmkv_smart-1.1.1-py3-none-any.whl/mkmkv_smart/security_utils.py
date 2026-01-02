"""
安全工具模块

提供通用的安全防护函数，防御常见的安全漏洞。
"""

import logging
import tempfile
from pathlib import Path
from typing import Union, Optional

logger = logging.getLogger(__name__)


def _safe_path_arg(path: Union[str, Path]) -> str:
    """
    安全化路径参数，防止被外部工具解释为命令行选项

    Args:
        path: 文件路径（字符串或 Path 对象）

    Returns:
        安全的路径字符串

    Note:
        防御 CWE-88 参数注入：文件名如 '--output=/tmp/evil.mkv' 或 '-map' 或 '@options'
        会被外部工具（如 mkvmerge/mkvpropedit/ffmpeg/ffprobe）误解为选项或选项文件而非文件名。
        通过添加 './' 前缀使以 '-' 或 '@' 开头的路径变为相对路径。

    Examples:
        >>> _safe_path_arg("video.mkv")
        'video.mkv'
        >>> _safe_path_arg("--output=evil.mkv")
        './/--output=evil.mkv'
        >>> _safe_path_arg("@options.txt")
        './/@options.txt'
    """
    path_str = str(path)
    if path_str.startswith(("-", "@")):
        return f"./{path_str}"
    return path_str


def _validate_output_path(output_file: Path, safe_dir: Optional[Path] = None) -> bool:
    """
    验证输出路径在安全目录内，防止路径遍历攻击

    Args:
        output_file: 输出文件路径
        safe_dir: 允许的安全目录（默认为系统临时目录）

    Returns:
        True 如果路径在安全目录内，否则 False

    Note:
        防御 CWE-22 路径遍历：防止通过 '../../../etc/passwd' 等路径
        写入敏感系统文件。

        使用 Path.resolve() 解析符号链接和相对路径，然后检查是否在
        安全目录的子树内。

    Security:
        - 阻止路径遍历攻击（如 '../../../etc/passwd'）
        - 阻止符号链接绕过（resolve() 会解析符号链接）
        - 默认仅允许写入临时目录

    Examples:
        >>> _validate_output_path(Path("/tmp/safe.txt"), Path("/tmp"))
        True
        >>> _validate_output_path(Path("/etc/passwd"), Path("/tmp"))
        False
        >>> _validate_output_path(Path("/tmp/../etc/passwd"), Path("/tmp"))
        False
    """
    if safe_dir is None:
        safe_dir = Path(tempfile.gettempdir())

    try:
        # 解析为绝对路径，解析符号链接
        output_abs = output_file.resolve()
        safe_abs = safe_dir.resolve()

        # 检查是否在安全目录内
        try:
            output_abs.relative_to(safe_abs)
            return True
        except ValueError:
            # 不在安全目录内
            logger.warning(
                f"路径遍历攻击尝试: {output_file} 不在安全目录 {safe_dir} 内"
            )
            return False

    except (OSError, ValueError) as e:
        # 路径无效或无法解析
        logger.debug(f"路径验证失败: {output_file}, {e}")
        return False
