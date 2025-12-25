from .text_cleaner import TextCleaner

# 导入插件模块以确保注册 (这些模块内部会向 PluginRegistry 注册插件)
from . import unicode_norm  # Unicode归一化插件

__version__ = "0.2.0"
__all__ = ["TextCleaner"]


