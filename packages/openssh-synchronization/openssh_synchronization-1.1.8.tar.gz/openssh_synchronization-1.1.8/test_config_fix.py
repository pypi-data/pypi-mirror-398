#!/usr/bin/env python3
"""
测试配置修复功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from openssh_sync.config import Config
from openssh_sync import logger


def test_config_post_init():
    """测试__post_init__方法中的配置自动调整功能"""
    logger.info("开始测试配置修复功能")
    
    # 测试1：检查间隔小于12小时，应该自动调整
    logger.info("测试1: 检查间隔小于12小时的自动调整")
    config1 = Config(check_interval=6)
    assert config1.check_interval == 12, f"检查间隔应该自动调整为12小时，实际为{config1.check_interval}"
    logger.info(f"✓ 检查间隔自动调整成功：6小时 → {config1.check_interval}小时")
    
    # 测试2：下载目录以斜杠结尾，应该自动移除
    logger.info("测试2: 下载目录斜杠处理")
    config2 = Config(download_dir="/tmp/openssh/")
    assert not config2.download_dir.endswith('/'), f"下载目录不应该以斜杠结尾，实际为{config2.download_dir}"
    logger.info(f"✓ 下载目录斜杠处理成功：/tmp/openssh/ → {config2.download_dir}")
    
    # 测试3：正常检查间隔（≥12小时），不应该调整
    logger.info("测试3: 正常检查间隔保持不变")
    config3 = Config(check_interval=24)
    assert config3.check_interval == 24, f"检查间隔应该保持24小时不变，实际为{config3.check_interval}"
    logger.info(f"✓ 正常检查间隔保持成功：{config3.check_interval}小时")
    
    # 测试4：正常下载目录（不以斜杠结尾），不应该调整
    logger.info("测试4: 正常下载目录保持不变")
    config4 = Config(download_dir="/tmp/openssh")
    assert config4.download_dir == "/tmp/openssh", f"下载目录应该保持不变，实际为{config4.download_dir}"
    logger.info(f"✓ 正常下载目录保持成功：{config4.download_dir}")
    
    logger.info("所有配置修复测试通过！")


if __name__ == "__main__":
    test_config_post_init()
