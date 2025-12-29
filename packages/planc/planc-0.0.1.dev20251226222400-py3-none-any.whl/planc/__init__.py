"""package.

...
"""

__version__ = "0.0.1dev20251226222400"

from enum import Enum

# 从_dag模块导入topological_sort_dfs函数，使其成为公共API
from ._common import _topo_sort


class TagNames(str, Enum):
    RESOURCE = "qpa_name"
    PROJECT = "qpa_project_name"


# core.py：包的功能实现模块

# 显式声明公共API，提高代码可读性和安全性
__all__ = [
    "_topo_sort",
    "__version__",
    "TagNames",
]
