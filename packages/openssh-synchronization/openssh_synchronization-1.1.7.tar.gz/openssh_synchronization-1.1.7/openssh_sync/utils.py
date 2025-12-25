"""OpenSSH同步工具实用函数模块"""

import re
import requests
from pathlib import Path
from typing import Tuple, Optional
from openssh_sync import logger


def parse_version(version_str: str) -> Optional[Tuple[int, int, int]]:
    """解析版本字符串
    
    参数:
        version_str: 版本字符串，如 "10.2p1" 或 "openssh-10.2p1.tar.gz"
        
    返回:
        Optional[Tuple[int, int, int]]: 解析后的版本元组，格式为 (主版本, 次版本, 修订版本)
        
    示例:
        >>> parse_version("10.2p1")
        (10, 2, 1)
        >>> parse_version("openssh-10.2p1.tar.gz")
        (10, 2, 1)
        >>> parse_version("invalid")
        None
    """
    # 从文件名中提取版本信息
    version_match = re.search(r'(\d+)\.(\d+)p(\d+)', version_str)
    if version_match:
        try:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            patch = int(version_match.group(3))
            return (major, minor, patch)
        except (ValueError, IndexError):
            return None
    return None


def is_version_greater_or_equal(version1: Tuple[int, int, int], 
                               version2: Tuple[int, int, int]) -> bool:
    """比较两个版本，判断version1是否大于等于version2
    
    参数:
        version1: 第一个版本，格式为 (主版本, 次版本, 修订版本)
        version2: 第二个版本，格式为 (主版本, 次版本, 修订版本)
        
    返回:
        bool: 如果version1 >= version2则返回True，否则返回False
        
    示例:
        >>> is_version_greater_or_equal((10, 2, 1), (10, 2, 1))
        True
        >>> is_version_greater_or_equal((10, 3, 0), (10, 2, 1))
        True
        >>> is_version_greater_or_equal((10, 1, 0), (10, 2, 1))
        False
    """
    for v1, v2 in zip(version1, version2):
        if v1 > v2:
            return True
        elif v1 < v2:
            return False
    return True  # 所有版本号都相等


def download_file(url: str, file_path: Path, timeout: int = 30) -> bool:
    """下载文件到指定路径
    
    参数:
        url: 文件下载URL
        file_path: 本地保存路径
        timeout: 请求超时时间（秒），默认30秒
        
    返回:
        bool: 下载是否成功
        
    示例:
        >>> download_file(
        ...     "https://mirrors.aliyun.com/openssh/portable/openssh-10.2p1.tar.gz",
        ...     Path("/tmp/openssh-10.2p1.tar.gz"),
        ...     timeout=30
        ... )
        True
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载文件
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
        
    except requests.RequestException as e:
        logger.error("下载文件失败", url=url, error=str(e))
        return False





def get_file_modification_time(file_path: Path) -> float:
    """获取文件的修改时间
    
    参数:
        file_path: 文件路径
        
    返回:
        float: 文件修改时间的时间戳
        
    示例:
        >>> get_file_modification_time(Path("/tmp/test.txt"))
        1640995200.0
    """
    if file_path.exists():
        return file_path.stat().st_mtime
    return 0.0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读的格式
    
    参数:
        size_bytes: 文件大小（字节）
        
    返回:
        str: 格式化后的文件大小字符串
        
    示例:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
        >>> format_file_size(1073741824)
        '1.0 GB'
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def validate_url(url: str) -> bool:
    """验证URL格式是否有效
    
    参数:
        url: 要验证的URL
        
    返回:
        bool: URL是否有效
        
    示例:
        >>> validate_url("https://mirrors.aliyun.com/openssh/portable")
        True
        >>> validate_url("invalid-url")
        False
    """
    try:
        result = requests.utils.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def cleanup_old_files(directory: Path, keep_count: int = 5) -> None:
    """清理旧文件，只保留指定数量的最新文件
    
    参数:
        directory: 要清理的目录
        keep_count: 要保留的文件数量，默认保留5个最新文件
        
    示例:
        >>> cleanup_old_files(Path("/tmp/openssh"), keep_count=3)
        # 只保留最新的3个文件，删除其他旧文件
    """
    if not directory.exists():
        return
    
    # 获取所有tar.gz文件并按修改时间排序
    tar_files = list(directory.glob("*.tar.gz"))
    tar_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # 删除旧文件
    for old_file in tar_files[keep_count:]:
        try:
            old_file.unlink()
            logger.info("已删除旧文件", filename=old_file.name)
        except OSError as e:
            logger.error("删除文件失败", filename=old_file.name, error=str(e))