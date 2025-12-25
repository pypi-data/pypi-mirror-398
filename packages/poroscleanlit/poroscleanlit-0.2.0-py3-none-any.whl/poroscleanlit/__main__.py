# -*- coding: utf-8 -*-
"""PorosCleanlit 包的主入口点

允许通过 `python -m PorosCleanlit` 运行演示代码
"""

import sys
import os

# 设置 Windows 控制台编码为 UTF-8
if sys.platform == "win32":
    # 方法1：设置环境变量
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # 方法2：尝试设置控制台代码页（如果可能）
    try:
        import subprocess
        subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
    except:
        pass
    # 方法3：重新配置标准输出编码
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from . import __version__, TextCleaner
from .greek_latex_converter import GreekLatexConverter


def main():
    """主入口函数"""
    run_demo()


def run_demo():
    """运行演示代码"""
    print("=" * 60)
    print(f"PorosCleanlit v{__version__} - 文本清洗工具包")
    print("=" * 60)
    print()
    
    # 基本使用示例
    print("基本使用示例：")
    print("-" * 60)
    
    cleaner = TextCleaner()
    test_text = "这是一个  测试文本。包含α粒子、β射线。"
    
    print(f"原始文本: {test_text}")
    cleaned = cleaner.clean(test_text)
    print(f"清洗后: {cleaned}")
    print()
    
    # 希腊字母转换示例
    print("希腊字母转换示例：")
    print("-" * 60)
    
    converter = GreekLatexConverter()
    greek_text = "α粒子、β射线、γ辐射"
    latex_text = converter.to_latex(greek_text)
    
    print(f"原始: {greek_text}")
    print(f"转换为LaTeX: {latex_text}")
    print()
    
    print("=" * 60)
    print("提示：更多示例请查看 PorosCleanlit/examples/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    """运行演示代码"""
    main()

