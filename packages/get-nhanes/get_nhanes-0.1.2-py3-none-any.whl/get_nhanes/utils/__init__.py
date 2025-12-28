"""
Utils package initialization.
Exposes convenient functions from submodules.
"""

from .getMetricsConvenient import *  # 导入所有来自getMetricsConvenient的功能
from .racialReconstruction import race_combine

# 显式声明公开接口
__all__ = [
    "get_nhanes_data",
    "save_result",
    "sort_by_seqn",
    "race_combine"
]

# 可选：添加包版本信息
__version__ = '0.1.0'

