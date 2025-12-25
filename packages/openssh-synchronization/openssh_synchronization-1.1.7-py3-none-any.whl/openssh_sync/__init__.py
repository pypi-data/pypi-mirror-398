"""OpenSSH资源同步工具"""

__version__ = "1.1.7"
__author__ = "坐公交也用券"
__email__ = "liumou.site@qq.com"

# 导入结构化日志
from ColorInfo_liumou_Stable import ColorLogger, sugar

# 创建结构化日志记录器实例，所有模块共享
logger = sugar(ColorLogger(txt=False, fileinfo=True, basename=False))

from openssh_sync.main import OpenSSHSync
from openssh_sync.config import Config
from openssh_sync.fetcher import OpenSSHFetcher, create_fetcher
from openssh_sync.downloader import OpenSSHDownloader, create_downloader
from openssh_sync.utils import (
    parse_version,
    is_version_greater_or_equal,
    download_file,
)

__all__ = [
    "logger",
    "OpenSSHSync",
    "Config",
    "OpenSSHFetcher",
    "create_fetcher",
    "OpenSSHDownloader",
    "create_downloader",
    "parse_version",
    "is_version_greater_or_equal",
    "download_file",
]