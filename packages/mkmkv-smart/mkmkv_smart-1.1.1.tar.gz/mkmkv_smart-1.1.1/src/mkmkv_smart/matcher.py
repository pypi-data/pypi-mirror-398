"""
智能文件匹配模块

使用多种模糊匹配算法智能匹配视频和字幕文件。
"""

from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import linear_sum_assignment
import numpy as np

from .normalizer import FileNormalizer

# 支持的匹配方法（权威定义）
VALID_MATCH_METHODS = frozenset({
    "token_set",    # 集合匹配（推荐）
    "token_sort",   # 顺序无关匹配
    "partial",      # 部分匹配
    "ratio",        # 标准编辑距离
    "wratio",       # 加权比率
    "hybrid"        # 混合策略（默认）
})


@dataclass
class MatchResult:
    """匹配结果"""
    subtitle_file: str
    similarity: float
    language_code: Optional[str] = None
    method: str = "hybrid"


class SmartMatcher:
    """智能文件匹配器"""

    def __init__(
        self,
        threshold: float = 30.0,
        method: str = 'hybrid',
        normalizer: Optional[FileNormalizer] = None
    ):
        """
        Args:
            threshold: 相似度阈值 (0-100)
            method: 匹配方法
                - 'token_set': 集合匹配（推荐）
                - 'token_sort': 顺序无关匹配
                - 'partial': 部分匹配
                - 'ratio': 标准编辑距离
                - 'hybrid': 混合策略（默认，综合多种算法）
            normalizer: 文件名规范化器（可选）
        """
        # 验证阈值范围
        if not 0 <= threshold <= 100:
            raise ValueError(f"threshold 必须在 0-100 之间，当前值: {threshold}")

        # 验证方法有效性
        if method not in VALID_MATCH_METHODS:
            raise ValueError(
                f"未知的匹配方法: {method}。"
                f"有效方法: {', '.join(sorted(VALID_MATCH_METHODS))}"
            )

        self.threshold = threshold
        self.method = method
        self.normalizer = normalizer or FileNormalizer()

    def calculate_similarity(
        self,
        video: str,
        subtitle: str,
        method: Optional[str] = None
    ) -> float:
        """
        计算两个文件名的相似度

        Args:
            video: 视频文件名
            subtitle: 字幕文件名
            method: 匹配方法（可选，默认使用初始化时指定的方法）

        Returns:
            相似度分数 (0-100)
        """
        # 规范化文件名
        video_norm = self.normalizer.normalize(video)
        sub_norm = self.normalizer.normalize(subtitle)

        # 使用指定的方法
        match_method = method or self.method

        if match_method == 'token_set':
            score = fuzz.token_set_ratio(video_norm, sub_norm)
        elif match_method == 'token_sort':
            score = fuzz.token_sort_ratio(video_norm, sub_norm)
        elif match_method == 'partial':
            score = fuzz.partial_ratio(video_norm, sub_norm)
        elif match_method == 'ratio':
            score = fuzz.ratio(video_norm, sub_norm)
        elif match_method == 'wratio':
            score = fuzz.WRatio(video_norm, sub_norm)
        elif match_method == 'hybrid':
            # 混合策略：综合多种算法，取最高分
            scores = [
                fuzz.token_set_ratio(video_norm, sub_norm),      # 集合匹配
                fuzz.token_sort_ratio(video_norm, sub_norm),     # 顺序无关
                fuzz.partial_ratio(video_norm, sub_norm) * 0.9,  # 部分匹配（权重略低）
            ]
            score = max(scores)
        else:
            raise ValueError(f"Unknown method: {match_method}")

        return float(score)

    def find_best_match(
        self,
        video: str,
        subtitles: List[str],
        return_all: bool = False
    ) -> List[MatchResult]:
        """
        为视频文件找到最佳匹配的字幕

        Args:
            video: 视频文件名
            subtitles: 字幕文件列表
            return_all: 是否返回所有匹配（而非仅最佳匹配）

        Returns:
            匹配结果列表，按相似度降序排列
        """
        results = []

        for sub in subtitles:
            # 计算相似度
            similarity = self.calculate_similarity(video, sub)

            # 过滤低于阈值的匹配
            if similarity >= self.threshold:
                # 提取语言代码
                lang_code = self.normalizer.extract_language_code(sub)

                results.append(MatchResult(
                    subtitle_file=sub,
                    similarity=similarity,
                    language_code=lang_code,
                    method=self.method
                ))

        # 按相似度降序排序
        results.sort(key=lambda x: x.similarity, reverse=True)

        # 如果只返回最佳匹配，且有结果，则只返回第一个
        if not return_all and results:
            return [results[0]]

        return results

    def match_by_language(
        self,
        video: str,
        subtitles: List[str],
        language_priority: Optional[List[str]] = None
    ) -> Dict[str, MatchResult]:
        """
        按语言分组匹配字幕

        为每种语言选择相似度最高的字幕。

        Args:
            video: 视频文件名
            subtitles: 字幕文件列表
            language_priority: 语言优先级列表（可选）

        Returns:
            {语言代码: 匹配结果} 字典
        """
        # 找到所有匹配
        all_matches = self.find_best_match(video, subtitles, return_all=True)

        # 按语言分组
        lang_groups: Dict[str, List[MatchResult]] = {}
        for match in all_matches:
            # 如果没有语言代码，使用 'und'（未确定）作为默认值
            lang = match.language_code if match.language_code else 'und'
            if lang not in lang_groups:
                lang_groups[lang] = []
            lang_groups[lang].append(match)

        # 为每种语言选择最佳匹配
        result: Dict[str, MatchResult] = {}
        for lang, matches in lang_groups.items():
            # 按相似度降序排序（已排序，但再确认）
            matches.sort(key=lambda x: x.similarity, reverse=True)
            result[lang] = matches[0]

        # 如果指定了语言优先级，按优先级排序
        if language_priority:
            sorted_result = {}
            # 先添加优先级列表中的语言
            for lang in language_priority:
                if lang in result:
                    sorted_result[lang] = result[lang]
            # 再添加其他语言
            for lang, match in result.items():
                if lang not in sorted_result:
                    sorted_result[lang] = match
            return sorted_result

        return result

    def batch_match(
        self,
        videos: List[str],
        subtitles: List[str],
        language_priority: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, MatchResult]]:
        """
        批量匹配视频和字幕（全局最优分配）

        使用 RapidFuzz 的 cdist 批量计算相似度矩阵，提升性能。
        使用匈牙利算法（Hungarian Algorithm）实现全局最优分配，
        确保总体相似度最大化，而不是局部贪心。

        Args:
            videos: 视频文件列表
            subtitles: 字幕文件列表
            language_priority: 语言优先级列表（可选）

        Returns:
            {视频文件名: {语言代码: 匹配结果, ...}, ...}
        """
        if not videos or not subtitles:
            return {}

        # 步骤 1: 规范化所有文件名
        videos_norm = [self.normalizer.normalize(v) for v in videos]
        subtitles_norm = [self.normalizer.normalize(s) for s in subtitles]

        # 步骤 2: 使用 cdist 批量计算相似度矩阵
        if self.method == 'hybrid':
            # hybrid 方法：计算多个矩阵，逐元素取最大值
            matrix1 = process.cdist(
                videos_norm,
                subtitles_norm,
                scorer=fuzz.token_set_ratio,
                workers=-1  # 使用所有 CPU 核心
            )
            matrix2 = process.cdist(
                videos_norm,
                subtitles_norm,
                scorer=fuzz.token_sort_ratio,
                workers=-1
            )
            matrix3 = process.cdist(
                videos_norm,
                subtitles_norm,
                scorer=fuzz.partial_ratio,
                workers=-1
            )
            # 逐元素取最大值（partial_ratio 权重 0.9）
            # 注意：cdist 返回的是列表的列表，需要逐行处理
            similarity_matrix = []
            for i in range(len(videos)):
                row = []
                for j in range(len(subtitles)):
                    score = max(
                        matrix1[i][j],
                        matrix2[i][j],
                        matrix3[i][j] * 0.9
                    )
                    row.append(score)
                similarity_matrix.append(row)
        else:
            # 其他方法：直接使用对应的 scorer
            scorer_map = {
                'token_set': fuzz.token_set_ratio,
                'token_sort': fuzz.token_sort_ratio,
                'partial': fuzz.partial_ratio,
                'ratio': fuzz.ratio,
                'wratio': fuzz.WRatio
            }
            scorer = scorer_map[self.method]
            similarity_matrix = process.cdist(
                videos_norm,
                subtitles_norm,
                scorer=scorer,
                workers=-1  # 使用所有 CPU 核心
            )

        # 转换为 numpy 数组以便后续处理
        similarity_matrix = np.array(similarity_matrix)

        # 步骤 3: 按语言分组字幕
        subtitle_languages: Dict[str, List[Tuple[int, str]]] = {}  # {语言: [(索引, 文件名), ...]}

        for j, subtitle in enumerate(subtitles):
            lang_code = self.normalizer.extract_language_code(subtitle)
            lang = lang_code if lang_code else 'und'
            if lang not in subtitle_languages:
                subtitle_languages[lang] = []
            subtitle_languages[lang].append((j, subtitle))

        # 步骤 4: 对每种语言使用匈牙利算法求解最优分配
        final_results: Dict[str, Dict[str, MatchResult]] = {}

        for lang, lang_subtitles in subtitle_languages.items():
            # 提取该语言的字幕索引
            subtitle_indices = [idx for idx, _ in lang_subtitles]

            # 构建该语言的相似度子矩阵 (n_videos × n_lang_subtitles)
            lang_similarity = similarity_matrix[:, subtitle_indices]

            # 构建成本矩阵（匈牙利算法求最小成本）
            # cost = 100 - similarity，低于阈值的设为极大值（不可行）
            cost_matrix = np.where(
                lang_similarity >= self.threshold,
                100 - lang_similarity,  # 可行分配：相似度越高，成本越低
                1000.0  # 不可行分配：成本极大
            )

            # 使用匈牙利算法求解最优分配
            # row_ind: 视频索引数组, col_ind: 字幕索引数组（在该语言子集中）
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            # 将分配结果转换为 MatchResult
            for video_idx, subtitle_idx_in_lang in zip(row_ind, col_ind):
                # 获取实际的字幕索引和文件名
                actual_subtitle_idx, subtitle_file = lang_subtitles[subtitle_idx_in_lang]

                # 获取相似度
                similarity = similarity_matrix[video_idx, actual_subtitle_idx]

                # 过滤掉低于阈值的分配（成本极大的）
                if similarity < self.threshold:
                    continue

                video_name = videos[video_idx]

                # 添加到结果
                if video_name not in final_results:
                    final_results[video_name] = {}

                final_results[video_name][lang] = MatchResult(
                    subtitle_file=subtitle_file,
                    similarity=float(similarity),
                    language_code=lang,
                    method=self.method
                )

        # 步骤 5: 应用语言优先级排序
        if language_priority:
            for video_name in final_results:
                sorted_result: Dict[str, MatchResult] = {}
                # 先按优先级添加
                for lang in language_priority:
                    if lang in final_results[video_name]:
                        sorted_result[lang] = final_results[video_name][lang]
                # 再添加其他语言
                for lang, match in final_results[video_name].items():
                    if lang not in sorted_result:
                        sorted_result[lang] = match
                final_results[video_name] = sorted_result

        return final_results
