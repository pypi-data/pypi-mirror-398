import importlib.metadata
import importlib.util


def _is_package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _get_package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "0.0.0"


def is_flash_attn2_available():
    return _is_package_available("flash_attn") and _get_package_version("flash_attn").startswith("2")


def is_jieba_available():
    return _is_package_available("jieba")

def is_levenshtein_available():
    return _is_package_available("Levenshtein")

def is_nltk_available():
    return _is_package_available("nltk")


def is_rouge_available():
    return _is_package_available("rouge_chinese")
