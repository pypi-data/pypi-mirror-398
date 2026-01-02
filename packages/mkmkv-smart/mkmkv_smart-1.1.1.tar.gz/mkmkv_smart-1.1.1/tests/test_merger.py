"""
测试 mkvmerge 封装模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from mkmkv_smart.merger import MKVMerger, SubtitleTrack
from mkmkv_smart.language_utils import LANGUAGE_NAMES


class TestSubtitleTrack:
    """测试 SubtitleTrack 数据类"""

    def test_subtitle_track_creation(self):
        """测试创建字幕轨道"""
        track = SubtitleTrack(
            file_path="/path/to/subtitle.srt",
            language_code="zh-hans",
            track_name="简体中文",
            is_default=True,
            charset="UTF-8"
        )
        assert track.file_path == "/path/to/subtitle.srt"
        assert track.language_code == "zh-hans"
        assert track.track_name == "简体中文"
        assert track.is_default is True
        assert track.charset == "UTF-8"

    def test_subtitle_track_defaults(self):
        """测试字幕轨道默认值"""
        track = SubtitleTrack(
            file_path="/path/to/subtitle.srt",
            language_code="en",
            track_name="English"
        )
        assert track.is_default is False
        assert track.charset == "UTF-8"


class TestLanguageMap:
    """测试语言映射"""

    def test_language_map_chinese(self):
        """测试中文语言代码"""
        assert LANGUAGE_NAMES["zh"] == "中文"
        assert LANGUAGE_NAMES["zh-hans"] == "简体中文"
        assert LANGUAGE_NAMES["zh-hant"] == "繁體中文"

    def test_language_map_chinese_aliases(self):
        """测试中文别名映射"""
        assert LANGUAGE_NAMES["chs"] == "简体中文"
        assert LANGUAGE_NAMES["cht"] == "繁體中文"
        assert LANGUAGE_NAMES["gb"] == "简体中文"
        assert LANGUAGE_NAMES["big5"] == "繁體中文"

    def test_language_map_english(self):
        """测试英文语言代码"""
        assert LANGUAGE_NAMES["en"] == "English"
        assert "english" in LANGUAGE_NAMES["en"].lower()

    def test_language_map_japanese(self):
        """测试日文语言代码"""
        assert LANGUAGE_NAMES["ja"] == "日本語"

    def test_language_map_korean(self):
        """测试韩文语言代码"""
        assert LANGUAGE_NAMES["ko"] == "한국어"


class TestMKVMerger:
    """测试 MKVMerger 类"""

    @patch('mkmkv_smart.merger.shutil.which')
    def test_initialization_success(self, mock_which):
        """测试成功初始化"""
        mock_which.return_value = "/usr/bin/mkvmerge"

        merger = MKVMerger()
        assert merger.mkvmerge_path == "mkvmerge"

    @patch('mkmkv_smart.merger.shutil.which')
    def test_initialization_custom_path(self, mock_which):
        """测试自定义路径初始化"""
        mock_which.return_value = "/custom/path/mkvmerge"

        merger = MKVMerger(
            mkvmerge_path="/custom/path/mkvmerge"
        )
        assert merger.mkvmerge_path == "/custom/path/mkvmerge"

    @patch('mkmkv_smart.merger.shutil.which')
    def test_initialization_mkvmerge_not_found(self, mock_which):
        """测试 mkvmerge 未找到"""
        mock_which.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            MKVMerger()

        assert "mkvmerge not found" in str(exc_info.value)

    @patch('mkmkv_smart.merger.shutil.which')
    def test_is_mkvmerge_available_true(self, mock_which):
        """测试 mkvmerge 可用"""
        mock_which.return_value = "/usr/bin/mkvmerge"

        merger = MKVMerger()
        assert merger.is_mkvmerge_available() is True

    @patch('mkmkv_smart.merger.shutil.which')
    def test_is_mkvmerge_available_false(self, mock_which):
        """测试 mkvmerge 不可用"""
        mock_which.return_value = None

        # 不能直接创建实例，因为会抛出异常
        # 所以我们只测试方法逻辑
        with patch.object(MKVMerger, '__init__', lambda x: None):
            merger = MKVMerger()
            merger.mkvmerge_path = "nonexistent"
            mock_which.return_value = None
            assert merger.is_mkvmerge_available() is False

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_merge_success(self, mock_run, mock_path, mock_which):
        """测试成功合并"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)

        # Mock 视频文件路径
        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        # Mock 字幕文件路径
        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        # Mock 输出文件路径
        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.resolve.return_value = Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        # 根据调用返回不同的 mock
        def path_side_effect(path_str):
            if 'video.mp4' in path_str:
                return mock_video_path
            elif 'zh.srt' in path_str:
                return mock_subtitle_path
            elif 'output.mkv' in path_str:
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect

        merger = MKVMerger()
        tracks = [
            SubtitleTrack(
                file_path="/path/to/zh.srt",
                language_code="zh-hans",
                track_name="简体中文",
                is_default=True
            )
        ]

        result = merger.merge(
            video_file="/path/to/video.mp4",
            subtitle_tracks=tracks,
            output_file="/path/to/output.mkv"
        )

        assert result is True
        assert mock_run.called

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_merge_failure(self, mock_run, mock_path, mock_which):
        """测试合并失败"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.side_effect = subprocess.CalledProcessError(1, 'mkvmerge', stderr='Error')

        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if path_str == "/path/to/video.mp4":
                return mock_video_path
            if path_str == "/path/to/zh.srt":
                return mock_subtitle_path
            if path_str == "/path/to/output.mkv":
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect

        merger = MKVMerger()
        tracks = [
            SubtitleTrack(
                file_path="/path/to/zh.srt",
                language_code="zh",
                track_name="中文"
            )
        ]

        result = merger.merge(
            video_file="/path/to/video.mp4",
            subtitle_tracks=tracks,
            output_file="/path/to/output.mkv"
        )

        assert result is False
        # 验证 subprocess.run 被调用（确保测试覆盖到 subprocess 错误分支）
        mock_run.assert_called_once()

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    def test_merge_dry_run(self, mock_path, mock_which, capsys):
        """测试干运行模式"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        # Mock 文件存在性检查
        mock_path_instance = Mock()
        mock_path_instance.is_file.return_value = True
        mock_path.return_value = mock_path_instance

        merger = MKVMerger()
        tracks = [
            SubtitleTrack(
                file_path="/path/to/zh.srt",
                language_code="zh",
                track_name="中文"
            )
        ]

        result = merger.merge(
            video_file="/path/to/video.mp4",
            subtitle_tracks=tracks,
            output_file="/path/to/output.mkv",
            dry_run=True
        )

        assert result is True

        # 验证输出
        captured = capsys.readouterr()
        assert "将执行以下命令" in captured.out

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_merge_multiple_subtitles(self, mock_run, mock_path, mock_which):
        """测试多个字幕合并"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)

        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_zh_path = Mock()
        mock_subtitle_zh_path.is_file.return_value = True

        mock_subtitle_en_path = Mock()
        mock_subtitle_en_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if path_str == "/path/to/video.mp4":
                return mock_video_path
            if path_str == "/path/to/zh.srt":
                return mock_subtitle_zh_path
            if path_str == "/path/to/en.srt":
                return mock_subtitle_en_path
            if path_str == "/path/to/output.mkv":
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect

        merger = MKVMerger()
        tracks = [
            SubtitleTrack(
                file_path="/path/to/zh.srt",
                language_code="zh-hans",
                track_name="简体中文",
                is_default=True
            ),
            SubtitleTrack(
                file_path="/path/to/en.srt",
                language_code="en",
                track_name="English",
                is_default=False
            ),
        ]

        result = merger.merge(
            video_file="/path/to/video.mp4",
            subtitle_tracks=tracks,
            output_file="/path/to/output.mkv"
        )

        assert result is True

        # 验证调用参数
        call_args = mock_run.call_args[0][0]
        assert "/path/to/zh.srt" in call_args
        assert "/path/to/en.srt" in call_args

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_merge_with_extra_args(self, mock_run, mock_path, mock_which):
        """测试带额外参数的合并"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)
        # Mock 文件存在性检查
        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if "video" in path_str and ".mp4" in path_str:
                return mock_video_path
            if ".srt" in path_str or ".ass" in path_str:
                return mock_subtitle_path
            if "output" in path_str and ".mkv" in path_str:
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect
        merger = MKVMerger()
        tracks = [
            SubtitleTrack(
                file_path="/path/to/zh.srt",
                language_code="zh",
                track_name="中文"
            )
        ]

        result = merger.merge(
            video_file="/path/to/video.mp4",
            subtitle_tracks=tracks,
            output_file="/path/to/output.mkv",
            extra_args=["--title", "My Movie"]
        )

        assert result is True

        # 验证额外参数被包含
        call_args = mock_run.call_args[0][0]
        assert "--title" in call_args
        assert "My Movie" in call_args

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_merge_command_structure(self, mock_run, mock_path, mock_which):
        """测试合并命令结构"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)
        # Mock 文件存在性检查
        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if "video" in path_str and ".mp4" in path_str:
                return mock_video_path
            if ".srt" in path_str or ".ass" in path_str:
                return mock_subtitle_path
            if "output" in path_str and ".mkv" in path_str:
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect
        merger = MKVMerger()
        tracks = [
            SubtitleTrack(
                file_path="/path/to/zh.srt",
                language_code="zh-hans",
                track_name="简体中文",
                is_default=True,
                charset="UTF-8"
            )
        ]

        merger.merge(
            video_file="/path/to/video.mp4",
            subtitle_tracks=tracks,
            output_file="/path/to/output.mkv"
        )

        # 验证命令结构
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "mkvmerge"
        assert "-o" in call_args
        assert "/path/to/output.mkv" in call_args
        assert "-S" in call_args  # 不复制原视频字幕
        assert "--no-global-tags" in call_args
        assert "/path/to/video.mp4" in call_args

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_batch_merge_success(self, mock_run, mock_path, mock_which, capsys):
        """测试批量合并成功"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)
        # Mock 文件存在性检查
        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if "video" in path_str and ".mp4" in path_str:
                return mock_video_path
            if ".srt" in path_str or ".ass" in path_str:
                return mock_subtitle_path
            if "output" in path_str and ".mkv" in path_str:
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect
        merger = MKVMerger()

        tasks = [
            {
                'video_file': '/path/to/video1.mp4',
                'subtitle_tracks': [
                    SubtitleTrack(
                        file_path="/path/to/video1.zh.srt",
                        language_code="zh",
                        track_name="中文"
                    )
                ],
                'output_file': '/path/to/output1.mkv'
            },
            {
                'video_file': '/path/to/video2.mp4',
                'subtitle_tracks': [
                    SubtitleTrack(
                        file_path="/path/to/video2.zh.srt",
                        language_code="zh",
                        track_name="中文"
                    )
                ],
                'output_file': '/path/to/output2.mkv'
            }
        ]

        results = merger.batch_merge(tasks, show_progress=True)

        assert len(results) == 2
        assert all(results.values())  # 所有都成功

        # 验证进度输出
        captured = capsys.readouterr()
        assert "[1/2]" in captured.out
        assert "[2/2]" in captured.out

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_batch_merge_partial_failure(self, mock_run, mock_path, mock_which):
        """测试批量合并部分失败"""
        mock_which.return_value = "/usr/bin/mkvmerge"

        # 第一个成功，第二个失败
        mock_run.side_effect = [
            Mock(returncode=0),
            subprocess.CalledProcessError(1, 'mkvmerge', stderr='Error')
        ]

        # Mock 文件存在性检查
        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if "video" in path_str and ".mp4" in path_str:
                return mock_video_path
            if ".srt" in path_str or ".ass" in path_str:
                return mock_subtitle_path
            if "output" in path_str and ".mkv" in path_str:
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect
        merger = MKVMerger()

        tasks = [
            {
                'video_file': '/path/to/video1.mp4',
                'subtitle_tracks': [],
                'output_file': '/path/to/output1.mkv'
            },
            {
                'video_file': '/path/to/video2.mp4',
                'subtitle_tracks': [],
                'output_file': '/path/to/output2.mkv'
            }
        ]

        results = merger.batch_merge(tasks, show_progress=False)

        assert results['/path/to/video1.mp4'] is True
        assert results['/path/to/video2.mp4'] is False

    @patch('mkmkv_smart.merger.shutil.which')
    def test_batch_merge_empty_tasks(self, mock_which):
        """测试空任务列表"""
        mock_which.return_value = "/usr/bin/mkvmerge"

        merger = MKVMerger()
        results = merger.batch_merge([])

        assert len(results) == 0

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    def test_batch_merge_dry_run(self, mock_path, mock_which, capsys):
        """测试批量干运行"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        # Mock 文件存在性检查
        mock_path_instance = Mock()
        mock_path_instance.is_file.return_value = True
        mock_path.return_value = mock_path_instance

        merger = MKVMerger()

        tasks = [
            {
                'video_file': '/path/to/video1.mp4',
                'subtitle_tracks': [],
                'output_file': '/path/to/output1.mkv'
            }
        ]

        results = merger.batch_merge(tasks, dry_run=True)

        assert results['/path/to/video1.mp4'] is True

        # 验证干运行输出
        captured = capsys.readouterr()
        assert "将执行以下命令" in captured.out


class TestMKVMergerIntegration:
    """测试集成场景"""

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.Path')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_real_world_scenario(self, mock_run, mock_path, mock_which):
        """测试真实场景"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)
        # Mock 文件存在性检查
        # Mock 文件存在性检查
        def resolve_not_equal():
            return Mock(spec=['__eq__'], __eq__=lambda self, other: False)

        mock_video_path = Mock()
        mock_video_path.is_file.return_value = True
        mock_video_path.resolve.return_value = resolve_not_equal()

        mock_subtitle_path = Mock()
        mock_subtitle_path.is_file.return_value = True

        mock_output_path = Mock()
        mock_output_path.exists.return_value = False
        mock_output_path.parent.exists.return_value = True
        mock_output_path.parent.is_dir.return_value = True
        mock_output_path.parent.mkdir.return_value = None
        mock_output_path.resolve.return_value = resolve_not_equal()

        def path_side_effect(path_str):
            if "video" in path_str and ".mp4" in path_str:
                return mock_video_path
            if ".srt" in path_str or ".ass" in path_str:
                return mock_subtitle_path
            if "output" in path_str and ".mkv" in path_str:
                return mock_output_path
            return Mock()

        mock_path.side_effect = path_side_effect
        merger = MKVMerger()

        # 模拟真实场景：电影配多语言字幕
        tracks = [
            SubtitleTrack(
                file_path="/downloads/Movie.2024.zh-hans.srt",
                language_code="zh-hans",
                track_name="简体中文",
                is_default=True
            ),
            SubtitleTrack(
                file_path="/downloads/Movie.2024.en.srt",
                language_code="en",
                track_name="English",
                is_default=False
            ),
        ]

        result = merger.merge(
            video_file="/downloads/Movie.2024.1080p.mp4",
            subtitle_tracks=tracks,
            output_file="/movies/Movie.2024.mkv"
        )

        assert result is True

        # 验证命令包含所有字幕
        call_args = mock_run.call_args[0][0]
        assert "zh-hans" in str(call_args)
        assert "en" in str(call_args)


class TestSecurityFixes:
    """测试安全修复 - M3: extra_args 验证"""

    @patch('shutil.which')
    def test_merge_rejects_output_args(self, mock_which, tmp_path):
        """M3: 测试拒绝包含输出参数的 extra_args"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()
        output_file = tmp_path / "output.mkv"

        tracks = [
            SubtitleTrack(
                file_path=str(subtitle_file),
                language_code="zh-hans",
                track_name="简体中文"
            )
        ]

        # 测试各种形式的输出参数都被拒绝
        dangerous_args_list = [
            ["-o"],
            ["--output"],
            ["-o=evil.mkv"],
            ["--output=evil.mkv"],
            ["--some-flag", "-o", "evil.mkv"],
        ]

        for dangerous_args in dangerous_args_list:
            result = merger.merge(
                video_file=str(video_file),
                subtitle_tracks=tracks,
                output_file=str(output_file),
                extra_args=dangerous_args
            )

            # 应该返回 False（被拒绝）
            assert result is False, f"应该拒绝: {dangerous_args}"

    @patch('shutil.which')
    def test_merge_rejects_command_line_charset(self, mock_which, tmp_path):
        """M3: 测试拒绝 --command-line-charset 参数"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()
        output_file = tmp_path / "output.mkv"

        tracks = [SubtitleTrack(
            file_path=str(subtitle_file),
            language_code="en",
            track_name="English"
        )]

        # 测试危险参数被拒绝
        dangerous_args = [
            ["--command-line-charset", "UTF-8"],
            ["--command-line-charset=UTF-8"],
            ["--ui-language", "en"],
            ["--ui-language=en"],
        ]

        for args in dangerous_args:
            result = merger.merge(
                video_file=str(video_file),
                subtitle_tracks=tracks,
                output_file=str(output_file),
                extra_args=args
            )
            assert result is False, f"应该拒绝: {args}"

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_merge_allows_safe_args(self, mock_run, mock_which, tmp_path):
        """M3: 测试允许安全的 extra_args"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()
        output_file = tmp_path / "output.mkv"

        tracks = [SubtitleTrack(
            file_path=str(subtitle_file),
            language_code="zh-hans",
            track_name="简体中文"
        )]

        # 测试安全参数被允许
        safe_args = [
            ["--title", "My Movie"],
            ["--verbose"],
            ["--track-order", "0:0,1:0"],
        ]

        for args in safe_args:
            result = merger.merge(
                video_file=str(video_file),
                subtitle_tracks=tracks,
                output_file=str(output_file),
                extra_args=args
            )

            # 应该成功
            assert result is True, f"应该允许: {args}"

            # 验证参数被正确传递
            call_args = mock_run.call_args[0][0]
            for arg in args:
                assert arg in call_args


class TestTrackOrder:
    """测试轨道顺序功能"""

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_merge_with_valid_track_order(self, mock_run, mock_which, tmp_path):
        """测试有效的轨道顺序"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()
        output_file = tmp_path / "output.mkv"

        tracks = [SubtitleTrack(
            file_path=str(subtitle_file),
            language_code="zh-hans",
            track_name="简体中文"
        )]

        # 测试有效的轨道顺序格式
        valid_track_orders = [
            "0:0,0:1,1:0",
            "0:0",
            "0:0,0:1",
            "0:0,0:1,0:2,1:0,2:0",
        ]

        for track_order in valid_track_orders:
            result = merger.merge(
                video_file=str(video_file),
                subtitle_tracks=tracks,
                output_file=str(output_file),
                track_order=track_order
            )

            # 应该成功
            assert result is True, f"应该接受轨道顺序: {track_order}"

            # 验证 track_order 参数被传递到 mkvmerge 命令
            call_args = mock_run.call_args[0][0]
            assert '--track-order' in call_args
            assert track_order in call_args

    @patch('shutil.which')
    def test_merge_with_invalid_track_order(self, mock_which, tmp_path):
        """测试无效的轨道顺序格式被拒绝"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()
        output_file = tmp_path / "output.mkv"

        tracks = [SubtitleTrack(
            file_path=str(subtitle_file),
            language_code="zh-hans",
            track_name="简体中文"
        )]

        # 测试无效的轨道顺序格式
        invalid_track_orders = [
            "0:0,",           # 末尾有逗号
            ",0:0",           # 开头有逗号
            "0:0,,1:0",       # 连续逗号
            "0",              # 缺少轨道编号
            "0:",             # 缺少轨道编号
            ":0",             # 缺少文件编号
            "abc:0",          # 非数字文件编号
            "0:abc",          # 非数字轨道编号
            "0:0;1:0",        # 使用分号而非逗号
            "0:0 1:0",        # 使用空格而非逗号
        ]

        for track_order in invalid_track_orders:
            result = merger.merge(
                video_file=str(video_file),
                subtitle_tracks=tracks,
                output_file=str(output_file),
                track_order=track_order
            )

            # 应该失败（返回 False）
            assert result is False, f"应该拒绝无效轨道顺序: {track_order}"

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_merge_without_track_order(self, mock_run, mock_which, tmp_path):
        """测试不指定轨道顺序时使用默认顺序"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()
        output_file = tmp_path / "output.mkv"

        tracks = [SubtitleTrack(
            file_path=str(subtitle_file),
            language_code="zh-hans",
            track_name="简体中文"
        )]

        result = merger.merge(
            video_file=str(video_file),
            subtitle_tracks=tracks,
            output_file=str(output_file)
            # 不指定 track_order
        )

        # 应该成功
        assert result is True

        # 验证 --track-order 参数不在命令中
        call_args = mock_run.call_args[0][0]
        assert '--track-order' not in call_args

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_batch_merge_with_track_order(self, mock_run, mock_which, tmp_path):
        """测试批量合并支持轨道顺序"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        merger = MKVMerger()

        # 创建测试文件
        video1 = tmp_path / "video1.mp4"
        video1.touch()
        video2 = tmp_path / "video2.mp4"
        video2.touch()
        subtitle1 = tmp_path / "subtitle1.srt"
        subtitle1.touch()
        subtitle2 = tmp_path / "subtitle2.srt"
        subtitle2.touch()

        tasks = [
            {
                'video_file': str(video1),
                'subtitle_tracks': [
                    SubtitleTrack(
                        file_path=str(subtitle1),
                        language_code="zh-hans",
                        track_name="简体中文"
                    )
                ],
                'output_file': str(tmp_path / "output1.mkv"),
                'track_order': "0:0,0:1,1:0"  # 指定轨道顺序
            },
            {
                'video_file': str(video2),
                'subtitle_tracks': [
                    SubtitleTrack(
                        file_path=str(subtitle2),
                        language_code="en",
                        track_name="English"
                    )
                ],
                'output_file': str(tmp_path / "output2.mkv")
                # 不指定轨道顺序
            }
        ]

        results = merger.batch_merge(tasks, show_progress=False)

        # 两个任务都应该成功
        assert results[str(video1)] is True
        assert results[str(video2)] is True

        # 验证第一次调用包含 track_order
        first_call_args = mock_run.call_args_list[0][0][0]
        assert '--track-order' in first_call_args
        assert '0:0,0:1,1:0' in first_call_args

        # 验证第二次调用不包含 track_order
        second_call_args = mock_run.call_args_list[1][0][0]
        assert '--track-order' not in second_call_args

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_track_order_in_dry_run(self, mock_run, mock_which, tmp_path, capsys):
        """测试干运行模式显示轨道顺序"""
        mock_which.return_value = '/usr/bin/mkvmerge'
        merger = MKVMerger()

        video_file = tmp_path / "video.mp4"
        video_file.touch()
        subtitle_file = tmp_path / "subtitle.srt"
        subtitle_file.touch()

        tracks = [SubtitleTrack(
            file_path=str(subtitle_file),
            language_code="zh-hans",
            track_name="简体中文"
        )]

        result = merger.merge(
            video_file=str(video_file),
            subtitle_tracks=tracks,
            output_file=str(tmp_path / "output.mkv"),
            track_order="0:0,0:1,1:0",
            dry_run=True
        )

        # 应该成功
        assert result is True

        # 验证输出包含轨道顺序
        captured = capsys.readouterr()
        assert "将执行以下命令" in captured.out
        assert "--track-order" in captured.out
        assert "0:0,0:1,1:0" in captured.out

        # 验证 subprocess.run 未被调用（干运行模式）
        assert not mock_run.called
