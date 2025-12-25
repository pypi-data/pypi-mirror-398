# weixinauto/__init__.py
from .wechat import Wechat
from . import wechat  # 把模块也挂到包上

__all__ = ["Wechat"]
__version__: str
