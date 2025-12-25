"""增量更新检查模块"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from openssh_sync import logger


class IncrementalChecker:
    """增量更新检查器"""
    
    def __init__(self, download_dir: str):
        """初始化检查器
        
        参数:
            download_dir: 下载目录路径
        """
        self.download_dir = Path(download_dir)
        self.html_file = self.download_dir / "index.html"
    
    def parse_html_index(self, html_file: str = None) -> Dict[str, Dict[str, str]]:
        """解析HTML索引文件，提取文件信息
        
        参数:
            html_file: HTML文件路径（可选，默认使用download_dir/index.html）
            
        返回:
            文件信息字典，key为文件名，value包含size和date信息
        """
        if html_file is None:
            html_file = self.html_file
        else:
            html_file = Path(html_file)
            
        if not html_file.exists():
            return {}
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            files_info = {}
            
            # 使用正则表达式提取文件行
            # 匹配格式: <td><a href="filename" class="file-link">filename</a></td>
            #           <td>size</td>
            #           <td>date</td>
            pattern = r'<td><a href="([^"]+)"[^>]*>[^<]+</a></td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>'
            
            matches = re.findall(pattern, html_content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                filename, size, date = match
                files_info[filename] = {
                    'size': size.strip(),
                    'date': date.strip()
                }
            
            return files_info
            
        except Exception as e:
            logger.warning("解析HTML文件失败", html_file=str(html_file), error=str(e))
            return {}
    
    def get_local_file_info(self, filename: str) -> Optional[Dict[str, str]]:
        """获取本地文件信息
        
        参数:
            filename: 文件名
            
        返回:
            文件信息字典，包含size和mtime，文件不存在返回None
        """
        file_path = self.download_dir / filename
        
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            size_bytes = stat.st_size
            
            # 格式化文件大小
            size_str = self._format_file_size(size_bytes)
            
            return {
                'size': size_str,
                'size_bytes': size_bytes,  # 原始字节数用于精确比较
                'exists': True
            }
        except Exception as e:
            logger.warning("获取文件信息失败", filename=filename, error=str(e))
            return None
    
    def should_update_file(self, filename: str, mirror_size: str, mirror_date: str) -> Tuple[bool, str]:
        """判断文件是否需要更新
        
        参数:
            filename: 文件名
            mirror_size: 镜像站文件大小（格式化后的字符串）
            mirror_date: 镜像站文件日期
            
        返回:
            (是否需要更新, 原因说明)
        """
        # 1. 检查本地文件是否存在
        local_info = self.get_local_file_info(filename)
        if not local_info:
            return True, "本地文件不存在"
        
        # 2. 检查HTML索引中是否有记录
        html_files = self.parse_html_index()
        if filename not in html_files:
            return True, "HTML索引中无记录"
        
        html_info = html_files[filename]
        
        # 3. 比较文件大小
        if html_info['size'] != mirror_size:
            return True, f"文件大小不匹配 (HTML: {html_info['size']}, 镜像: {mirror_size})"
        
        if local_info['size'] != mirror_size:
            return True, f"本地文件大小不匹配 (本地: {local_info['size']}, 镜像: {mirror_size})"
        
        # 4. 比较文件日期（可选检查）
        if html_info['date'] != mirror_date:
            return True, f"文件日期不匹配 (HTML: {html_info['date']}, 镜像: {mirror_date})"
        
        # 5. 所有检查通过，无需更新
        return False, "文件已是最新"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小
        
        参数:
            size_bytes: 文件大小（字节）
            
        返回:
            格式化后的文件大小字符串
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def get_update_summary(self, mirror_files: list) -> Dict[str, any]:
        """获取更新摘要
        
        参数:
            mirror_files: 镜像站文件列表
            
        返回:
            更新摘要信息
        """
        html_files = self.parse_html_index()
        
        summary = {
            'total_files': len(mirror_files),
            'html_recorded': len(html_files),
            'need_update': 0,
            'skip_update': 0,
            'missing_local': 0,
            'details': []
        }
        
        for file_info in mirror_files:
            filename = file_info['filename']
            mirror_size = file_info['size']
            mirror_date = file_info.get('mirror_date', '')
            
            need_update, reason = self.should_update_file(filename, mirror_size, mirror_date)
            
            if need_update:
                summary['need_update'] += 1
                summary['details'].append({
                    'filename': filename,
                    'action': 'update',
                    'reason': reason
                })
            else:
                summary['skip_update'] += 1
                summary['details'].append({
                    'filename': filename,
                    'action': 'skip',
                    'reason': reason
                })
            
            # 检查本地文件是否存在
            local_info = self.get_local_file_info(filename)
            if not local_info:
                summary['missing_local'] += 1
        
        return summary