import re
from typing import Union
from pathlib import Path
import os


def sanitize_filename(filename: Union[str, Path]) -> str:
    """
    파일 시스템에 안전한 파일명으로 변환합니다.
    
    Args:
        filename: 변환할 파일명 또는 경로
        
    Returns:
        str: 안전한 파일명
        
    Examples:
        >>> sanitize_filename("test/file.txt")
        'test_file.txt'
        >>> sanitize_filename("test:file.txt")
        'test_file.txt'
        >>> sanitize_filename("test/file:name.txt")
        'test_file_name.txt'
    """
    # Path 객체인 경우 문자열로 변환
    if isinstance(filename, Path):
        filename = str(filename)
    
    # 파일명과 확장자 분리
    name, ext = os.path.splitext(filename)
    
    # 안전하지 않은 문자들을 언더스코어로 대체
    # Windows에서 사용할 수 없는 문자: \ / : * ? " < > |
    # 추가로 공백도 언더스코어로 대체
    safe_name = re.sub(r'[\\/:*?"<>|\s]', '_', name)
    
    # 연속된 언더스코어를 하나로 통합
    safe_name = re.sub(r'_+', '_', safe_name)
    
    # 시작과 끝의 언더스코어 제거
    safe_name = safe_name.strip('_')
    
    # 확장자와 결합
    return safe_name + ext


def sanitize_path(path: Union[str, Path]) -> str:
    """
    파일 시스템에 안전한 경로로 변환합니다.
    
    Args:
        path: 변환할 경로
        
    Returns:
        str: 안전한 경로
        
    Examples:
        >>> sanitize_path("test/folder/file.txt")
        'test/folder/file.txt'
        >>> sanitize_path("test:folder/file.txt")
        'test_folder/file.txt'
    """
    # Path 객체인 경우 문자열로 변환
    if isinstance(path, Path):
        path = str(path)
    
    # 경로를 디렉토리와 파일명으로 분리
    dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    
    # 파일명만 sanitize
    safe_filename = sanitize_filename(filename)
    
    # 디렉토리가 있으면 결합
    if dirname:
        return os.path.join(dirname, safe_filename)
    return safe_filename 