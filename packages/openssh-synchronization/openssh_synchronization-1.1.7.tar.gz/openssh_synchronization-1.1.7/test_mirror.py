#!/usr/bin/env python3
"""
测试镜像地址功能
"""

import os
import sys
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from openssh_sync import logger
from openssh_sync.config import Config
from openssh_sync.fetcher import create_fetcher


def test_mirror_url():
    """测试镜像地址功能"""
    logger.info("开始测试镜像地址功能")
    
    # 测试1：默认镜像地址
    logger.info("测试1: 默认镜像地址")
    config1 = Config()
    logger.info("创建默认配置", mirror_url=config1.mirror_url)
    assert config1.mirror_url == "https://mirrors.aliyun.com/openssh/portable", "默认镜像地址不正确"
    
    # 测试2：自定义镜像地址
    logger.info("\n测试2: 自定义镜像地址")
    custom_mirror = "https://example.com/openssh/portable"
    config2 = Config(mirror_url=custom_mirror)
    logger.info("创建自定义配置", mirror_url=config2.mirror_url)
    assert config2.mirror_url == custom_mirror, "自定义镜像地址不正确"
    
    # 测试3：环境变量设置镜像地址
    logger.info("\n测试3: 环境变量设置镜像地址")
    os.environ['MIRROR_URL'] = "https://env.example.com/openssh/portable"
    from openssh_sync.config import create_default_config
    config3 = create_default_config()
    logger.info("从环境变量创建配置", mirror_url=config3.mirror_url)
    assert config3.mirror_url == "https://env.example.com/openssh/portable", "环境变量镜像地址不正确"
    # 清理环境变量
    del os.environ['MIRROR_URL']
    
    # 测试4：fetcher使用镜像地址
    logger.info("\n测试4: Fetcher使用镜像地址")
    test_mirror = "https://test.example.com/openssh/portable"
    fetcher = create_fetcher(base_url=test_mirror)
    assert fetcher.base_url == test_mirror, "Fetcher镜像地址不正确"
    logger.info("创建Fetcher", base_url=fetcher.base_url)
    
    logger.info("\n所有测试通过！镜像地址功能正常工作。")


if __name__ == "__main__":
    test_mirror_url()
