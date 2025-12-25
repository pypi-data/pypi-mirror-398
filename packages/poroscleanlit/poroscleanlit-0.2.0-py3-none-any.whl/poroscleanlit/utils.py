# -*- coding: utf-8 -*-
"""辅助函数（文件读写等）"""

import os
from pathlib import Path
from typing import Optional, List
from .config import DEFAULT_ENCODING, SUPPORTED_EXTENSIONS


def read_file(file_path: str, encoding: str = DEFAULT_ENCODING) -> str:
    """
    读取文本文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码，默认为utf-8
        
    Returns:
        文件内容字符串
        
    Raises:
        FileNotFoundError: 文件不存在
        UnicodeDecodeError: 编码错误
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(
    file_path: str, 
    content: str, 
    encoding: str = DEFAULT_ENCODING,
    create_dirs: bool = True
) -> None:
    """
    写入文本文件
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认为utf-8
        create_dirs: 如果目录不存在是否创建
        
    Raises:
        IOError: 写入失败
    """
    path = Path(file_path)
    
    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def is_supported_file(file_path: str) -> bool:
    """
    检查文件扩展名是否支持
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否支持
    """
    path = Path(file_path)
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_file_encoding(file_path: str) -> Optional[str]:
    """
    尝试检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        检测到的编码，如果无法检测返回None
    """
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result.get('encoding')
    except ImportError:
        # 如果没有chardet，返回默认编码
        return DEFAULT_ENCODING
    except Exception:
        return None


def batch_process_files(
    input_dir: str,
    output_dir: str,
    processor: callable,
    file_pattern: str = "*.*",
    encoding: str = DEFAULT_ENCODING
) -> List[str]:
    """
    批量处理文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        processor: 处理函数，接受文本返回处理后的文本
        file_pattern: 文件匹配模式
        encoding: 文件编码
        
    Returns:
        处理后的文件路径列表
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processed_files = []
    
    for file_path in input_path.glob(file_pattern):
        if not file_path.is_file():
            continue
        
        if not is_supported_file(str(file_path)):
            continue
        
        try:
            # 读取文件
            content = read_file(str(file_path), encoding)
            
            # 处理内容
            processed_content = processor(content)
            
            # 写入输出目录
            output_file = output_path / file_path.name
            write_file(str(output_file), processed_content, encoding)
            
            processed_files.append(str(output_file))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return processed_files


def normalize_path(path: str) -> str:
    """
    规范化路径（统一使用正斜杠）
    
    Args:
        path: 路径字符串
        
    Returns:
        规范化后的路径
    """
    return str(Path(path)).replace('\\', '/')


def ensure_dir(dir_path: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
    """
    Path(dir_path).mkdir(parents=True, exist_ok=True)

