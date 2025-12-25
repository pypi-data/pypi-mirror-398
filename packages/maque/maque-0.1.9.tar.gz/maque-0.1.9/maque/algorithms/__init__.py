"""
算法模块 - 数据结构和算法实现

包含各种算法实现：Trie树、变换算法、去重算法、数学函数等
"""

# 数据结构
from .trie import *
from .bktree import *

# 变换算法
from .hilbert import *
from .transform import *

# 去重算法
from .video import *  # video deduplication

# 数学函数
from .bezier import *
from .core import *  # functions core
from .rate_function import *
from .utils import *  # functions utils

__all__ = [
    # Data structures
    "BKTree",
    "brute_query",
    "levenshtein",
    "Trie",
    "PyTrie",
    "HatTrie",
    "MarisaTrie",
    "DaTrie",
    "AutomatonTrie",
    "Benchmark",
    # Transforms
    "get_hilbert_1d_array",
    "repeat",
    # Video deduplication
    "VideoFrameDeduplicator",
    # Math functions
    "bezier",
    "dict_topk",
    "topk",
    "random_idx",
    "clamp",
    "choose_using_cache",
    "choose",
    "get_num_args",
    "get_parameters",
    # Rate functions
    "linear",
    "smooth",
    "rush_into",
    "rush_from",
    "slow_into",
    "double_smooth",
    "there_and_back",
    "there_and_back_with_pause",
    "running_start",
    "not_quite_there",
    "wiggle",
    "squish_rate_func",
    "lingering",
    "exponential_decay",
    # Utils
    "exists",
    "default",
    "cast_tuple",
    "null_context",
    "pick_and_pop",
    "group_dict_by_key",
    "string_begins_with",
    "group_by_key_prefix",
    "groupby_prefix_and_trim",
    "num_to_groups",
    "find_first",
]
