# -*- coding: utf-8 -*-
"""Utility functions (file I/O, etc.)"""

import os
from pathlib import Path
from typing import Optional, List
from .config import DEFAULT_ENCODING, SUPPORTED_EXTENSIONS


def read_file(file_path: str, encoding: str = DEFAULT_ENCODING) -> str:
    """
    Read text file
    
    Args:
        file_path: File path
        encoding: File encoding, defaults to utf-8
        
    Returns:
        File content string
        
    Raises:
        FileNotFoundError: File not found
        UnicodeDecodeError: Encoding error
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
    Write text file
    
    Args:
        file_path: File path
        content: Content to write
        encoding: File encoding, defaults to utf-8
        create_dirs: Whether to create directories if they don't exist
        
    Raises:
        IOError: Write failure
    """
    path = Path(file_path)
    
    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def is_supported_file(file_path: str) -> bool:
    """
    Check if file extension is supported
    
    Args:
        file_path: File path
        
    Returns:
        Whether supported
    """
    path = Path(file_path)
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_file_encoding(file_path: str) -> Optional[str]:
    """
    Try to detect file encoding
    
    Args:
        file_path: File path
        
    Returns:
        Detected encoding, returns None if unable to detect
    """
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result.get('encoding')
    except ImportError:
        # If chardet not available, return default encoding
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
    Batch process files
    
    Args:
        input_dir: Input directory
        output_dir: Output directory
        processor: Processing function that takes text and returns processed text
        file_pattern: File matching pattern
        encoding: File encoding
        
    Returns:
        List of processed file paths
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
            # Read file
            content = read_file(str(file_path), encoding)
            
            # Process content
            processed_content = processor(content)
            
            # Write to output directory
            output_file = output_path / file_path.name
            write_file(str(output_file), processed_content, encoding)
            
            processed_files.append(str(output_file))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return processed_files


def normalize_path(path: str) -> str:
    """
    Normalize path (unify to use forward slashes)
    
    Args:
        path: Path string
        
    Returns:
        Normalized path
    """
    return str(Path(path)).replace('\\', '/')


def ensure_dir(dir_path: str) -> None:
    """
    Ensure directory exists, create if it doesn't exist
    
    Args:
        dir_path: Directory path
    """
    Path(dir_path).mkdir(parents=True, exist_ok=True)

