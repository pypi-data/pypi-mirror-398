"""OpenSSH下载管理模块"""

import time
from pathlib import Path
from typing import List, Dict

from openssh_sync import logger
from .utils import download_file, get_file_modification_time
from .incremental_checker import IncrementalChecker


class OpenSSHDownloader:
    """OpenSSH下载管理类"""

    def __init__(self, download_dir: str = "./downloads", check_interval: int = 24):
        """使用下载配置初始化
        
        参数:
            download_dir: 下载文件的目录
            check_interval: 检查间隔（小时）
        """
        self.download_dir = Path(download_dir)
        self.check_interval = check_interval
        self.incremental_checker = IncrementalChecker(download_dir)

    def should_download(self, filename: str, mirror_size: str = "", mirror_date: str = "") -> bool:
        """检查文件是否应该下载
        
        参数:
            filename: 文件名
            mirror_size: 镜像站文件大小（可选）
            mirror_date: 镜像站文件日期（可选）
            
        返回:
            True表示文件应该下载
        """
        # 如果没有提供镜像站信息，使用传统的时间间隔检查
        if not mirror_size or not mirror_date:
            return self._should_download_legacy(filename)
        
        # 使用增量检查器进行完整检查
        need_update, reason = self.incremental_checker.should_update_file(filename, mirror_size, mirror_date)
        
        if not need_update:
            logger.info("跳过", reason=reason, filename=filename)
        
        return need_update
    
    def _should_download_legacy(self, filename: str) -> bool:
        """传统的基于时间间隔的检查（后备方案）
        
        参数:
            filename: 文件名
            
        返回:
            True表示文件应该下载
        """
        file_path = self.download_dir / filename
        
        # 如果文件不存在，下载它
        if not file_path.exists():
            return True
        
        # 检查文件是否比最小间隔更旧
        if self.check_interval > 0:
            file_mtime = get_file_modification_time(file_path)
            current_time = time.time()
            
            # 将小时转换为秒
            interval_seconds = self.check_interval * 3600
            
            if current_time - file_mtime > interval_seconds:
                return True
        
        return False

    def download_files(self, file_list: List[Dict[str, str]]) -> int:
        """从提供的列表中下载文件
        
        参数:
            file_list: 文件信息字典列表
            
        返回:
            成功下载的文件数量
        """
        # 如果下载目录不存在，创建它
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_count = 0
        
        # 获取更新摘要
        logger.info("分析文件更新需求")
        summary = self.incremental_checker.get_update_summary(file_list)
        
        logger.info("总计文件", total_files=summary['total_files'])
        logger.info("HTML记录", html_recorded=summary['html_recorded'])
        logger.info("需要更新", need_update=summary['need_update'])
        logger.info("跳过更新", skip_update=summary['skip_update'])
        logger.info("本地缺失", missing_local=summary['missing_local'])
        
        for file_info in file_list:
            filename = file_info['filename']
            url = file_info['url']
            mirror_size = file_info.get('size', '')
            mirror_date = file_info.get('mirror_date', '')
            
            # 使用新的增量检查逻辑
            if self.should_download(filename, mirror_size, mirror_date):
                logger.info("正在下载", filename=filename)
                
                if download_file(url, self.download_dir / filename):
                    # 保存镜像站日期信息
                    if mirror_date:
                        self._save_mirror_date(filename, mirror_date)
                    downloaded_count += 1
                    logger.info("成功下载", filename=filename)
                else:
                    logger.error("下载失败", filename=filename)
            else:
                # 即使跳过下载，也更新镜像站日期信息
                if mirror_date:
                    self._save_mirror_date(filename, mirror_date)
                # 跳过原因已在should_download中打印
        
        return downloaded_count
    
    def _save_mirror_date(self, filename: str, mirror_date: str):
        """保存镜像站日期信息到元数据文件
        
        参数:
            filename: 文件名
            mirror_date: 镜像站日期字符串
        """
        metadata_file = self.download_dir / f"{filename}.meta"
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(mirror_date)
        except Exception as e:
            logger.warning("保存镜像站日期失败", filename=filename, error=str(e))
    
    def get_mirror_date(self, filename: str) -> str:
        """获取保存的镜像站日期
        
        参数:
            filename: 文件名
            
        返回:
            镜像站日期字符串，如果不存在则返回空字符串
        """
        metadata_file = self.download_dir / f"{filename}.meta"
        try:
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning("读取镜像站日期失败", filename=filename, error=str(e))
        return ""

    def get_local_files(self) -> List[Dict[str, str]]:
        """获取本地下载的文件列表
        
        返回:
            本地文件信息列表
        """
        if not self.download_dir.exists():
            return []
        
        files = []
        for file_path in self.download_dir.glob("*.tar.gz"):
            if file_path.is_file():
                files.append({
                    'filename': file_path.name,
                    'local_path': str(file_path),
                    'size': file_path.stat().st_size if file_path.exists() else 0
                })
        
        return files


def create_downloader(download_dir: str = "./downloads", check_interval: int = 24) -> OpenSSHDownloader:
    """创建新的OpenSSH下载器实例
    
    参数:
        download_dir: 下载文件的目录
        check_interval: 检查间隔（小时）
        
    返回:
        OpenSSHDownloader实例
    """
    return OpenSSHDownloader(download_dir, check_interval)