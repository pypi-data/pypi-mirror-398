"""
风险关键词匹配器 - 从长文本中高效提取包含风险关键词的关键段落

使用方法：
    from maque.nlp.risk_matcher import RiskMatcher

    matcher = RiskMatcher.from_json("risk_keywords.json")
    results = matcher.extract_segments("你的长文本...")

    for seg in results:
        print(f"[{seg['risk_level']}] {seg['keyword']} -> {seg['segment']}")
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import ahocorasick

from .sentence_splitter import SentenceSplitter


@dataclass
class MatchResult:
    """匹配结果"""
    keyword: str              # 匹配到的关键词
    risk_level: str           # 风险级别: high/medium/combo
    category: str             # 关键词类别
    start: int                # 关键词在原文中的起始位置
    end: int                  # 关键词在原文中的结束位置
    segment: str              # 提取的关键段落
    segment_start: int        # 段落在原文中的起始位置
    segment_end: int          # 段落在原文中的结束位置


@dataclass
class ExtractResult:
    """提取结果汇总"""
    text: str                              # 原始文本
    matches: list[MatchResult] = field(default_factory=list)  # 所有匹配
    segments: list[str] = field(default_factory=list)         # 去重后的段落列表
    risk_level: str = "none"               # 整体风险级别
    hit_high: bool = False                 # 是否命中高风险词
    hit_medium_count: int = 0              # 命中中风险词数量
    hit_combo: bool = False                # 是否命中组合规则

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "hit_high": self.hit_high,
            "hit_medium_count": self.hit_medium_count,
            "hit_combo": self.hit_combo,
            "segments": self.segments,
            "matches": [
                {
                    "keyword": m.keyword,
                    "risk_level": m.risk_level,
                    "category": m.category,
                    "segment": m.segment,
                }
                for m in self.matches
            ],
        }


class RiskMatcher:
    """风险关键词匹配器（基于 Aho-Corasick 算法）"""

    def __init__(
        self,
        high_risk: list[str] | dict[str, list[str]] = None,
        medium_risk: list[str] | dict[str, list[str]] = None,
        combo_rules: dict[str, dict] = None,
        context_chars: int = 150,
    ):
        """
        Args:
            high_risk: 高风险词列表或 {类别: [关键词列表]}
            medium_risk: 中风险词列表或 {类别: [关键词列表]}
            combo_rules: 组合规则
            context_chars: 关键词前后提取的字符数
        """
        self.combo_rules = combo_rules or {}
        self.context_chars = context_chars
        self._low_risk_words: set[str] = set()  # 低风险词（需组合才触发）

        # 句子切分器
        self._splitter = SentenceSplitter(max_length=300)

        # 构建关键词到(级别, 类别)的映射
        self._keyword_map: dict[str, tuple[str, str]] = {}

        # 支持列表或字典格式
        if isinstance(high_risk, list):
            for kw in high_risk:
                self._keyword_map[kw.lower()] = ("high", "高风险")
        elif isinstance(high_risk, dict):
            for category, keywords in high_risk.items():
                if category == "说明" or not isinstance(keywords, list):
                    continue
                for kw in keywords:
                    self._keyword_map[kw.lower()] = ("high", category)

        if isinstance(medium_risk, list):
            for kw in medium_risk:
                self._keyword_map[kw.lower()] = ("medium", "中风险")
        elif isinstance(medium_risk, dict):
            for category, keywords in medium_risk.items():
                if category == "说明" or not isinstance(keywords, list):
                    continue
                for kw in keywords:
                    self._keyword_map[kw.lower()] = ("medium", category)

        # 构建 Aho-Corasick 自动机
        self._automaton = None
        if self._keyword_map:
            self._build_automaton()

    def _build_automaton(self):
        """构建 Aho-Corasick 自动机"""
        self._automaton = ahocorasick.Automaton()
        for keyword in self._keyword_map:
            self._automaton.add_word(keyword, keyword)
        self._automaton.make_automaton()

    @classmethod
    def from_json(cls, json_path: str, **kwargs) -> "RiskMatcher":
        """从 JSON 文件加载配置"""
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 合并高风险词、风险句式、GPT变体
        high_risk = config.get("高风险词", [])
        risk_phrases = config.get("风险句式", [])
        gpt_variants = config.get("高风险GPT变体", [])

        if isinstance(high_risk, list):
            if isinstance(risk_phrases, list):
                high_risk = high_risk + risk_phrases
            if isinstance(gpt_variants, list):
                high_risk = high_risk + gpt_variants
        elif isinstance(high_risk, dict):
            if isinstance(risk_phrases, list):
                high_risk["风险句式"] = risk_phrases
            if isinstance(gpt_variants, list):
                high_risk["GPT变体"] = gpt_variants

        # 获取低风险词（需要组合才触发）
        low_risk_config = config.get("低风险词_需组合", {})
        low_risk_words = low_risk_config.get("词列表", []) if isinstance(low_risk_config, dict) else []

        matcher = cls(
            high_risk=high_risk,
            medium_risk=config.get("中风险词", {}),
            combo_rules=config.get("组合规则", {}),
            **kwargs,
        )
        # 存储低风险词列表
        matcher._low_risk_words = set(kw.lower() for kw in low_risk_words)
        return matcher

    def _find_matches(self, text_lower: str) -> list[tuple[str, int, int]]:
        """使用 Aho-Corasick 查找所有匹配"""
        if not self._automaton:
            return []
        matches = []
        for end_idx, keyword in self._automaton.iter(text_lower):
            start_idx = end_idx - len(keyword) + 1
            matches.append((keyword, start_idx, end_idx + 1))
        return matches

    def _split_sentences(self, text: str) -> list[tuple[str, int, int]]:
        """切分句子，返回 [(句子, 起始位置, 结束位置)]"""
        return [(s.text, s.start, s.end) for s in self._splitter.split(text)]

    def _extract_segment(
        self,
        text: str,
        start: int,
        end: int,
        sentences: list[tuple[str, int, int]] = None,
    ) -> tuple[str, int, int]:
        """提取包含关键词的完整句子"""
        # 如果没有传入句子列表，则切分（兼容旧调用）
        if sentences is None:
            sentences = self._split_sentences(text)

        # 找到包含关键词的句子
        matched_sentences = []
        for sent, s_start, s_end in sentences:
            # 关键词位置与句子有重叠
            if s_start <= start < s_end or s_start < end <= s_end:
                matched_sentences.append((sent, s_start, s_end))

        if matched_sentences:
            # 合并所有匹配的句子
            seg_start = min(s[1] for s in matched_sentences)
            seg_end = max(s[2] for s in matched_sentences)
            segment = text[seg_start:seg_end].strip()
            return segment, seg_start, seg_end

        # fallback: 使用固定窗口
        seg_start = max(0, start - self.context_chars)
        seg_end = min(len(text), end + self.context_chars)
        segment = text[seg_start:seg_end].strip()
        return segment, seg_start, seg_end

    def _check_combo_rules(self, text_lower: str) -> list[tuple[str, str, str]]:
        """检查组合规则，返回 [(规则名, A组词, B组词)]"""
        hits = []
        for rule_name, rule in self.combo_rules.items():
            if rule_name == "说明":
                continue

            # 支持多种字段名格式
            a_keywords = (
                rule.get("A组") or
                rule.get("A组_角色扮演") or
                rule.get("A组_指令词") or
                []
            )
            b_keywords = (
                rule.get("B组") or
                rule.get("B组_规避词") or
                rule.get("B组_强制词") or
                []
            )

            a_hit = None
            b_hit = None
            for kw in a_keywords:
                if kw.lower() in text_lower:
                    a_hit = kw
                    break
            for kw in b_keywords:
                if kw.lower() in text_lower:
                    b_hit = kw
                    break

            if a_hit and b_hit:
                hits.append((rule_name, a_hit, b_hit))

        return hits

    def _merge_overlapping_segments(
        self,
        matches: list[MatchResult],
        merge_gap: int = 50,
        min_length: int = 20,
        max_length: int = 500,
    ) -> list[str]:
        """合并重叠或相邻的段落，并过滤长度"""
        if not matches:
            return []

        # 按段落位置排序
        sorted_matches = sorted(matches, key=lambda m: m.segment_start)

        merged = []
        current_start = sorted_matches[0].segment_start
        current_end = sorted_matches[0].segment_end
        current_text = sorted_matches[0].segment

        for m in sorted_matches[1:]:
            if m.segment_start <= current_end + merge_gap:
                # 重叠或相邻，合并
                current_end = max(current_end, m.segment_end)
            else:
                # 不重叠，保存当前段落
                merged.append(current_text)
                current_start = m.segment_start
                current_end = m.segment_end
                current_text = m.segment

        merged.append(current_text)

        # 过滤长度
        filtered = []
        for seg in merged:
            if len(seg) < min_length:
                continue
            if len(seg) > max_length:
                seg = seg[:max_length] + "..."
            filtered.append(seg)

        return filtered

    def _find_sentence_boundary_start(self, text: str, pos: int, max_search: int = 100) -> int:
        """从 pos 向前找句子开始位置（上一个句子结束符之后）"""
        if pos <= 0:
            return 0

        terminators = '.?!。？！\n'
        search_start = max(0, pos - max_search)
        for i in range(pos - 1, search_start - 1, -1):
            if text[i] in terminators:
                boundary = i + 1
                while boundary < pos and text[boundary] in ' \t\n\r':
                    boundary += 1
                return boundary

        return search_start if search_start > 0 else pos

    def _find_sentence_boundary_end(self, text: str, pos: int, max_search: int = 100) -> int:
        """从 pos 向后找句子结束位置"""
        text_len = len(text)
        if pos >= text_len:
            return text_len

        terminators = '.?!。？！\n'
        search_end = min(text_len, pos + max_search)
        for i in range(pos, search_end):
            if text[i] in terminators:
                return i + 1

        return search_end if search_end < text_len else pos

    def get_expanded_segments(
        self,
        text: str,
        matches: list[MatchResult],
        context_chars: int = 200,
        merge_gap: int = 50,
        min_length: int = 150,
        max_length: int = 1000,
        snap_to_sentence: bool = True,
    ) -> list[str]:
        """
        对匹配结果扩展上下文并合并重叠区域，生成适合向量检索的段落

        Args:
            text: 原始文本
            matches: 匹配结果列表
            context_chars: 每个 segment 前后扩展的字符数
            merge_gap: 合并间距阈值
            min_length: 最小段落长度
            max_length: 最大段落长度
            snap_to_sentence: 是否对齐到句子边界
        """
        if not matches:
            return []

        # 1. 计算每个 match 的扩展区域
        regions = []
        for m in matches:
            start = max(0, m.segment_start - context_chars)
            end = min(len(text), m.segment_end + context_chars)

            if snap_to_sentence:
                start = self._find_sentence_boundary_start(text, start)
                end = self._find_sentence_boundary_end(text, end)

            regions.append((start, end))

        # 2. 按起始位置排序并合并重叠区域
        regions.sort()
        merged = []
        curr_start, curr_end = regions[0]

        for start, end in regions[1:]:
            if start <= curr_end + merge_gap:
                curr_end = max(curr_end, end)
            else:
                merged.append((curr_start, curr_end))
                curr_start, curr_end = start, end
        merged.append((curr_start, curr_end))

        # 3. 提取文本并过滤
        segments = []
        for start, end in merged:
            seg = text[start:end].strip()
            if len(seg) >= min_length:
                if len(seg) > max_length:
                    if snap_to_sentence:
                        cut_pos = self._find_sentence_boundary_end(seg, max_length - 50, max_search=50)
                        if cut_pos > min_length:
                            seg = seg[:cut_pos]
                        else:
                            seg = seg[:max_length] + "..."
                    else:
                        seg = seg[:max_length] + "..."
                segments.append(seg)

        return segments

    def extract_segments(
        self,
        text: str,
        medium_threshold: int = 2,
    ) -> ExtractResult:
        """
        从文本中提取风险段落

        Args:
            text: 输入文本
            medium_threshold: 中风险词命中阈值

        Returns:
            ExtractResult 对象
        """
        result = ExtractResult(text=text)

        if not text:
            return result

        text_lower = text.lower()

        # 1. 查找关键词匹配
        raw_matches = self._find_matches(text_lower)

        # 2. 检查组合规则
        combo_hits = self._check_combo_rules(text_lower)

        # 如果没有任何匹配，直接返回
        if not raw_matches and not combo_hits:
            return result

        # 3. 句子切分（只做一次）
        sentences = self._split_sentences(text)

        # 4. 构建 MatchResult
        high_count = 0
        medium_count = 0

        for keyword, start, end in raw_matches:
            level, category = self._keyword_map[keyword]
            segment, seg_start, seg_end = self._extract_segment(text, start, end, sentences)

            match = MatchResult(
                keyword=keyword,
                risk_level=level,
                category=category,
                start=start,
                end=end,
                segment=segment,
                segment_start=seg_start,
                segment_end=seg_end,
            )
            result.matches.append(match)

            if level == "high":
                high_count += 1
            else:
                medium_count += 1

        # 5. 处理组合规则匹配
        for rule_name, a_kw, b_kw in combo_hits:
            a_idx = text_lower.find(a_kw.lower())
            if a_idx >= 0:
                segment, seg_start, seg_end = self._extract_segment(text, a_idx, a_idx + len(a_kw), sentences)
                match = MatchResult(
                    keyword=f"{a_kw} + {b_kw}",
                    risk_level="combo",
                    category=rule_name,
                    start=a_idx,
                    end=a_idx + len(a_kw),
                    segment=segment,
                    segment_start=seg_start,
                    segment_end=seg_end,
                )
                result.matches.append(match)

        # 6. 处理低风险词逻辑（需要配合其他风险词才触发）
        has_real_risk = high_count > 0 or medium_count > 0 or len(combo_hits) > 0

        low_risk_matches = [kw for kw in self._low_risk_words if kw in text_lower]

        if low_risk_matches and has_real_risk:
            for kw in low_risk_matches:
                idx = text_lower.find(kw)
                if idx >= 0:
                    segment, seg_start, seg_end = self._extract_segment(text, idx, idx + len(kw), sentences)
                    match = MatchResult(
                        keyword=kw,
                        risk_level="medium",
                        category="低风险词_已激活",
                        start=idx,
                        end=idx + len(kw),
                        segment=segment,
                        segment_start=seg_start,
                        segment_end=seg_end,
                    )
                    result.matches.append(match)
                    medium_count += 1

        # 7. 判断整体风险级别
        result.hit_high = high_count > 0
        result.hit_medium_count = medium_count
        result.hit_combo = len(combo_hits) > 0

        if result.hit_high or result.hit_combo:
            result.risk_level = "high"
        elif result.hit_medium_count >= medium_threshold:
            result.risk_level = "medium"
        elif result.hit_medium_count > 0:
            result.risk_level = "low"

        # 8. 合并重叠段落
        result.segments = self._merge_overlapping_segments(result.matches)

        return result

    def batch_extract(
        self,
        texts: list[str],
        medium_threshold: int = 2,
        only_risky: bool = True,
    ) -> list[ExtractResult]:
        """
        批量提取

        Args:
            texts: 文本列表
            medium_threshold: 中风险词命中阈值
            only_risky: 是否只返回有风险的结果
        """
        results = []
        for text in texts:
            r = self.extract_segments(text, medium_threshold)
            if only_risky and r.risk_level == "none":
                continue
            results.append(r)
        return results


def match_and_extract(
    text: str,
    keywords_json: str = None,
    context_chars: int = 150,
) -> ExtractResult:
    """
    便捷函数：匹配并提取风险段落

    Args:
        text: 输入文本
        keywords_json: 关键词库 JSON 文件路径
        context_chars: 上下文字符数
    """
    if keywords_json is None:
        keywords_json = Path(__file__).parent / "risk_keywords.json"

    matcher = RiskMatcher.from_json(keywords_json, context_chars=context_chars)
    return matcher.extract_segments(text)
