from __future__ import annotations
from typing import List, Dict, Union
from abc import ABCMeta, abstractmethod
from pathlib import Path


class Trie(metaclass=ABCMeta):
    trie = None
    rtrie = None

    def matches(self, word: str) -> list:
        matched_list = self.startwith(word)
        matched_list.extend(self.prefixes(word))
        return matched_list

    def __contains__(self, item):
        return item in self.trie

    @abstractmethod
    def prefixes(self, word: str) -> list:
        """在trie中匹配出所有可以作为word的前缀的keys

        Parameters
        ----------
        word : str
            待匹配词语
            
        Returns
        -------
        list
            Trie中所有匹配到的元素数组

        Example
        -------
        >>> trie = Trie(["ab", "bc", "bcd", "bcde"])
        >>> trie.prefixes("bcdf")
        ["bc", "bcd"]
        """

    def full_prefixes(self, word: str) -> list:
        full_matches = []
        for idx in range(len(word)):
            cur_word = word[idx:]
            lst = self.prefixes(cur_word)
            lst.sort(key=lambda x: len(x), reverse=True)
            full_matches.extend(lst)
        return full_matches

    @abstractmethod
    def startwith(self, word: str) -> list:
        """在前缀树中匹配出所有以word为前缀的keys

        Parameters
        ----------
        word : str
            待匹配词语
            
        Returns
        -------
        list
            Trie中所有匹配到的元素数组
        
        Example
        -------
        >>> trie = Trie(["ab", "bc", "bcd", "bcde"])
        >>> trie.startwith("bc")
        ["bc", "bcd", "bcde"]
        """

    @abstractmethod
    def endwith(self, word: str) -> list:
        """在前缀树中匹配出所有以word为后缀的keys

        Parameters
        ----------
        word : str
            待匹配词语

        Returns
        -------
        list
            Trie中所有匹配到的元素数组

        Example
        -------
        >>> trie = Trie(["bc", "abc", "bcd", "edbc"])
        >>> trie.endwith("bc")
        ["bc", "abc", "edbc"]
        """

    def has_keys_with_prefix(self, word):
        ...

    def save(self):
        ...

    def load(self, file_name: Union[str, Path]):
        ...


class PyTrie:
    def __init__(self, words: List[str]):
        self.trie = {}
        self._end = "eos"
        for word in words:
            self.add(word)

    def add(self, word):
        word = word.strip()
        assert word
        cur_node = self.trie
        for char in word:
            cur_node = cur_node.setdefault(char, {})
        # cur_node[self._end] = ""
        cur_node[self._end] = word

    def find(self, word: str, full=True) -> bool:
        """
        Parameters
        ----------
        full: bool
            True: 完全匹配时返回True
            False: 前缀匹配到则返回True
        """
        trie = self.trie
        for c in word:
            if c not in trie:
                return False
            trie = trie[c]
        if full:
            return self._end in trie
        else:
            return True

    def extract_longest_item(self, word: str):
        """从一个文本的开头开始匹配字典中最长的词，返回最长词和长度"""
        curr_dict, longest, offset = self.trie, None, 0

        if not word:
            return longest, offset

        for i, c in enumerate(word):
            if c not in curr_dict:
                return longest, offset
            curr_dict = curr_dict[c]
            if 'end' in curr_dict:
                longest, offset = curr_dict['end'], i + 1
        return longest, offset

    def __str__(self):
        return self.trie


class HatTrie(Trie):
    ...


class MarisaTrie(Trie):
    """Static memory-efficient Trie-like structures for Python
    based on marisa-trie C++ library.
    String data in a MARISA-trie may take up to 50x-100x less memory than in a standard Python dict;
    the raw lookup speed is comparable;
    trie also provides fast advanced methods like prefix search.
    """

    def __init__(self, key_list: list):
        import marisa_trie
        self.trie = marisa_trie.Trie(key_list)
        rkey_list = [i[::-1] for i in key_list]
        self.rtrie = marisa_trie.Trie(rkey_list)

    def prefixes(self, word: str):
        return self.trie.prefixes(word)

    def rprefixes(self, word: str):
        rword = word[::-1]
        return self.rtrie.prefixes(rword)

    def startwith(self, word: str):
        return self.trie.keys(word)

    def endwith(self, word: str):
        rword = word[::-1]
        return [i[::-1] for i in self.rtrie.keys(rword)]

    def get_longest(self, text):
        """匹配整个字典中最长的词，返回最长词"""
        if not text:
            return None

        longest = ''
        for idx, item in enumerate(text):
            items = self.trie.prefixes(text[idx:])

            for item in items:
                if len(item) > len(longest):
                    longest = item
        if longest == '':
            return None
        return longest

    def has_keys_with_prefix(self, word):
        return self.trie.has_keys_with_prefix(word)


class DaTrie(Trie):
    def __init__(self, word_list: list):
        import datrie
        self.trie = datrie.BaseTrie(word_list)
        rkey_list = [i[::-1] for i in word_list]
        self.rtrie = datrie.BaseTrie(rkey_list)

    def prefixes(self, name: str):
        return self.trie.prefixes(name)

    def startwith(self, name: str):
        return self.trie.startwith(name)

    def longest_prefix(self, word: str):
        return self.trie.longest_prefix(word)

    def has_keys_with_prefix(self, word):
        return self.trie.has_keys_with_prefix(word)


class AutomatonTrie:
    def __init__(self, key_list: list):
        import ahocorasick
        self.trie = ahocorasick.Automaton()
        for idx, key in enumerate(key_list):
            self.trie.add_word(key, (idx, key))

    def __contains__(self, item):
        return item in self.trie


class Benchmark:
    def __init__(self):
        from maque.performance import MeasureTime
        self.ms = MeasureTime()
        n = 2000000
        word_list = [str(i) for i in range(n)]
        self.ms.start()
        pytrie = PyTrie(word_list)
        self.ms.show_interval(f"pytrie build")
        mtrie = MarisaTrie(word_list)
        self.ms.show_interval(f"marisa trie build")

    def run(self):
        self.ms.start()


if __name__ == "__main__":
    from rich import print

    key_list = ['as', 'asdf', "basdfg", 'casd']
    t = MarisaTrie(key_list)
    print(t.startwith("as"))
    print(t.endwith("sd"))
    print('asd' in t)
    t2 = AutomatonTrie(key_list)
    print('asd' in t2)

    # print(t.rkeys("asd"))
    # t = AutomatonTrie(['as', '1asdf'])
    # print("a" in t.trie)
    # t = PyTrie(["a", "ab", "abc", "bc",
    #             "abcd"
    #             ])
    # print(t.find("abc"))
    # print(t.find("bcd", ))
    # Benchmark()
