from .media import *
from .systemC import *

__version__ = "1.0.0"
__author__ = "@bilibili_秋天会有下雪天"
API_instance = {
    "MEDIA_C": WinMedia,  # 媒体工具
    "SYS_C": SYS_C  # 系统工具
}  # 对外部暴露的api实例
__all__ = [
    "WinMedia", "KeyMedia", "SYS_C",
    "API_instance",
    "__version__",
    "__author__",
]


