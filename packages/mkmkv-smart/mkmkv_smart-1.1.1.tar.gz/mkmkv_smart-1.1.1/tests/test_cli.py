"""
测试命令行界面模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sys
from io import StringIO

from mkmkv_smart.cli import (
    collect_files,
    display_matches,
    run_match,
    main,
    sanitize_language_code,
    _get_language_priority,
)
from mkmkv_smart.matcher import MatchResult
from mkmkv_smart.config import Config


class TestSanitizeLanguageCode:
    """测试语言代码消毒 - P2 Issue"""

    def test_sanitize_language_code_allows_lowercase(self):
        """测试保持小写语言代码"""
        assert sanitize_language_code("en") == "en"
        assert sanitize_language_code("zh-hans") == "zh-hans"
        assert sanitize_language_code("ja") == "ja"

    def test_sanitize_language_code_normalizes_case(self):
        """测试大写/混合大小写被规范化"""
        assert sanitize_language_code("EN") == "en"
        assert sanitize_language_code("Zh-Hans") == "zh-hans"
        assert sanitize_language_code("JA") == "ja"
        assert sanitize_language_code("zh-HANS") == "zh-hans"

    def test_sanitize_language_code_rejects_invalid(self):
        """测试非法字符被拒绝"""
        assert sanitize_language_code("en/us") == "und"
        assert sanitize_language_code("zh;cn") == "und"
        assert sanitize_language_code("ja$") == "und"

    def test_sanitize_language_code_empty(self):
        """测试空字符串"""
        assert sanitize_language_code("") == "und"


class TestLanguagePriority:
    """测试字幕语言优先级排序"""

    def test_simplified_chinese_highest_priority(self):
        """测试简体中文拥有最高优先级（0）"""
        assert _get_language_priority("zh-hans") == 0
        assert _get_language_priority("zh-cn") == 0
        assert _get_language_priority("zh") == 0
        assert _get_language_priority("chs") == 0
        assert _get_language_priority("chi") == 0
        assert _get_language_priority("zho") == 0
        assert _get_language_priority("sc") == 0
        assert _get_language_priority("cn") == 0

    def test_traditional_chinese_second_priority(self):
        """测试繁体中文拥有第二优先级（1）"""
        assert _get_language_priority("zh-hant") == 1
        assert _get_language_priority("zh-tw") == 1
        assert _get_language_priority("zh-hk") == 1
        assert _get_language_priority("zh-mo") == 1
        assert _get_language_priority("cht") == 1
        assert _get_language_priority("tc") == 1
        assert _get_language_priority("tw") == 1
        assert _get_language_priority("hk") == 1

    def test_english_third_priority(self):
        """测试英文拥有第三优先级（2）"""
        assert _get_language_priority("en") == 2
        assert _get_language_priority("en-us") == 2
        assert _get_language_priority("en-gb") == 2
        assert _get_language_priority("en-au") == 2
        assert _get_language_priority("en-ca") == 2
        assert _get_language_priority("eng") == 2

    def test_other_languages_lowest_priority(self):
        """测试其他语言拥有最低优先级（999）"""
        assert _get_language_priority("ja") == 999
        assert _get_language_priority("ko") == 999
        assert _get_language_priority("fr") == 999
        assert _get_language_priority("de") == 999
        assert _get_language_priority("es") == 999
        assert _get_language_priority("unknown") == 999

    def test_case_insensitive(self):
        """测试优先级判断不区分大小写"""
        assert _get_language_priority("ZH-HANS") == 0
        assert _get_language_priority("Zh-Hant") == 1
        assert _get_language_priority("EN") == 2
        assert _get_language_priority("JA") == 999

    def test_sorting_order(self):
        """测试实际排序效果"""
        languages = ["ja", "en", "zh-hant", "ko", "zh-hans", "fr"]
        sorted_langs = sorted(languages, key=_get_language_priority)
        # 期望顺序：zh-hans, zh-hant, en, ja, ko, fr
        assert sorted_langs[0] == "zh-hans"  # 简体第一
        assert sorted_langs[1] == "zh-hant"  # 繁体第二
        assert sorted_langs[2] == "en"  # 英文第三
        # ja, ko, fr 顺序不变（都是 999）
        assert set(sorted_langs[3:]) == {"ja", "ko", "fr"}


class TestCollectFiles:
    """测试文件收集功能"""

    def test_collect_files_mixed(self, tmp_path):
        """测试收集混合文件"""
        # 创建测试文件
        (tmp_path / "video1.mp4").touch()
        (tmp_path / "video2.mkv").touch()
        (tmp_path / "subtitle1.srt").touch()
        (tmp_path / "subtitle2.ass").touch()
        (tmp_path / "readme.txt").touch()

        videos, subtitles = collect_files(tmp_path)

        assert len(videos) == 2
        assert len(subtitles) == 2
        assert all(v.suffix.lower() in ['.mp4', '.mkv'] for v in videos)
        assert all(s.suffix.lower() in ['.srt', '.ass'] for s in subtitles)

    def test_collect_files_only_videos(self, tmp_path):
        """测试只有视频文件"""
        (tmp_path / "video1.mp4").touch()
        (tmp_path / "video2.mkv").touch()

        videos, subtitles = collect_files(tmp_path)

        assert len(videos) == 2
        assert len(subtitles) == 0

    def test_collect_files_only_subtitles(self, tmp_path):
        """测试只有字幕文件"""
        (tmp_path / "subtitle1.srt").touch()
        (tmp_path / "subtitle2.ass").touch()

        videos, subtitles = collect_files(tmp_path)

        assert len(videos) == 0
        assert len(subtitles) == 2

    def test_collect_files_empty_directory(self, tmp_path):
        """测试空目录"""
        videos, subtitles = collect_files(tmp_path)

        assert len(videos) == 0
        assert len(subtitles) == 0

    def test_collect_files_sorted(self, tmp_path):
        """测试文件排序"""
        (tmp_path / "c.mp4").touch()
        (tmp_path / "a.mp4").touch()
        (tmp_path / "b.mp4").touch()

        videos, subtitles = collect_files(tmp_path)

        # 验证排序
        assert videos[0].name == "a.mp4"
        assert videos[1].name == "b.mp4"
        assert videos[2].name == "c.mp4"

    def test_collect_files_ignores_subdirectories(self, tmp_path):
        """测试忽略子目录"""
        (tmp_path / "video.mp4").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "video2.mp4").touch()

        videos, subtitles = collect_files(tmp_path)

        # 应该只收集顶层文件
        assert len(videos) == 1


class TestDisplayMatches:
    """测试匹配结果显示"""

    @patch('mkmkv_smart.cli.console')
    def test_display_matches_with_results(self, mock_console, tmp_path):
        """测试显示有结果的匹配"""
        from mkmkv_smart.normalizer import FileNormalizer

        video = tmp_path / "Movie.2024.mp4"
        lang_matches = {
            "zh-hans": MatchResult(
                subtitle_file="Movie.2024.zh-hans.srt",
                similarity=95.5,
                language_code="zh-hans"
            ),
            "en": MatchResult(
                subtitle_file="Movie.2024.en.srt",
                similarity=90.0,
                language_code="en"
            )
        }
        normalizer = FileNormalizer()

        display_matches(video, lang_matches, normalizer)

        # 验证调用了 print 方法
        assert mock_console.print.called

    @patch('mkmkv_smart.cli.console')
    def test_display_matches_no_results(self, mock_console, tmp_path):
        """测试显示无结果的匹配"""
        from mkmkv_smart.normalizer import FileNormalizer

        video = tmp_path / "Movie.2024.mp4"
        lang_matches = {}
        normalizer = FileNormalizer()

        display_matches(video, lang_matches, normalizer)

        # 验证显示了警告
        assert mock_console.print.called


class TestRunMatch:
    """测试主匹配流程"""

    @patch('mkmkv_smart.cli.MKVMerger')
    @patch('mkmkv_smart.cli.console')
    def test_run_match_dry_run(self, mock_console, mock_merger, tmp_path):
        """测试干运行模式"""
        # 创建测试文件
        (tmp_path / "Movie.2024.mp4").touch()
        (tmp_path / "Movie.2024.zh.srt").touch()

        # 创建模拟参数
        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = True
        args.threshold = None
        args.method = None
        args.config = None

        result = run_match(args, Config())

        # 干运行不应该调用 merger
        assert not mock_merger.called or not mock_merger.return_value.batch_merge.called
        assert result == 0

    @patch('mkmkv_smart.cli.MKVMerger')
    @patch('mkmkv_smart.cli.console')
    def test_run_match_nonexistent_directory(self, mock_console, mock_merger):
        """测试不存在的目录"""
        args = Mock()
        args.source = "/nonexistent/directory"
        args.output = None
        args.dry_run = False
        args.threshold = None
        args.method = None
        args.config = None

        result = run_match(args, Config())

        assert result == 1  # 应该返回错误代码

    @patch('mkmkv_smart.cli.MKVMerger')
    @patch('mkmkv_smart.cli.console')
    def test_run_match_no_videos(self, mock_console, mock_merger, tmp_path):
        """测试无视频文件"""
        # 只创建字幕文件
        (tmp_path / "subtitle.srt").touch()

        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = False
        args.threshold = None
        args.method = None
        args.config = None

        result = run_match(args, Config())

        assert result == 0  # 应该正常退出

    @patch('mkmkv_smart.cli.MKVMerger')
    @patch('mkmkv_smart.cli.SmartMatcher')
    @patch('mkmkv_smart.cli.console')
    def test_run_match_custom_threshold(self, mock_console, mock_matcher_class, mock_merger, tmp_path):
        """测试自定义阈值"""
        (tmp_path / "video.mp4").touch()

        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = True
        args.threshold = 50.0
        args.method = None
        args.config = None

        run_match(args, Config())

        # 验证使用了自定义阈值
        mock_matcher_class.assert_called_once()
        call_kwargs = mock_matcher_class.call_args[1]
        assert call_kwargs['threshold'] == 50.0

    @patch('mkmkv_smart.cli.MKVMerger')
    @patch('mkmkv_smart.cli.SmartMatcher')
    @patch('mkmkv_smart.cli.console')
    def test_run_match_custom_method(self, mock_console, mock_matcher_class, mock_merger, tmp_path):
        """测试自定义匹配方法"""
        (tmp_path / "video.mp4").touch()

        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = True
        args.threshold = None
        args.method = 'token_set'
        args.config = None

        run_match(args, Config())

        # 验证使用了自定义方法
        mock_matcher_class.assert_called_once()
        call_kwargs = mock_matcher_class.call_args[1]
        assert call_kwargs['method'] == 'token_set'

    @patch('mkmkv_smart.cli.MKVMerger')
    @patch('mkmkv_smart.cli.console')
    def test_run_match_with_config_file(self, mock_console, mock_merger, tmp_path):
        """测试使用配置文件"""
        import yaml

        # 创建配置文件
        config_file = tmp_path / "config.yaml"
        config_data = {
            'match': {'threshold': 40.0, 'method': 'token_sort'},
            'language': {'priority': ['en', 'zh']},
            'output': {}
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        (tmp_path / "video.mp4").touch()

        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = True
        args.threshold = None
        args.method = None
        args.config = str(config_file)

        result = run_match(args, Config())

        assert result == 0

    @patch('mkmkv_smart.cli.console')
    def test_run_match_with_output_directory(self, mock_console, tmp_path):
        """测试指定输出目录"""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        output_dir.mkdir()

        (source_dir / "video.mp4").touch()
        (source_dir / "video.zh.srt").touch()

        args = Mock()
        args.source = str(source_dir)
        args.output = str(output_dir)
        args.dry_run = True
        args.threshold = None
        args.method = None
        args.config = None

        result = run_match(args, Config())

        assert result == 0


class TestMain:
    """测试主入口函数"""

    @patch('mkmkv_smart.cli.run_match')
    def test_main_with_minimal_args(self, mock_run_match, tmp_path):
        """测试最小参数"""
        mock_run_match.return_value = 0

        with patch('sys.argv', ['mkmkv-smart', str(tmp_path)]):
            result = main()

        assert result == 0
        assert mock_run_match.called

    @patch('mkmkv_smart.cli.run_match')
    def test_main_with_all_args(self, mock_run_match, tmp_path):
        """测试所有参数"""
        mock_run_match.return_value = 0

        # 创建临时配置文件
        config_file = tmp_path / "config.yaml"
        Config().save(str(config_file))

        with patch('sys.argv', [
            'mkmkv-smart',
            str(tmp_path),
            str(tmp_path / 'output'),
            '--dry-run',
            '--threshold', '50',
            '--method', 'token_set',
            '--config', str(config_file)
        ]):
            result = main()

        assert result == 0
        assert mock_run_match.called

    @patch('mkmkv_smart.cli.run_match')
    def test_main_keyboard_interrupt(self, mock_run_match, tmp_path):
        """测试键盘中断"""
        mock_run_match.side_effect = KeyboardInterrupt()

        with patch('sys.argv', ['mkmkv-smart', str(tmp_path)]):
            result = main()

        assert result == 130  # 键盘中断退出码

    @patch('mkmkv_smart.cli.run_match')
    def test_main_exception(self, mock_run_match, tmp_path):
        """测试异常处理"""
        mock_run_match.side_effect = Exception("Test error")

        with patch('sys.argv', ['mkmkv-smart', str(tmp_path)]):
            result = main()

        assert result == 1  # 错误退出码

    def test_main_help(self, capsys):
        """测试帮助信息"""
        with patch('sys.argv', ['mkmkv-smart', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "智能视频字幕合并工具" in captured.out

    def test_main_version(self, capsys):
        """测试版本信息"""
        from mkmkv_smart import __version__

        with patch('sys.argv', ['mkmkv-smart', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert __version__ in captured.out


class TestCLIIntegration:
    """测试命令行集成场景"""

    @patch('mkmkv_smart.merger.shutil.which')
    @patch('mkmkv_smart.merger.subprocess.run')
    def test_full_workflow_dry_run(self, mock_run, mock_which, tmp_path):
        """测试完整工作流（干运行）"""
        mock_which.return_value = "/usr/bin/mkvmerge"
        mock_run.return_value = Mock(returncode=0)

        # 创建测试文件
        (tmp_path / "Movie.2024.1080p.mp4").touch()
        (tmp_path / "Movie.2024.zh-hans.srt").touch()
        (tmp_path / "Movie.2024.en.srt").touch()

        with patch('sys.argv', [
            'mkmkv-smart',
            str(tmp_path),
            '--dry-run'
        ]):
            result = main()

        assert result == 0

    @patch('mkmkv_smart.merger.shutil.which')
    def test_multiple_videos_and_subtitles(self, mock_which, tmp_path):
        """测试多个视频和字幕"""
        mock_which.return_value = "/usr/bin/mkvmerge"

        # 创建多个视频和字幕
        (tmp_path / "Movie.A.2024.mp4").touch()
        (tmp_path / "Movie.B.2024.mp4").touch()
        (tmp_path / "Movie.A.2024.zh.srt").touch()
        (tmp_path / "Movie.A.2024.en.srt").touch()
        (tmp_path / "Movie.B.2024.zh.srt").touch()

        with patch('sys.argv', [
            'mkmkv-smart',
            str(tmp_path),
            '--dry-run'
        ]):
            result = main()

        assert result == 0

    @patch('mkmkv_smart.merger.shutil.which')
    def test_series_episodes(self, mock_which, tmp_path):
        """测试剧集"""
        mock_which.return_value = "/usr/bin/mkvmerge"

        # 创建剧集文件
        (tmp_path / "Series.S01E01.mp4").touch()
        (tmp_path / "Series.S01E02.mp4").touch()
        (tmp_path / "Series.S01E01.zh.srt").touch()
        (tmp_path / "Series.S01E02.zh.srt").touch()

        with patch('sys.argv', [
            'mkmkv-smart',
            str(tmp_path),
            '--dry-run',
            '--threshold', '30'
        ]):
            result = main()

        assert result == 0


class TestEdgeCases:
    """测试边界情况"""

    @patch('mkmkv_smart.cli.console')
    def test_run_match_unicode_filenames(self, mock_console, tmp_path):
        """测试 Unicode 文件名"""
        (tmp_path / "电影.2024.mp4").touch()
        (tmp_path / "电影.2024.简体中文.srt").touch()

        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = True
        args.threshold = None
        args.method = None
        args.config = None

        result = run_match(args, Config())

        assert result == 0

    @patch('mkmkv_smart.cli.console')
    def test_run_match_special_characters(self, mock_console, tmp_path):
        """测试特殊字符文件名"""
        (tmp_path / "Movie (2024) [1080p].mp4").touch()
        (tmp_path / "Movie (2024) [zh-hans].srt").touch()

        args = Mock()
        args.source = str(tmp_path)
        args.output = None
        args.dry_run = True
        args.threshold = None
        args.method = None
        args.config = None

        result = run_match(args, Config())

        assert result == 0
