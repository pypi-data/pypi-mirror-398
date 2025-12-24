# 版本信息
__version__ = '0.1.1'

# 导出utils和mm模块
from . import utils
from . import mm

# 定义 __all__ 控制 from fvgtools import * 的行为
__all__ = ['utils', 'mm', '__version__']

# 可选：包级别初始化（如日志、全局配置）
print("Initializing fvgtools...")