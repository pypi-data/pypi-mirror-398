# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析器"""

import re
from typing import List
import pandas as pd


def parse_generic_tags(text: str, strict: bool = False) -> dict:
    """
    通用的标签解析函数，可以解析字符串中混合存在的 <label>content</label> 和 <label>content 格式。

    Args:
        text: 待解析的字符串。
        strict: 布尔值，用于控制是否启用严格匹配模式。
                - False (默认): 解析所有闭合标签和开放式标签，并优先处理闭合标签。
                - True: 仅解析格式完好的闭合标签 (<label>content</label>)，忽略所有开放式标签。

    Returns:
        dict: 解析结果，格式为 {label: content, ...}
    """
    if not text:
        return {}

    result = {}

    if strict:
        # --- 严格模式 ---
        # 只匹配拥有正确闭合标签的 <label>content</label> 格式
        pattern_with_closing = r"<([^>]+)>\s*(.*?)\s*</\1>"
        matches = re.findall(pattern_with_closing, text, re.DOTALL)
        for label, content in matches:
            result[label.strip()] = content.strip()

    else:
        # --- 兼容模式 (非严格) ---
        remaining_text = str(text)

        # 1. 优先处理闭合标签，并从文本中“移除”它们
        def process_closed_tag(match_obj):
            label = match_obj.group(1).strip()
            content = match_obj.group(2).strip()
            result[label] = content
            return ""

        pattern_with_closing = r"<([^>]+)>\s*(.*?)\s*</\1>"
        remaining_text = re.sub(
            pattern_with_closing, process_closed_tag, remaining_text, flags=re.DOTALL
        )

        # 2. 在剩余文本中处理开放式标签
        pattern_open = r"<([^>]+)>\s*(.*?)(?=<[^>]+>|$)"
        matches_open = re.findall(pattern_open, remaining_text, re.DOTALL)
        for label, content in matches_open:
            label_stripped = label.strip()
            if label_stripped not in result:
                result[label_stripped] = content.strip()

    return result


def split_urls(text: str) -> List[str]:
    """从文本中提取所有URL

    Args:
        text: 包含URL的字符串

    Returns:
        List[str]: 提取到的URL列表
    """
    if not text:
        return []

    # 使用正则表达式匹配所有URL
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)
    urls = re.findall(r"https?://.*?(?=https?://|$)", text)
    url_list = [url.strip(" ,|;；") for url in urls]
    return url_list


def split_image_paths(text: str, separators: List[str] = None) -> List[str]:
    """从文本中提取所有图像路径（包括HTTP URL和本地路径）
    
    优化版本：能够正确处理URL中包含逗号等分隔符的情况，避免错误切割。

    Args:
        text: 包含图像路径的字符串
        separators: 分隔符列表，如 [",", ";"] 或 ["\n"]，默认为 [",", ";", "\n", "\r"]

    Returns:
        List[str]: 提取到的图像路径列表
    """
    if not text or pd.isna(text):
        return []

    text = str(text).strip()
    if not text:
        return []

    # 如果用户提供了自定义分隔符，优先使用用户的设置，不使用智能检测
    if separators is not None:
        # 用户明确指定了分隔符，跳过智能检测，直接使用用户的分隔符
        pass
    else:
        # 只有在用户没有指定分隔符时，才使用智能提取完整的URL
        # 使用正则表达式匹配完整的HTTP(S) URL
        url_pattern = r'https?://[^\s<>"\';]*'
        urls = re.findall(url_pattern, text)
        
        # 如果找到了URL，检查是否覆盖了整个文本（说明是单个URL）
        if urls:
            # 如果只有一个URL且几乎覆盖了整个文本，直接返回
            if len(urls) == 1 and len(urls[0]) > len(text) * 0.8:
                return [urls[0]]
            
            # 如果找到多个URL，返回所有URL
            if len(urls) > 1:
                return urls
            
            # 如果只找到一个URL但不覆盖全文，可能有其他路径，继续原逻辑
    
    # 如果没有找到HTTP URL，或需要处理混合内容，使用原来的分隔符逻辑
    # 但要更小心地处理逗号，避免切断URL参数
    
    # 默认分隔符列表
    if separators is None:
        separators = [";", "\n", "\r"]  # 永远不使用逗号作为分隔符，因为URL参数中常包含逗号
    
    # 使用正则表达式进行分割，支持多个分隔符
    if len(separators) == 1:
        # 单个分隔符，直接分割
        paths = text.split(separators[0])
    else:
        # 多个分隔符，构建正则表达式
        escaped_separators = [re.escape(sep) for sep in separators]
        pattern = "|".join(escaped_separators)
        paths = re.split(pattern, text)

    # 清理和过滤路径
    cleaned_paths = []
    for path in paths:
        path = path.strip()
        if path:
            # 检查是否为HTTP(S) URL
            if re.match(r"https?://", path):
                cleaned_paths.append(path)
            # 检查是否为有效的文件路径
            elif (
                path.startswith("./")
                or path.startswith("../")
                or path.startswith("/")
                or path.startswith("\\")
                or re.match(r"^[A-Za-z]:[/\\]", path)  # Windows绝对路径如 C:\ 或 D:/
                or (
                    ("/" in path or "\\" in path)
                    and (
                        "." in path
                        or path.endswith(
                            (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
                        )
                    )
                )
            ):
                cleaned_paths.append(path)

    return cleaned_paths
