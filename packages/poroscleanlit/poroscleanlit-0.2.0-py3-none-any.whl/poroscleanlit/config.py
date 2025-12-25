# -*- coding: utf-8 -*-
"""配置和常量管理"""

# 默认配置
DEFAULT_ENCODING = "utf-8"
DEFAULT_CHUNK_SIZE = 1024 * 4  # 4KB

# 支持的文件扩展名
# 注意：LaTeX空格清理功能适用于所有包含LaTeX公式的文本文件格式
# 包括但不限于：Markdown (.md)、JSON (.json)、纯文本 (.txt)、LaTeX源文件 (.tex, .latex) 等
SUPPORTED_EXTENSIONS = {".txt", ".md", ".tex", ".latex", ".json"}

# 日志级别
LOG_LEVEL = "INFO"

# 默认清洗选项
# 注意：基础清洗功能（normalize_whitespace, remove_extra_spaces）已移入默认 pipeline
# 这里只保留高级可选功能
DEFAULT_CLEAN_OPTIONS = {
    # 是否清理 LaTeX 数学公式内部的多余空格（如：\mathbf { X } -> \mathbf{X}）
    # 默认关闭，避免对已有行为产生影响，需要时显式开启
    "clean_latex_math_spaces": False,
}

