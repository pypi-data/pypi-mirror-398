# CLI命令组模块
from .config import ConfigGroup
from .mllm import MllmGroup
from .data import DataGroup
from .service import ServiceGroup
from .doctor import DoctorGroup
from .help import HelpGroup
from .embedding import EmbeddingGroup
from .git import GitGroup
from .system import SystemGroup
from .mcp import MCPGroup

__all__ = [
    'ConfigGroup',
    'MllmGroup',
    'DataGroup',
    'ServiceGroup',
    'DoctorGroup',
    'HelpGroup',
    'EmbeddingGroup',
    'GitGroup',
    'SystemGroup',
    'MCPGroup',
]