"""HTML生成器模块 - 生成类似阿里云镜像站的静态文件列表页面"""

import os
import time
from typing import List, Dict
from datetime import datetime

from .downloader import create_downloader
from openssh_sync import logger


class HTMLGenerator:
    """HTML生成器类"""
    
    def __init__(self, download_dir: str):
        """初始化HTML生成器
        
        参数:
            download_dir: 下载目录路径
        """
        self.download_dir = download_dir
        self.downloader = create_downloader(download_dir)
    
    def generate_html(self, files: List[Dict[str, str]]) -> str:
        """生成HTML页面
        
        参数:
            files: 文件信息列表
            
        返回:
            HTML内容字符串
        """
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 生成HTML头部
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenSSH Portable Releases</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .file-list {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .file-list th,
        .file-list td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .file-list th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .file-list tr:hover {{
            background-color: #f8f9fa;
        }}
        .file-link {{
            color: #0366d6;
            text-decoration: none;
        }}
        .file-link:hover {{
            text-decoration: underline;
        }}
        .parent-dir {{
            margin-bottom: 20px;
        }}
        .parent-dir a {{
            color: #0366d6;
            text-decoration: none;
        }}
        .parent-dir a:hover {{
            text-decoration: underline;
        }}
        .last-modified {{
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Index of /openssh/portable</h1>
        
        <div class="parent-dir">
            <a href="../">Parent directory/</a>
        </div>
        
        <table class="file-list">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Size</th>
                    <th>Date</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 添加文件行
        for file_info in files:
            filename = file_info.get('filename', '')
            last_modified = file_info.get('last_modified', '')
            size = file_info.get('size', '')
            
            html += f"""                <tr>
                    <td><a href="{filename}" class="file-link">{filename}</a></td>
                    <td>{size}</td>
                    <td>{last_modified}</td>
                </tr>
"""
        
        # 生成HTML尾部
        html += f"""            </tbody>
        </table>
        
        <div class="last-modified">
            Last updated: {current_time}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def scan_downloaded_files(self) -> List[Dict[str, str]]:
        """扫描下载目录中的文件
        
        返回:
            文件信息列表（仅包含.tar.gz和.tar.gz.asc文件）
        """
        files = []
        
        if not os.path.exists(self.download_dir):
            return files
        
        # 扫描目录中的所有文件
        for filename in os.listdir(self.download_dir):
            file_path = os.path.join(self.download_dir, filename)
            
            if os.path.isfile(file_path):
                # 只处理.tar.gz和.tar.gz.asc文件
                if filename.endswith('.tar.gz') or filename.endswith('.tar.gz.asc'):
                    # 获取文件信息
                    stat = os.stat(file_path)
                    size = self._format_file_size(stat.st_size)
                    
                    # 优先使用镜像站日期，如果没有则使用本地文件系统日期
                    mirror_date = self.downloader.get_mirror_date(filename)
                    if mirror_date:
                        last_modified = mirror_date
                    else:
                        last_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    # 根据文件名生成描述
                    description = self._get_file_description(filename)
                    
                    files.append({
                        'filename': filename,
                        'last_modified': last_modified,
                        'size': size,
                        'description': description
                    })
        
        # 按文件名排序
        files.sort(key=lambda x: x['filename'])
        
        return files
    
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
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _get_file_description(self, filename: str) -> str:
        """根据文件名生成描述
        
        参数:
            filename: 文件名
            
        返回:
            文件描述
        """
        if filename.startswith('openssh-') and filename.endswith('.tar.gz'):
            return "OpenSSH source code"
        elif filename.endswith('.asc'):
            return "GPG signature"
        elif filename.endswith('.diff.gz'):
            return "Diff vs OpenBSD"
        elif filename in ['ChangeLog', 'INSTALL', 'README', 'TODO', 'UPGRADING']:
            return "Documentation"
        elif 'deprecated' in filename:
            return "Deprecated key"
        else:
            return "-"
    
    def generate_index_html(self) -> bool:
        """生成index.html文件
        
        返回:
            True表示成功，False表示失败
        """
        try:
            # 扫描下载的文件
            files = self.scan_downloaded_files()
            
            # 生成HTML内容
            html_content = self.generate_html(files)
            
            # 写入index.html文件
            index_path = os.path.join(self.download_dir, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info("已生成index.html文件", files_count=len(files))
            return True
            
        except Exception as e:
            logger.error("生成index.html失败", error=str(e))
            return False


def create_html_generator(download_dir: str) -> HTMLGenerator:
    """创建HTML生成器实例
    
    参数:
        download_dir: 下载目录路径
        
    返回:
        HTMLGenerator实例
    """
    return HTMLGenerator(download_dir)