"""OpenSSH资源获取模块"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from urllib.parse import urljoin

from .utils import is_version_greater_or_equal
from openssh_sync import logger


class OpenSSHFetcher:
    """OpenSSH资源获取类"""

    def __init__(self, base_url: list = None):
        """使用基础URL初始化
        
        参数:
            base_url: OpenSSH镜像的基础URL列表
        """
        # 如果未提供镜像列表或不是列表，使用默认阿里云镜像
        if not base_url or not isinstance(base_url, list):
            self.base_urls = ["https://mirrors.aliyun.com/openssh/portable"]
        else:
            self.base_urls = base_url

    def fetch_file_list(self, min_version: Tuple[int, int, int] = (0, 0, 0)) -> List[Dict[str, str]]:
        """从镜像获取OpenSSH文件列表，支持多节点检测
        
        参数:
            min_version: 最低版本要求 (主版本, 次版本, 修订版本)
            
        返回:
            文件信息字典列表
        """
        # 依次尝试每个镜像地址
        for base_url in self.base_urls:
            try:
                logger.info(f"尝试从镜像获取文件列表: {base_url}")
                response = requests.get(base_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                files = []
                
                # 解析HTML表格结构
                for row in soup.find_all('tr'):
                    # 在行中查找文件链接
                    link = row.find('a')
                    if not link:
                        continue
                        
                    href = link.get('href')
                    if href and href.endswith('.tar.gz') and 'openssh-' in href:
                        # 清理href中的换行符和空格
                        href = href.strip()
                        
                        # 从文件名中提取版本
                        version_match = re.search(r'openssh-(\d+)\.(\d+)p(\d+)', href)
                        if version_match:
                            major = int(version_match.group(1))
                            minor = int(version_match.group(2))
                            patch = int(version_match.group(3))
                            
                            # 检查版本是否满足最低要求
                            if is_version_greater_or_equal((major, minor, patch), min_version):
                                # 在同一行中查找文件大小
                                size_cell = row.find('td', class_='size')
                                file_size = size_cell.text.strip() if size_cell else '未知大小'
                                
                                # 在同一行中查找文件修改日期
                                date_cell = row.find('td', class_='date')
                                mirror_date = date_cell.text.strip() if date_cell else ''
                                
                                # 构建完整的URL - 确保保留基础URL的完整路径
                                if base_url.endswith('/'):
                                    full_url = base_url + href
                                else:
                                    full_url = base_url + '/' + href
                                
                                files.append({
                                    'filename': href,
                                    'url': full_url,
                                    'version': (major, minor, patch),
                                    'size': file_size,
                                    'mirror_date': mirror_date
                                })
                
                if files:
                    logger.info(f"从镜像 {base_url} 获取文件列表成功")
                    return sorted(files, key=lambda x: x['version'], reverse=True)
                
            except requests.RequestException as e:
                logger.warning(f"从镜像 {base_url} 获取文件列表失败，尝试下一个镜像", error=str(e))
        
        logger.error("所有镜像均获取文件列表失败")
        return []
    
    def get_latest_version(self, min_version: Tuple[int, int, int] = (0, 0, 0)) -> Dict[str, str]:
        """获取最新的可用版本信息
        
        参数:
            min_version: 最低版本要求
            
        返回:
            最新版本文件信息，如果没有找到则返回空字典
        """
        files = self.fetch_file_list(min_version)
        return files[0] if files else {}


def create_fetcher(base_url: list = None) -> OpenSSHFetcher:
    """创建新的OpenSSH获取器实例
    
    参数:
        base_url: OpenSSH镜像的基础URL列表
        
    返回:
        OpenSSHFetcher实例
    """
    return OpenSSHFetcher(base_url)