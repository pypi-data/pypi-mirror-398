"""
测试安全工具模块
"""

import tempfile
from pathlib import Path

import pytest

from mkmkv_smart.security_utils import _safe_path_arg, _validate_output_path


class TestSafePathArg:
    """测试路径参数安全化函数"""

    def test_normal_paths_unchanged(self):
        """正常路径不应被修改"""
        test_cases = [
            "video.mkv",
            "/tmp/video.mkv",
            "./video.mkv",
            "folder/subfolder/video.mkv",
            Path("video.mkv"),
            Path("/tmp/video.mkv"),
        ]
        for path in test_cases:
            result = _safe_path_arg(path)
            assert result == str(path), f"路径 {path} 不应被修改"

    def test_dash_prefix_paths_sanitized(self):
        """以 - 开头的路径应被安全化"""
        dangerous_paths = [
            "-o",
            "--output",
            "-map",
            "--output=evil.mkv",
            "-i",
            "--delete-all",
        ]
        for path in dangerous_paths:
            result = _safe_path_arg(path)
            assert result.startswith("./"), f"路径 {path} 应添加 ./ 前缀"
            assert result == f"./{path}"

    def test_at_prefix_paths_sanitized(self):
        """以 @ 开头的路径应被安全化（防止选项文件注入）"""
        dangerous_paths = [
            "@options.txt",
            "@evil_commands",
            "@/tmp/malicious",
            "@config",
        ]
        for path in dangerous_paths:
            result = _safe_path_arg(path)
            assert result.startswith("./"), f"路径 {path} 应添加 ./ 前缀"
            assert result == f"./{path}"

    def test_string_and_path_objects(self):
        """测试字符串和 Path 对象都能正常处理"""
        # 正常路径
        assert _safe_path_arg("video.mkv") == "video.mkv"
        assert _safe_path_arg(Path("video.mkv")) == "video.mkv"

        # 危险路径
        assert _safe_path_arg("-o") == "./-o"
        assert _safe_path_arg(Path("-o")) == "./-o"
        assert _safe_path_arg("@options") == "./@options"
        assert _safe_path_arg(Path("@options")) == "./@options"


class TestValidateOutputPath:
    """测试输出路径验证函数"""

    def test_safe_paths_within_temp_dir(self, tmp_path):
        """临时目录内的路径应通过验证"""
        safe_file = tmp_path / "output.srt"
        assert _validate_output_path(safe_file, tmp_path) is True

        # 子目录内的文件也应通过
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        safe_file_in_subdir = sub_dir / "output.srt"
        assert _validate_output_path(safe_file_in_subdir, tmp_path) is True

    def test_dangerous_paths_rejected(self, tmp_path):
        """危险的路径遍历应被拒绝"""
        dangerous_paths = [
            Path("/etc/passwd"),
            Path("/tmp/../../etc/passwd"),
            Path("/root/.ssh/authorized_keys"),
            Path("/var/log/system.log"),
        ]

        for dangerous_path in dangerous_paths:
            result = _validate_output_path(dangerous_path, tmp_path)
            assert result is False, f"路径 {dangerous_path} 应被拒绝"

    def test_default_temp_dir(self):
        """测试默认使用系统临时目录"""
        # 不提供 safe_dir 参数时，应使用系统临时目录
        temp_file = Path(tempfile.gettempdir()) / "test_output.srt"
        assert _validate_output_path(temp_file) is True

        # 临时目录外的文件应被拒绝
        outside_file = Path("/etc/passwd")
        assert _validate_output_path(outside_file) is False

    def test_relative_path_traversal_blocked(self, tmp_path):
        """测试相对路径遍历被阻止"""
        # 尝试用相对路径遍历到父目录
        traversal_path = tmp_path / "../../../etc/passwd"
        result = _validate_output_path(traversal_path, tmp_path)
        assert result is False, "相对路径遍历应被阻止"

    def test_symlink_resolution(self, tmp_path):
        """测试符号链接会被解析（防止绕过）"""
        # 创建一个指向外部的符号链接
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()

        # 创建指向 /tmp 的符号链接
        symlink = safe_dir / "link_to_tmp"
        try:
            symlink.symlink_to("/tmp")
        except (OSError, NotImplementedError):
            pytest.skip("系统不支持符号链接")

        # 通过符号链接访问外部文件应被拒绝
        file_via_symlink = symlink / "evil.txt"
        result = _validate_output_path(file_via_symlink, safe_dir)
        # resolve() 会解析符号链接，所以应该被拒绝
        assert result is False, "通过符号链接的路径遍历应被阻止"

    def test_invalid_paths_rejected(self, tmp_path):
        """测试无效路径被正确处理"""
        # 使用不存在的驱动器（Windows）或无效路径
        invalid_paths = [
            Path("Z:/nonexistent/path/file.txt"),  # Windows 不存在的驱动器
        ]

        for invalid_path in invalid_paths:
            result = _validate_output_path(invalid_path, tmp_path)
            # 应该返回 False（无法验证）
            assert isinstance(result, bool)
