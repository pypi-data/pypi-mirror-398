"""
句子切分器 - 支持中英文，自动语言检测

使用方法：
    from maque.nlp.sentence_splitter import SentenceSplitter

    splitter = SentenceSplitter(max_length=300)
    sentences = splitter.split("你的文本...")

    # 或使用便捷函数
    from maque.nlp.sentence_splitter import split_sentences
    sentences = split_sentences("你的文本...")
"""

import re
from dataclasses import dataclass


@dataclass
class Sentence:
    """句子对象"""
    text: str       # 句子文本
    start: int      # 在原文中的起始位置
    end: int        # 在原文中的结束位置

    def __len__(self):
        return len(self.text)


# 常见英文缩写（句号不表示句子结束）
_ABBREVIATIONS = {
    'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'vs', 'etc', 'inc', 'ltd',
    'st', 'ave', 'rd', 'blvd', 'dept', 'univ', 'govt', 'approx', 'appt',
    'apt', 'asst', 'assn', 'atty', 'corp', 'est', 'ext', 'fig', 'gen',
    'hon', 'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct',
    'nov', 'dec', 'no', 'nos', 'vol', 'rev', 'e.g', 'i.e', 'cf', 'al',
}


class SentenceSplitter:
    """句子切分器，支持中英文自动检测"""

    def __init__(self, max_length: int = 300):
        """
        Args:
            max_length: 单个句子最大长度，超过则按次级标点切分
        """
        self.max_length = max_length

        # 中文: 句号后直接切分，或换行分隔
        self._pattern_cn = re.compile(r'(?<=[。！？])|\n+')
        # 次级标点（用于切分超长句子）
        self._pattern_sub = re.compile(r'(?<=[,;，；])\s*')

    def _has_chinese(self, text: str) -> bool:
        """检测文本是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def _split_english(self, text: str) -> list[str]:
        """英文句子切分，处理缩写"""
        sentences = []
        current = []
        i = 0
        n = len(text)

        while i < n:
            char = text[i]
            current.append(char)

            # 检测句子结束符
            if char in '.!?':
                # 检查是否是缩写
                is_abbrev = False
                if char == '.':
                    # 向前找单词
                    word_chars = []
                    j = len(current) - 2  # 跳过当前的点
                    while j >= 0 and (current[j].isalpha() or current[j] == '.'):
                        word_chars.append(current[j])
                        j -= 1
                    word = ''.join(reversed(word_chars)).lower().rstrip('.')
                    if word in _ABBREVIATIONS:
                        is_abbrev = True
                    # 检查是否是单字母缩写（如 A. B. C.）
                    if len(word) == 1 and word.isupper():
                        is_abbrev = True

                if not is_abbrev:
                    # 检查后面是否有空格或换行（句子结束的标志）
                    if i + 1 < n and text[i + 1] in ' \t\n\r':
                        sent = ''.join(current).strip()
                        if sent:
                            sentences.append(sent)
                        current = []
                        # 跳过空白
                        i += 1
                        while i < n and text[i] in ' \t\n\r':
                            i += 1
                        continue
            elif char == '\n':
                # 换行也作为句子分隔
                sent = ''.join(current).strip()
                if sent:
                    sentences.append(sent)
                current = []

            i += 1

        # 处理最后一个句子
        if current:
            sent = ''.join(current).strip()
            if sent:
                sentences.append(sent)

        return sentences

    def _split_by_punctuation(self, text: str) -> list[str]:
        """按标点切分文本"""
        if self._has_chinese(text):
            return [s.strip() for s in self._pattern_cn.split(text) if s.strip()]
        else:
            return self._split_english(text)

    def _split_long_sentence(self, sent: str) -> list[str]:
        """切分超长句子，按次级标点（逗号、分号）切分"""
        parts = [p.strip() for p in self._pattern_sub.split(sent) if p.strip()]

        result = []
        for part in parts:
            if len(part) <= self.max_length:
                result.append(part)
            else:
                # 强制按长度切分
                for i in range(0, len(part), self.max_length):
                    result.append(part[i:i + self.max_length])
        return result

    def split(self, text: str) -> list[Sentence]:
        """
        切分文本为句子列表

        Args:
            text: 输入文本

        Returns:
            Sentence 对象列表，包含文本、起始位置、结束位置
        """
        if not text:
            return []

        sentences = self._split_by_punctuation(text)

        result = []
        pos = 0
        for sent in sentences:
            idx = text.find(sent, pos)
            if idx < 0:
                continue

            if len(sent) <= self.max_length:
                result.append(Sentence(sent, idx, idx + len(sent)))
            else:
                # 超长句子：按次级标点切分
                sub_parts = self._split_long_sentence(sent)
                sub_pos = idx
                for part in sub_parts:
                    part_idx = text.find(part, sub_pos)
                    if part_idx >= 0:
                        result.append(Sentence(part, part_idx, part_idx + len(part)))
                        sub_pos = part_idx + len(part)

            pos = idx + len(sent)

        return result

    def split_text(self, text: str) -> list[str]:
        """切分文本，只返回句子文本列表（不含位置信息）"""
        return [s.text for s in self.split(text)]


# 默认切分器实例
_default_splitter = SentenceSplitter()


def split_sentences(text: str, max_length: int = 300) -> list[Sentence]:
    """
    便捷函数：切分文本为句子列表

    Args:
        text: 输入文本
        max_length: 单个句子最大长度

    Returns:
        Sentence 对象列表
    """
    if max_length != 300:
        splitter = SentenceSplitter(max_length=max_length)
        return splitter.split(text)
    return _default_splitter.split(text)
