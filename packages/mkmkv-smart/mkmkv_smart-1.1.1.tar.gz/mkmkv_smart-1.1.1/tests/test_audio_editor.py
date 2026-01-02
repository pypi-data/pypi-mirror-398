"""
测试 MKV 音轨元数据编辑模块
"""

import json
import os
import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

from mkmkv_smart.audio_editor import (
    AudioTrackEditor,
    convert_to_ietf_tag,
    convert_to_iso639_2,
    get_language_name,
    UNDEFINED_LANGUAGE,
)
from mkmkv_smart.security_utils import (
    _safe_path_arg,
    _validate_output_path,
)


class TestConvertToIETFTag:
    """测试 IETF BCP-47 标签转换"""

    def test_simple_language_codes(self):
        """测试简单语言代码的默认映射"""
        assert convert_to_ietf_tag('zh') == 'zh-Hans'
        assert convert_to_ietf_tag('en') == 'en-US'
        assert convert_to_ietf_tag('ja') == 'ja-JP'
        assert convert_to_ietf_tag('ko') == 'ko-KR'
        assert convert_to_ietf_tag('fr') == 'fr-FR'
        assert convert_to_ietf_tag('de') == 'de-DE'

    def test_extended_language_codes(self):
        """测试扩展语言代码的规范化"""
        # 简体中文
        assert convert_to_ietf_tag('zh-hans') == 'zh-Hans'
        assert convert_to_ietf_tag('zh-Hans') == 'zh-Hans'
        assert convert_to_ietf_tag('ZH-HANS') == 'zh-Hans'

        # 繁体中文
        assert convert_to_ietf_tag('zh-hant') == 'zh-Hant'
        assert convert_to_ietf_tag('zh-Hant') == 'zh-Hant'

        # 地区代码
        assert convert_to_ietf_tag('en-gb') == 'en-GB'
        assert convert_to_ietf_tag('en-GB') == 'en-GB'
        assert convert_to_ietf_tag('zh-cn') == 'zh-CN'
        assert convert_to_ietf_tag('zh-tw') == 'zh-TW'

    def test_complex_tags(self):
        """测试复杂的 IETF 标签"""
        # Script + Region
        assert convert_to_ietf_tag('zh-hans-cn') == 'zh-Hans-CN'
        assert convert_to_ietf_tag('zh-hant-tw') == 'zh-Hant-TW'

    def test_empty_input(self):
        """测试空输入"""
        assert convert_to_ietf_tag('') == ''
        assert convert_to_ietf_tag(None) == ''

    def test_unknown_language(self):
        """测试未知语言代码"""
        # 未在映射表中的语言代码直接返回
        assert convert_to_ietf_tag('xyz') == 'xyz'


class TestConvertToISO6392:
    """测试 ISO 639-2 转换"""

    def test_iso639_1_conversion(self):
        """测试 ISO 639-1 (2字母) 到 ISO 639-2 (3字母) 的转换"""
        assert convert_to_iso639_2('zh') == 'chi'
        assert convert_to_iso639_2('en') == 'eng'
        assert convert_to_iso639_2('ja') == 'jpn'
        assert convert_to_iso639_2('ko') == 'kor'
        assert convert_to_iso639_2('fr') == 'fre'

    def test_iso639_1_new_mappings(self):
        """测试 P2-2 新增的 ISO 639-1 映射"""
        # P2-2: 新增的 5 个映射，防止 langdetect 结果被错误映射为 'und'
        assert convert_to_iso639_2('id') == 'ind'  # 印尼语
        assert convert_to_iso639_2('ms') == 'may'  # 马来语
        assert convert_to_iso639_2('fa') == 'per'  # 波斯语
        assert convert_to_iso639_2('he') == 'heb'  # 希伯来语
        assert convert_to_iso639_2('tl') == 'tgl'  # 他加禄语

    def test_extended_language_codes(self):
        """测试扩展语言代码（提取基础代码）"""
        assert convert_to_iso639_2('zh-hans') == 'chi'
        assert convert_to_iso639_2('zh-hant') == 'chi'
        assert convert_to_iso639_2('en-us') == 'eng'
        assert convert_to_iso639_2('en-gb') == 'eng'

    def test_iso639_3_special_mapping(self):
        """测试 ISO 639-3 特殊映射（中文方言）"""
        assert convert_to_iso639_2('yue') == 'chi'  # 粤语
        assert convert_to_iso639_2('wuu') == 'chi'  # 吴语
        assert convert_to_iso639_2('nan') == 'chi'  # 闽南语

    def test_iso639_3_bcp47_mapping(self):
        """测试 ISO 639-3 方言代码的 BCP-47 形式（应映射到 ISO 639-2）"""
        assert convert_to_iso639_2('yue-hk') == 'chi'  # 粤语（香港）→ 中文
        assert convert_to_iso639_2('wuu-cn') == 'chi'  # 吴语（中国）→ 中文
        assert convert_to_iso639_2('nan-tw') == 'chi'  # 闽南语（台湾）→ 中文

    def test_three_letter_base_bcp47(self):
        """测试三字母基础的 BCP-47 标签"""
        assert convert_to_iso639_2('fil-ph') == 'fil'  # 菲律宾语（菲律宾）
        assert convert_to_iso639_2('ind-id') == 'ind'  # 印尼语（印尼）

    def test_unmapped_three_letter_bcp47(self):
        """测试未映射的三字母基础 BCP-47 标签（保持一致性）"""
        # 应该直接传递三字母代码，而不是返回 'und'
        assert convert_to_iso639_2('ast-es') == 'ast'  # 阿斯图里亚斯语
        assert convert_to_iso639_2('eus-es') == 'eus'  # 巴斯克语

    def test_already_iso639_2(self):
        """测试已经是 ISO 639-2 的代码"""
        assert convert_to_iso639_2('eng') == 'eng'
        assert convert_to_iso639_2('jpn') == 'jpn'
        assert convert_to_iso639_2('chi') == 'chi'

    def test_unknown_language(self):
        """测试未知语言"""
        assert convert_to_iso639_2('unknown') == 'und'
        assert convert_to_iso639_2('xy') == 'und'


class TestAudioTrackEditor:
    """测试 AudioTrackEditor 类"""

    @patch('shutil.which')
    def test_initialization_success(self, mock_which):
        """测试成功初始化"""
        mock_which.return_value = '/usr/bin/mkvpropedit'

        editor = AudioTrackEditor()
        assert editor.mkvpropedit_path == 'mkvpropedit'

    @patch('shutil.which')
    def test_initialization_failure(self, mock_which):
        """测试 mkvpropedit 不可用时初始化失败"""
        mock_which.return_value = None

        with pytest.raises(RuntimeError, match="mkvpropedit 未安装"):
            AudioTrackEditor()

    @patch('shutil.which')
    def test_is_mkvpropedit_available(self, mock_which):
        """测试检查 mkvpropedit 是否可用"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_which.return_value = None
        assert editor.is_mkvpropedit_available() is False

        mock_which.return_value = '/usr/bin/mkvpropedit'
        assert editor.is_mkvpropedit_available() is True

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_set_audio_track_language_success(self, mock_run, mock_which):
        """测试成功设置音轨语言"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        # 创建临时 MKV 文件
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name
            f.write(b"fake mkv data")

        try:
            # 模拟成功的 mkvpropedit 调用
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            result = editor.set_audio_track_language(
                mkv_file,
                track_index=0,
                language_code='jpn',
                track_name='日本語'
            )

            assert result is True

            # 验证调用参数
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert 'mkvpropedit' in call_args
            assert '--edit' in call_args
            assert 'track:a1' in call_args
            assert '--set' in call_args
            assert 'language=jpn' in call_args
            # 注意：convert_to_ietf_tag('jpn') 会返回 'jpn'（3字母代码不在映射表中）
            assert 'language-ietf=jpn' in call_args
            assert 'name=日本語' in call_args

        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_set_audio_track_language_with_original_code(self, mock_run, mock_which):
        """测试 P2-3: 使用 original_code 参数生成准确的 IETF 标签"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        # 创建临时 MKV 文件
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name
            f.write(b"fake mkv data")

        try:
            # 模拟成功的 mkvpropedit 调用
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            # 测试：原始检测代码是 'ja'（ISO 639-1），转换为 'jpn'（ISO 639-2）
            # IETF 标签应该从原始代码 'ja' 生成为 'ja-JP'，而非从 'jpn' 生成
            result = editor.set_audio_track_language(
                mkv_file,
                track_index=0,
                language_code='jpn',  # ISO 639-2
                track_name='日本語',
                original_code='ja'  # 原始 ISO 639-1 代码
            )

            assert result is True

            # 验证调用参数
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert 'language=jpn' in call_args
            # 关键验证：IETF 标签应该从 'ja' 生成，而非 'jpn'
            # convert_to_ietf_tag('ja') → 'ja-JP'
            assert 'language-ietf=ja-JP' in call_args
            assert 'name=日本語' in call_args

        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    def test_set_audio_track_language_invalid_index(self, mock_which):
        """测试无效的音轨索引"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name

        try:
            result = editor.set_audio_track_language(mkv_file, track_index=-1, language_code='eng')
            assert result is False
        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    def test_set_audio_track_language_nonexistent_file(self, mock_which):
        """测试设置不存在文件的音轨"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        result = editor.set_audio_track_language(
            '/nonexistent/file.mkv',
            track_index=0,
            language_code='eng'
        )
        assert result is False

    @patch('shutil.which')
    def test_set_audio_track_language_non_mkv_file(self, mock_which):
        """测试设置非 MKV 文件的音轨"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            mp4_file = f.name

        try:
            result = editor.set_audio_track_language(mp4_file, track_index=0, language_code='eng')
            assert result is False
        finally:
            Path(mp4_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_set_audio_track_language_timeout(self, mock_run, mock_which):
        """测试音轨设置超时"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name

        try:
            mock_run.side_effect = subprocess.TimeoutExpired('mkvpropedit', 60)

            result = editor.set_audio_track_language(mkv_file, track_index=0, language_code='eng')
            assert result is False
        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_set_subtitle_track_language_success(self, mock_run, mock_which):
        """测试成功设置字幕语言"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name
            f.write(b"fake mkv data")

        try:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            result = editor.set_subtitle_track_language(
                mkv_file,
                track_index=0,
                language_code='eng',
                track_name='English'
            )

            assert result is True

            # 验证调用参数
            call_args = mock_run.call_args[0][0]
            assert '--edit' in call_args
            assert 'track:s1' in call_args  # 字幕轨道
            assert 'language=eng' in call_args

        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_set_subtitle_track_language_with_original_code(self, mock_run, mock_which):
        """测试 P2-3: 字幕轨道使用 original_code 参数生成准确的 IETF 标签"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name
            f.write(b"fake mkv data")

        try:
            mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

            # 测试：原始检测代码是 'en'（ISO 639-1），转换为 'eng'（ISO 639-2）
            # IETF 标签应该从原始代码 'en' 生成为 'en-US'，而非从 'eng' 生成
            result = editor.set_subtitle_track_language(
                mkv_file,
                track_index=0,
                language_code='eng',  # ISO 639-2
                track_name='English',
                original_code='en'  # 原始 ISO 639-1 代码
            )

            assert result is True

            # 验证调用参数
            call_args = mock_run.call_args[0][0]
            assert 'language=eng' in call_args
            # 关键验证：IETF 标签应该从 'en' 生成，而非 'eng'
            # convert_to_ietf_tag('en') → 'en-US'
            assert 'language-ietf=en-US' in call_args
            assert 'name=English' in call_args

        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_audio_tracks_info_success(self, mock_run, mock_which):
        """测试成功获取音轨信息"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        # 模拟 mkvmerge -J 的 JSON 输出
        mock_json_output = {
            "tracks": [
                {
                    "id": 0,
                    "type": "video",
                    "codec": "V_MPEG4/ISO/AVC"
                },
                {
                    "id": 1,
                    "type": "audio",
                    "codec": "A_AAC",
                    "properties": {
                        "language": "jpn",
                        "track_name": "日本語"
                    }
                },
                {
                    "id": 2,
                    "type": "audio",
                    "codec": "A_AAC",
                    "properties": {
                        "language": "eng"
                    }
                }
            ]
        }

        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(mock_json_output),
            stderr=''
        )

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name

        try:
            tracks = editor.get_audio_tracks_info(mkv_file)

            assert len(tracks) == 2
            assert tracks[0]['track_id'] == 1
            assert tracks[0]['codec'] == 'A_AAC'
            assert tracks[0]['language'] == 'jpn'
            assert tracks[0]['track_name'] == '日本語'

            assert tracks[1]['track_id'] == 2
            assert tracks[1]['language'] == 'eng'
            assert tracks[1]['track_name'] == ''

        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_audio_tracks_info_no_tracks(self, mock_run, mock_which):
        """测试获取没有音轨的文件信息"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_json_output = {"tracks": []}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(mock_json_output),
            stderr=''
        )

        with tempfile.NamedTemporaryFile(suffix='.mkv') as f:
            tracks = editor.get_audio_tracks_info(f.name)
            assert tracks == []

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_audio_tracks_info_json_error(self, mock_run, mock_which):
        """测试 JSON 解析错误"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_run.return_value = Mock(
            returncode=0,
            stdout='invalid json',
            stderr=''
        )

        with tempfile.NamedTemporaryFile(suffix='.mkv') as f:
            tracks = editor.get_audio_tracks_info(f.name)
            assert tracks == []

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_get_subtitle_tracks_info_success(self, mock_run, mock_which):
        """测试成功获取字幕轨道信息"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_json_output = {
            "tracks": [
                {
                    "id": 3,
                    "type": "subtitles",
                    "codec": "SubRip/SRT",
                    "properties": {
                        "language": "eng",
                        "track_name": "English"
                    }
                },
                {
                    "id": 4,
                    "type": "subtitles",
                    "codec": "SubRip/SRT",
                    "properties": {
                        "language": "und"
                    }
                }
            ]
        }

        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(mock_json_output),
            stderr=''
        )

        with tempfile.NamedTemporaryFile(suffix='.mkv') as f:
            tracks = editor.get_subtitle_tracks_info(f.name)

            assert len(tracks) == 2
            assert tracks[0]['track_id'] == 3
            assert tracks[0]['language'] == 'eng'
            assert tracks[0]['track_name'] == 'English'

            assert tracks[1]['track_id'] == 4
            assert tracks[1]['language'] == 'und'

    def test_get_subtitle_suffix(self):
        """测试字幕文件扩展名判断"""
        assert AudioTrackEditor._get_subtitle_suffix('SubRip/SRT') == '.srt'
        assert AudioTrackEditor._get_subtitle_suffix('SubStationAlpha') == '.ass'
        assert AudioTrackEditor._get_subtitle_suffix('S_TEXT/ASS') == '.ass'
        assert AudioTrackEditor._get_subtitle_suffix('S_TEXT/WEBVTT') == '.vtt'
        assert AudioTrackEditor._get_subtitle_suffix('S_TEXT/SSA') == '.ass'
        assert AudioTrackEditor._get_subtitle_suffix(None) == '.srt'
        assert AudioTrackEditor._get_subtitle_suffix('') == '.srt'
        assert AudioTrackEditor._get_subtitle_suffix('Unknown') == '.srt'

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_extract_subtitle_content_success(self, mock_run, mock_which):
        """测试成功提取字幕内容"""
        mock_which.side_effect = lambda x: '/usr/bin/mkvextract' if x == 'mkvextract' else '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name
            f.write(b"fake mkv data")

        try:
            result = editor.extract_subtitle_content(mkv_file, track_id=3, codec='SubRip/SRT')

            assert result is not None
            assert result.endswith('.srt')

            # 验证调用
            call_args = mock_run.call_args[0][0]
            assert 'mkvextract' in call_args
            assert 'tracks' in call_args
            assert '3:' in str(call_args)

            # 清理临时文件
            if os.path.exists(result):
                os.remove(result)

        finally:
            Path(mkv_file).unlink()

    @patch('shutil.which')
    def test_extract_subtitle_content_mkvextract_not_found(self, mock_which):
        """测试 mkvextract 不可用"""
        mock_which.side_effect = lambda x: None if x == 'mkvextract' else '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mkv') as f:
            result = editor.extract_subtitle_content(f.name, track_id=3)
            assert result is None

    @patch('shutil.which')
    def test_extract_subtitle_content_nonexistent_file(self, mock_which):
        """测试提取不存在文件的字幕"""
        mock_which.side_effect = lambda x: '/usr/bin/' + x
        editor = AudioTrackEditor()

        result = editor.extract_subtitle_content('/nonexistent/file.mkv', track_id=3)
        assert result is None

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_extract_subtitle_content_timeout(self, mock_run, mock_which):
        """测试字幕提取超时"""
        mock_which.side_effect = lambda x: '/usr/bin/' + x
        editor = AudioTrackEditor()

        mock_run.side_effect = subprocess.TimeoutExpired('mkvextract', 120)

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f:
            mkv_file = f.name

        try:
            result = editor.extract_subtitle_content(mkv_file, track_id=3)
            assert result is None
        finally:
            Path(mkv_file).unlink()

    def test_should_process_subtitle_track(self):
        """测试字幕轨道过滤逻辑"""
        mock_which_patcher = patch('shutil.which', return_value='/usr/bin/mkvpropedit')
        mock_which_patcher.start()

        try:
            editor = AudioTrackEditor()

            # 应该处理：语言为 und，没有轨道名称
            track1 = {
                'language': 'und',
                'track_name': '',
                'codec': 'SubRip/SRT'
            }
            assert editor._should_process_subtitle_track(track1) is True

            # 应该处理：文本字幕，有语言有名称（新逻辑：只判断格式）
            track2 = {
                'language': 'eng',
                'track_name': 'English',
                'codec': 'SubRip/SRT'
            }
            assert editor._should_process_subtitle_track(track2) is True

            # 应该处理：有语言但没有名称
            track3 = {
                'language': 'eng',
                'track_name': '',
                'codec': 'SubRip/SRT'
            }
            assert editor._should_process_subtitle_track(track3) is True

            # 不应该处理：图形字幕（PGS）
            track4 = {
                'language': 'und',
                'track_name': '',
                'codec': 'S_HDMV/PGS'
            }
            assert editor._should_process_subtitle_track(track4) is False

            # 应该处理：WebVTT 格式
            track5 = {
                'language': 'und',
                'track_name': '',
                'codec': 'S_TEXT/WEBVTT'
            }
            assert editor._should_process_subtitle_track(track5) is True

            # P1 测试：不应该处理 - 缺少 codec
            track6 = {
                'language': 'und',
                'track_name': ''
            }
            assert editor._should_process_subtitle_track(track6) is False

            # P1 测试：不应该处理 - codec 为 None
            track7 = {
                'language': 'und',
                'track_name': '',
                'codec': None
            }
            assert editor._should_process_subtitle_track(track7) is False

        finally:
            mock_which_patcher.stop()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_convert_to_mkv_with_language_success(self, mock_run, mock_which):
        """测试成功转换视频为 MKV"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            input_file = f.name
            f.write(b"fake video data")

        output_file = input_file.replace('.mp4', '.mkv')

        try:
            result = editor.convert_to_mkv_with_language(
                input_file,
                output_file,
                audio_track_index=0,
                language_code='jpn',
                track_name='日本語'
            )

            assert result is True

            # 验证调用参数
            call_args = mock_run.call_args[0][0]
            assert 'mkvmerge' in call_args
            assert '-o' in call_args
            assert '--language' in call_args
            assert 'a0:jpn' in call_args
            assert '--track-name' in call_args

        finally:
            Path(input_file).unlink()
            if Path(output_file).exists():
                Path(output_file).unlink()

    @patch('shutil.which')
    def test_convert_to_mkv_same_input_output(self, mock_which):
        """测试输入输出文件相同时拒绝转换"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            same_file = f.name

        try:
            result = editor.convert_to_mkv_with_language(
                same_file,
                same_file,
                audio_track_index=0,
                language_code='eng'
            )
            assert result is False
        finally:
            Path(same_file).unlink()

    @patch('shutil.which')
    def test_convert_to_mkv_output_exists(self, mock_which):
        """测试输出文件已存在时拒绝转换"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f1:
            input_file = f1.name

        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as f2:
            output_file = f2.name

        try:
            result = editor.convert_to_mkv_with_language(
                input_file,
                output_file,
                audio_track_index=0,
                language_code='eng'
            )
            assert result is False
        finally:
            Path(input_file).unlink()
            Path(output_file).unlink()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_convert_to_mkv_with_language_timeout(self, mock_run, mock_which):
        """测试转换超时"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        mock_run.side_effect = subprocess.TimeoutExpired('mkvmerge', 120)

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            input_file = f.name

        output_file = input_file.replace('.mp4', '.mkv')

        try:
            result = editor.convert_to_mkv_with_language(
                input_file,
                output_file,
                audio_track_index=0,
                language_code='eng'
            )
            assert result is False
        finally:
            Path(input_file).unlink()
            # 超时后应该清理输出文件
            assert not Path(output_file).exists()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_cleanup_failed_output(self, mock_run, mock_which):
        """测试失败时清理输出文件"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        # 创建一个会被 mkvmerge 创建的临时输出文件
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as output:
            output_file = output.name
            output.write(b"partial output")

        # 模拟 mkvmerge 失败
        mock_run.side_effect = subprocess.CalledProcessError(1, 'mkvmerge')

        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            input_file = f.name

        try:
            result = editor.convert_to_mkv_with_language(
                input_file,
                output_file,
                audio_track_index=0,
                language_code='eng'
            )
            assert result is False
            # 输出文件应该被清理（如果不是预先存在的）
        finally:
            Path(input_file).unlink()
            if Path(output_file).exists():
                Path(output_file).unlink()


class TestGetLanguageName:
    """测试 get_language_name 函数"""

    def test_basic_language_codes(self):
        """测试基础语言代码"""
        # 这个函数导入自 language_utils，我们只测试它是否可调用
        result = get_language_name('zh')
        assert result is not None
        assert isinstance(result, str)

    def test_extended_language_codes(self):
        """测试扩展语言代码"""
        result = get_language_name('zh-hans')
        assert result is not None
        assert isinstance(result, str)


class TestSecurityFixes:
    """测试安全修复 (M1, M2, M3)"""

    def test_safe_path_arg_normal_path(self):
        """M1: 测试正常路径不被修改"""
        normal_paths = [
            Path("video.mkv"),
            Path("/tmp/video.mkv"),
            Path("./video.mkv"),
            Path("folder/video.mkv"),
        ]
        for path in normal_paths:
            result = _safe_path_arg(path)
            assert result == str(path)

    def test_safe_path_arg_dash_prefix(self):
        """M1: 测试以 - 开头的路径被安全化"""
        dangerous_paths = [
            Path("--output=evil.mkv"),
            Path("-map"),
            Path("-o"),
            Path("--delete-all"),
        ]
        for path in dangerous_paths:
            result = _safe_path_arg(path)
            # 应该添加 ./ 前缀
            assert result.startswith("./")
            assert result == f"./{str(path)}"

    def test_safe_path_arg_at_prefix(self):
        """M1: 测试以 @ 开头的路径被安全化（防止选项文件注入）"""
        dangerous_paths = [
            Path("@options.txt"),
            Path("@evil_commands"),
            Path("@/tmp/malicious"),
        ]
        for path in dangerous_paths:
            result = _safe_path_arg(path)
            # 应该添加 ./ 前缀
            assert result.startswith("./")
            assert result == f"./{str(path)}"


    def test_validate_output_path_safe_temp_dir(self, tmp_path):
        """M2: 测试临时目录内的路径验证通过"""
        # 临时目录内的文件应该通过验证
        safe_file = tmp_path / "output.srt"
        assert _validate_output_path(safe_file, tmp_path) is True

        # 子目录内的文件也应该通过
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        safe_file_in_subdir = sub_dir / "output.srt"
        assert _validate_output_path(safe_file_in_subdir, tmp_path) is True

    def test_validate_output_path_unsafe_paths(self, tmp_path):
        """M2: 测试危险路径被拒绝"""
        dangerous_paths = [
            Path("/etc/passwd"),
            Path("/tmp/../../etc/passwd"),
            Path("~/.ssh/authorized_keys"),
        ]

        for dangerous_path in dangerous_paths:
            result = _validate_output_path(dangerous_path, tmp_path)
            # 不在安全目录内，应该被拒绝
            assert result is False

    def test_validate_output_path_default_temp_dir(self):
        """M2: 测试默认使用系统临时目录"""
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        safe_file = temp_dir / "test_output.srt"

        # 使用默认参数（系统临时目录）
        assert _validate_output_path(safe_file) is True

        # 不在临时目录的文件应该被拒绝
        assert _validate_output_path(Path("/etc/passwd")) is False

    @patch('shutil.which')
    def test_extract_subtitle_validates_output_path(self, mock_which, tmp_path):
        """M2: 测试 extract_subtitle_content 验证输出路径"""
        mock_which.return_value = '/usr/bin/mkvpropedit'
        editor = AudioTrackEditor()

        # 创建测试视频文件
        video_file = tmp_path / "test.mkv"
        video_file.touch()

        # 尝试写入危险路径应该被拒绝
        dangerous_output = "/etc/passwd"
        result = editor.extract_subtitle_content(
            str(video_file),
            track_id=0,
            output_file=dangerous_output
        )

        # 应该返回 None（被拒绝）
        assert result is None
