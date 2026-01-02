"""
文件名规范化模块

负责清理视频和字幕文件名中的无关标签，提取核心信息用于匹配。
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple


class FileNormalizer:
    """文件名规范化器"""

    # 默认需要过滤的视频标签
    DEFAULT_VIDEO_TAGS = [
        # 分辨率
        r'\b(1080p|720p|2160p|4k|480p|576p|uhd|fhd|hd)\b',
        # 来源
        r'\b(bluray|blu-ray|bdrip|brrip|web-dl|webrip|hdtv|dvdrip|remux|dvd|web)\b',
        # 编码器
        r'\b(x264|x265|h264|h265|hevc|avc|xvid|divx|vc-1|vp9|av1)\b',
        # 音频
        r'\b(aac|ac3|dts|flac|mp3|eac3|truehd|atmos|dd|dts-hd)\b',
        # 音频声道
        r'\b(5\.1|7\.1|2\.0|stereo|mono)\b',
        # 色深
        r'\b(10bit|8bit|10-bit|8-bit)\b',
        # 发布组标签
        r'\b(internal|proper|repack|extended|unrated|directors\.cut|dc|theatrical)\b',
        # HDR 相关
        r'\b(hdr|hdr10|dolby\.?vision|dv|sdr)\b',
        # 编码组
        r'\[[^]]*\]',  # 方括号内容（避免回溯开销）
        r'\{[^}]*\}',  # 花括号内容（避免回溯开销）
    ]

    def __init__(
        self,
        custom_tags: Optional[List[str]] = None,
        keep_year: bool = True,
        keep_episode: bool = True,
    ):
        """
        Args:
            custom_tags: 自定义需要过滤的标签正则表达式列表
            keep_year: 是否保留年份（如 2024）
            keep_episode: 是否保留剧集编号（如 S01E01）
        """
        self.tags = self.DEFAULT_VIDEO_TAGS.copy()
        if custom_tags:
            self.tags.extend(custom_tags)

        self.keep_year = keep_year
        self.keep_episode = keep_episode

    def normalize(self, filename: str, remove_ext: bool = True) -> str:
        """
        规范化文件名

        Args:
            filename: 原始文件名
            remove_ext: 是否去除扩展名

        Returns:
            规范化后的字符串（小写，空格分隔）

        Examples:
            >>> normalizer = FileNormalizer()
            >>> normalizer.normalize("Movie.2024.1080p.BluRay.x264.mp4")
            'movie 2024'
            >>> normalizer.normalize("Series.S01E01.720p.WEB-DL.mp4")
            'series s01e01'
        """
        # 去除扩展名
        if remove_ext:
            name = Path(filename).stem
        else:
            name = filename

        # 转小写
        name = name.lower()

        # 去除视频标签
        for pattern in self.tags:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)

        # 可选：去除年份
        if not self.keep_year:
            name = re.sub(r'\b(19|20)\d{2}\b', '', name)

        # 可选：去除剧集编号
        if not self.keep_episode:
            name = re.sub(r'\bs\d+e\d+\b', '', name, flags=re.IGNORECASE)

        # 统一分隔符为空格
        name = re.sub(r'[._\-]+', ' ', name)

        # 压缩多个空格
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def extract_language_code(self, filename: str) -> Optional[str]:
        """
        从字幕文件名中提取语言代码

        Args:
            filename: 字幕文件名

        Returns:
            语言代码（如 'zh-hans', 'en'），如果未找到返回 None

        Examples:
            >>> normalizer = FileNormalizer()
            >>> normalizer.extract_language_code("Movie.zh-Hans.srt")
            'zh-hans'
            >>> normalizer.extract_language_code("Movie.CHS.srt")
            'zh-hans'
            >>> normalizer.extract_language_code("Movie.CHT.srt")
            'zh-hant'
            >>> normalizer.extract_language_code("Movie.en.srt")
            'en'
        """
        if not filename:
            return None
        # 只处理文件名部分，不包括路径
        filename = Path(filename).name

        # 语言代码别名映射
        # CHS/CHT 是常见的中文简繁体缩写
        language_aliases = {
            'chs': 'zh-hans',  # 简体中文
            'cht': 'zh-hant',  # 繁体中文
            'gb': 'zh-hans',   # 国标简体
            'big5': 'zh-hant', # Big5 繁体
        }

        # 正则表达式匹配语言代码
        # 支持格式：
        # - .zh-Hans.srt, .zh.srt, .CHS.srt, .Big5.srt
        # - _en-US.srt, -ja.ass, .es-419.srt
        # - .en.forced.srt, .zh.hi.srt
        # - .zh-Hans-CN.srt (多部分 BCP-47)
        # 注意：主语言代码（第一部分）必须以字母开头，以避免误匹配纯数字标签（如 2024, 720p）
        # 后续部分可以是数字（如 es-419 中的 419）
        pattern = r'[._-]([a-z][a-z0-9]{1,3}(?:[_-][a-z0-9]{2,4})*)[._\[-]?(cc|sdh|forced|hi)?\.(srt|ass|ssa|sub|vtt)$'
        match = re.search(pattern, filename.lower())

        if match:
            lang_code = match.group(1)
            # 检查是否是别名，如果是则返回标准代码
            return language_aliases.get(lang_code, lang_code)

        return None

    def extract_episode_info(self, filename: str) -> Optional[Tuple[int, int]]:
        """
        提取剧集信息

        Args:
            filename: 文件名

        Returns:
            (season, episode) 元组，如果未找到返回 None

        Examples:
            >>> normalizer = FileNormalizer()
            >>> normalizer.extract_episode_info("Series.S01E01.mp4")
            (1, 1)
            >>> normalizer.extract_episode_info("Series.1x02.mp4")
            (1, 2)
        """
        if not filename:
            return None
        # 只处理文件名部分，不包括路径
        filename = Path(filename).name

        # 支持 S01E01 格式
        match = re.search(r's(\d+)e(\d+)', filename, re.IGNORECASE)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        # 支持 1x02 格式
        match = re.search(r'(\d+)x(\d+)', filename)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        return None

    def extract_year(self, filename: str) -> Optional[int]:
        """
        提取年份

        Args:
            filename: 文件名

        Returns:
            年份（如 2024），如果未找到返回 None

        Examples:
            >>> normalizer = FileNormalizer()
            >>> normalizer.extract_year("Movie.2024.1080p.mp4")
            2024
        """
        if not filename:
            return None
        # 只处理文件名部分，不包括路径
        filename = Path(filename).name

        match = re.search(r'\b(19|20)(\d{2})\b', filename)
        if match:
            year = int(match.group(0))
            # 合理性检查：1900-2099
            if 1900 <= year <= 2099:
                return year

        return None

    def is_video_file(self, filename: str) -> bool:
        """
        判断是否是视频文件

        Args:
            filename: 文件名

        Returns:
            是否是视频文件
        """
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        return Path(filename).suffix.lower() in video_extensions

    def is_subtitle_file(self, filename: str) -> bool:
        """
        判断是否是字幕文件

        Args:
            filename: 文件名

        Returns:
            是否是字幕文件
        """
        subtitle_extensions = {'.srt', '.ass', '.ssa', '.sub', '.vtt'}
        return Path(filename).suffix.lower() in subtitle_extensions


# 便捷函数
def normalize_filename(filename: str) -> str:
    """快速规范化文件名的便捷函数"""
    normalizer = FileNormalizer()
    return normalizer.normalize(filename)


if __name__ == '__main__':
    # 测试
    normalizer = FileNormalizer()

    test_cases = [
        "Movie.2024.1080p.BluRay.x264.AAC.mp4",
        "Series.S01E01.720p.WEB-DL.H264.mp4",
        "Documentary.4K.HDR.2160p.mp4",
        "Movie.2024.zh-Hans.srt",
        "Series.S01E01.en-US.srt",
    ]

    print("文件名规范化测试:")
    print("=" * 70)
    for filename in test_cases:
        normalized = normalizer.normalize(filename)
        lang = normalizer.extract_language_code(filename)
        print(f"原始: {filename}")
        print(f"规范化: {normalized}")
        if lang:
            print(f"语言代码: {lang}")
        print()
