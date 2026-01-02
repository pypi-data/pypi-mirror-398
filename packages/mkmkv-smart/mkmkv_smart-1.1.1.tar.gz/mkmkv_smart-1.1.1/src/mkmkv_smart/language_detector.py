"""
语言检测模块

使用 langdetect 自动识别字幕文件的语言
"""

import itertools
import logging
import re
from typing import Optional, Tuple
from pathlib import Path
from langdetect import detect_langs, LangDetectException, DetectorFactory

# 设置 langdetect 随机种子以确保结果的确定性
DetectorFactory.seed = 0

# 配置日志
logger = logging.getLogger(__name__)

# langdetect 语言代码标准化映射
LANG_CODE_MAP = {
    'zh-cn': 'zh-hans',  # 简体中文
    'zh-tw': 'zh-hant',  # 繁体中文
}


class LanguageDetector:
    """语言检测器"""

    def __init__(self, min_confidence: float = 0.8, min_chars: int = 100):
        """
        初始化语言检测器

        Args:
            min_confidence: 最小置信度阈值 (0.0-1.0)
            min_chars: 最小文本长度要求
        """
        self.min_confidence = min_confidence
        self.min_chars = min_chars

    def detect_subtitle_language(
        self, subtitle_file: str
    ) -> Optional[Tuple[str, float]]:
        """
        检测字幕文件的语言

        Args:
            subtitle_file: 字幕文件路径

        Returns:
            (语言代码, 置信度) 或 None
            语言代码格式: zh-hans, zh-hant, en, ja 等
        """
        subtitle_path = Path(subtitle_file)

        # 验证文件存在
        if not subtitle_path.is_file():
            return None

        # 支持 .srt, .ass, .ssa, .vtt 文件
        if subtitle_path.suffix.lower() not in ['.srt', '.ass', '.ssa', '.vtt']:
            return None

        try:
            # 读取字幕内容
            text = self._extract_subtitle_text(subtitle_path)

            if not text or len(text) < self.min_chars:
                return None

            # 检测语言
            langs = detect_langs(text)

            if not langs or langs[0].prob < self.min_confidence:
                return None

            main_lang = langs[0].lang
            confidence = langs[0].prob

            # 标准化语言代码（langdetect 可能返回 zh-cn, zh-tw 等）
            main_lang = LANG_CODE_MAP.get(main_lang, main_lang)

            # 对于东亚语言（中日韩），应用增强的中文检测逻辑（方案B）
            # 只有在满足以下所有条件时才覆盖为中文：
            # 1. 检测到足够多的中文特征字符
            # 2. 没有日文假名
            # 3. 没有韩文字符
            if main_lang in ['zh', 'zh-hans', 'zh-hant', 'ko', 'ja']:
                has_chinese = self._has_chinese_chars(text)
                has_kana = self._has_kana_chars(text)
                has_hangul = self._has_hangul_chars(text)

                # 如果有中文特征且无假名/韩文，强制识别为中文
                if has_chinese and not has_kana and not has_hangul:
                    chinese_variant = self._detect_chinese_variant(text)
                    return (chinese_variant, confidence)

                # 否则保持 langdetect 的原始判断
                # （例如：日文有汉字+假名，韩文有汉字+韩文）

            # 如果 langdetect 明确判断为中文，进一步区分简繁体
            if main_lang.startswith('zh'):
                variant = self._detect_chinese_variant(text)
                return (variant, confidence)

            return (main_lang, confidence)

        except LangDetectException as e:
            # langdetect 检测失败（文本不足或无法识别）
            logger.debug(
                f"语言检测失败 (LangDetectException): {subtitle_file}, {e}"
            )
            return None
        except Exception as e:
            # 其他异常
            logger.warning(
                f"语言检测时发生异常: {subtitle_file}, {e}", exc_info=True
            )
            return None

    def _extract_subtitle_text(self, subtitle_path: Path) -> str:
        """
        提取字幕文本内容

        Args:
            subtitle_path: 字幕文件路径

        Returns:
            合并后的字幕文本
        """
        if subtitle_path.suffix.lower() == '.srt':
            return self._extract_srt_text(subtitle_path)
        elif subtitle_path.suffix.lower() in ['.ass', '.ssa']:
            return self._extract_ass_text(subtitle_path)
        elif subtitle_path.suffix.lower() == '.vtt':
            return self._extract_vtt_text(subtitle_path)
        return ""

    def _extract_srt_text(self, srt_path: Path) -> str:
        """
        提取 SRT 字幕文本（优化版本，仅读取前 N 条）

        Args:
            srt_path: SRT 文件路径

        Returns:
            合并后的文本
        """
        max_entries = 100  # 最多读取的字幕条数
        max_chars = 5000   # 最多读取的字符数

        try:
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'big5', 'utf-16']:
                try:
                    texts = []
                    total_chars = 0
                    entry_count = 0

                    with open(srt_path, 'r', encoding=encoding) as f:
                        in_text_block = False
                        current_text = []

                        for line in f:
                            line = line.strip()

                            # 空行表示一个字幕块结束
                            if not line:
                                if current_text:
                                    text = ' '.join(current_text)
                                    texts.append(text)
                                    total_chars += len(text)
                                    current_text = []
                                    entry_count += 1
                                    in_text_block = False

                                    # 达到限制后停止
                                    if entry_count >= max_entries or total_chars >= max_chars:
                                        break
                                continue

                            # 跳过序号行（纯数字）
                            if line.isdigit() and not in_text_block:
                                continue

                            # 跳过时间戳行
                            if '-->' in line:
                                in_text_block = True
                                continue

                            # 收集字幕文本
                            if in_text_block:
                                current_text.append(line)

                        # 处理最后一个字幕块（文件无尾部空行时）
                        if current_text and entry_count < max_entries and total_chars < max_chars:
                            text = ' '.join(current_text)
                            texts.append(text)

                    return ' '.join(texts)

                except UnicodeDecodeError:
                    continue

            return ""
        except Exception as e:
            logger.debug(f"提取 SRT 字幕文本失败: {srt_path}, {e}")
            return ""

    def _extract_ass_text(self, ass_path: Path) -> str:
        """
        提取 ASS/SSA 字幕文本

        Args:
            ass_path: ASS/SSA 文件路径

        Returns:
            合并后的文本
        """
        try:
            # ASS/SSA 文件是文本格式，直接读取
            for encoding in ['utf-8', 'gbk', 'big5', 'utf-16']:
                try:
                    with open(ass_path, 'r', encoding=encoding) as f:
                        texts = []
                        total_chars = 0
                        max_lines = 200
                        max_chars = 5000

                        # 使用 itertools.islice 仅读取前 N 行
                        for line in itertools.islice(f, max_lines):
                            if line.startswith('Dialogue:'):
                                # ASS/SSA 格式: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
                                parts = line.split(',', 9)
                                if len(parts) >= 10:
                                    text = parts[9].strip()
                                    # 移除 ASS 标签 (如 {\pos(x,y)})
                                    text = re.sub(r'\{[^}]*\}', '', text)
                                    if text:
                                        texts.append(text)
                                        total_chars += len(text)
                                        # 达到字符数限制后停止
                                        if total_chars >= max_chars:
                                            break

                    return ' '.join(texts)
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception as e:
            logger.debug(f"提取 ASS/SSA 字幕文本失败: {ass_path}, {e}")
            return ""

    def _extract_vtt_text(self, vtt_path: Path) -> str:
        """
        提取 WebVTT 字幕文本

        Args:
            vtt_path: VTT 文件路径

        Returns:
            合并后的文本
        """
        try:
            # WebVTT 文件是文本格式，直接读取
            for encoding in ['utf-8', 'gbk', 'big5', 'utf-16']:
                try:
                    with open(vtt_path, 'r', encoding=encoding) as f:
                        texts = []
                        total_chars = 0
                        max_lines = 200
                        max_chars = 5000
                        in_cue = False  # 是否在字幕块内

                        # 使用 itertools.islice 仅读取前 N 行
                        for line in itertools.islice(f, max_lines):
                            line = line.strip()

                            # 跳过空行
                            if not line:
                                in_cue = False
                                continue

                            # 跳过 WEBVTT 头
                            if line.startswith('WEBVTT'):
                                continue

                            # 跳过元数据块（NOTE, STYLE, REGION 等）
                            if line.startswith(('NOTE', 'STYLE', 'REGION', 'X-TIMESTAMP-MAP')):
                                continue

                            # 检测时间戳行（格式: 00:00:00.000 --> 00:00:05.000）
                            if '-->' in line:
                                in_cue = True
                                continue

                            # 跳过 cue identifier（纯数字行，但只在不在 cue 块内时跳过）
                            # 注意：cue 块内的纯数字是字幕文本，不应跳过
                            if line.isdigit() and not in_cue:
                                continue

                            # 提取字幕文本（只有在 cue 块内的非时间戳行才是文本）
                            if in_cue:
                                # 移除 WebVTT 标签 (如 <v Speaker>, <c.classname>)
                                text = re.sub(r'<[^>]*>', '', line)
                                if text:
                                    texts.append(text)
                                    total_chars += len(text)
                                    # 达到字符数限制后停止
                                    if total_chars >= max_chars:
                                        break

                    return ' '.join(texts)
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception as e:
            logger.debug(f"提取 VTT 字幕文本失败: {vtt_path}, {e}")
            return ""

    def _detect_chinese_variant(self, text: str) -> str:
        """
        区分简体/繁体中文

        Args:
            text: 中文文本

        Returns:
            'zh-hans' (简体) 或 'zh-hant' (繁体)
        """
        # 简体特征字 (常用且简繁差异明显的字)
        simplified_chars = set(
            '个为临书买乱习关压厅发听园国图'
            '务动劳势厂历华协变态总处梦电'
            '爱写万与专业严两丰举乐主买乡'
        )

        # 繁体特征字
        traditional_chars = set(
            '個為臨書買亂習關壓廳發聽園國圖'
            '務動勞勢廠歷華協變態總處夢電'
            '愛寫萬與專業嚴兩豐舉樂主買鄉'
        )

        simplified_count = sum(1 for c in text if c in simplified_chars)
        traditional_count = sum(1 for c in text if c in traditional_chars)

        # 繁体特征明显 (繁体特征字数量 > 简体 * 1.5)
        if traditional_count > simplified_count * 1.5 and traditional_count > 0:
            return 'zh-hant'

        # 默认简体 (大多数中文内容是简体)
        return 'zh-hans'

    def _has_chinese_chars(self, text: str) -> bool:
        """
        检查文本是否包含中文字符（区分中文和日文）

        Args:
            text: 待检查文本

        Returns:
            如果包含足够多的中文特征字符返回 True
        """
        # 中文特征字集合（简体+繁体）
        chinese_chars = set(
            '个为临书买乱习关压厅发听园国图'
            '务动劳势厂历华协变态总处梦电'
            '爱写万与专业严两丰举乐主买乡'
            '個為臨書買亂習關壓廳發聽園國圖'
            '務動勞勢廠歷華協變態總處夢電'
            '愛寫萬與專業嚴兩豐舉樂主買鄉'
            '的了在是我有个这上们来不和人你说他一'  # 高频常用字
        )

        # 计算中文特征字数量
        chinese_count = sum(1 for c in text if c in chinese_chars)

        # 如果中文特征字数量 >= 5，认为是中文
        # （日文虽然使用汉字，但很少包含这些中文特有的高频字）
        return chinese_count >= 5

    def _has_kana_chars(self, text: str) -> bool:
        """
        检查文本是否包含日文假名（平假名或片假名）

        Args:
            text: 待检查文本

        Returns:
            如果包含日文假名字符返回 True
        """
        # Unicode 范围：
        # 平假名: U+3040 - U+309F
        # 片假名: U+30A0 - U+30FF
        for char in text:
            code_point = ord(char)
            if (0x3040 <= code_point <= 0x309F) or (0x30A0 <= code_point <= 0x30FF):
                return True
        return False

    def _has_hangul_chars(self, text: str) -> bool:
        """
        检查文本是否包含韩文字符

        Args:
            text: 待检查文本

        Returns:
            如果包含韩文字符返回 True
        """
        # Unicode 范围：
        # 韩文音节: U+AC00 - U+D7AF
        # 韩文字母: U+1100 - U+11FF, U+3130 - U+318F, U+A960 - U+A97F
        for char in text:
            code_point = ord(char)
            if ((0xAC00 <= code_point <= 0xD7AF) or
                (0x1100 <= code_point <= 0x11FF) or
                (0x3130 <= code_point <= 0x318F) or
                (0xA960 <= code_point <= 0xA97F)):
                return True
        return False


def detect_subtitle_language(subtitle_file: str) -> Optional[Tuple[str, float]]:
    """
    便捷函数：检测字幕文件语言

    Args:
        subtitle_file: 字幕文件路径

    Returns:
        (语言代码, 置信度) 或 None
    """
    detector = LanguageDetector()
    return detector.detect_subtitle_language(subtitle_file)
