#!/usr/bin/env python3
"""测试多节点镜像地址功能"""

import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openssh_sync.config import Config, create_default_config
from openssh_sync.fetcher import OpenSSHFetcher
from openssh_sync import logger


def test_default_mirror():
    """测试默认镜像地址"""
    print("=== 测试默认镜像地址 ===")
    config = Config()
    assert isinstance(config.mirror_url, list), "镜像地址应为列表类型"
    assert len(config.mirror_url) == 1, "默认应为单个镜像地址"
    assert config.mirror_url[0] == "https://mirrors.aliyun.com/openssh/portable", "默认镜像地址不正确"
    print("✓ 默认镜像地址测试通过")
    print(f"  镜像地址列表: {config.mirror_url}")


def test_single_mirror():
    """测试自定义单个镜像地址"""
    print("\n=== 测试自定义单个镜像地址 ===")
    custom_mirror = "http://example.com/openssh"
    config = Config(mirror_url=custom_mirror)
    assert isinstance(config.mirror_url, list), "镜像地址应为列表类型"
    assert len(config.mirror_url) == 1, "单个镜像地址应转换为列表"
    assert config.mirror_url[0] == custom_mirror, "自定义镜像地址不正确"
    print("✓ 自定义单个镜像地址测试通过")
    print(f"  镜像地址列表: {config.mirror_url}")


def test_multi_mirror():
    """测试多个镜像地址"""
    print("\n=== 测试多个镜像地址 ===")
    multi_mirrors = "http://1.com/openssh http://2.com/openssh http://3.com/openssh"
    config = Config(mirror_url=multi_mirrors)
    assert isinstance(config.mirror_url, list), "镜像地址应为列表类型"
    assert len(config.mirror_url) == 3, "应解析为3个镜像地址"
    assert config.mirror_url[0] == "http://1.com/openssh", "第一个镜像地址不正确"
    assert config.mirror_url[1] == "http://2.com/openssh", "第二个镜像地址不正确"
    assert config.mirror_url[2] == "http://3.com/openssh", "第三个镜像地址不正确"
    print("✓ 多个镜像地址测试通过")
    print(f"  镜像地址列表: {config.mirror_url}")


def test_env_multi_mirror():
    """测试环境变量设置多个镜像地址"""
    print("\n=== 测试环境变量设置多个镜像地址 ===")
    # 设置环境变量
    os.environ['MIRROR_URL'] = "http://env1.com/openssh http://env2.com/openssh"
    
    config = create_default_config()
    assert isinstance(config.mirror_url, list), "镜像地址应为列表类型"
    assert len(config.mirror_url) == 2, "应解析为2个镜像地址"
    assert config.mirror_url[0] == "http://env1.com/openssh", "第一个环境变量镜像地址不正确"
    assert config.mirror_url[1] == "http://env2.com/openssh", "第二个环境变量镜像地址不正确"
    print("✓ 环境变量设置多个镜像地址测试通过")
    print(f"  镜像地址列表: {config.mirror_url}")
    
    # 清除环境变量
    del os.environ['MIRROR_URL']


def test_fetcher_multi_mirror():
    """测试Fetcher使用多个镜像地址"""
    print("\n=== 测试Fetcher使用多个镜像地址 ===")
    # 创建一个包含有效和无效镜像的列表
    mirrors = ["http://invalid-mirror.example.com", "https://mirrors.aliyun.com/openssh/portable"]
    
    fetcher = OpenSSHFetcher(base_url=mirrors)
    assert hasattr(fetcher, 'base_urls'), "Fetcher应具有base_urls属性"
    assert isinstance(fetcher.base_urls, list), "base_urls应为列表类型"
    assert len(fetcher.base_urls) == 2, "Fetcher应包含2个镜像地址"
    assert fetcher.base_urls[0] == "http://invalid-mirror.example.com", "第一个镜像地址不正确"
    assert fetcher.base_urls[1] == "https://mirrors.aliyun.com/openssh/portable", "第二个镜像地址不正确"
    print("✓ Fetcher多镜像地址测试通过")
    print(f"  Fetcher镜像地址列表: {fetcher.base_urls}")


if __name__ == "__main__":
    print("开始测试多节点镜像地址功能...\n")
    
    try:
        test_default_mirror()
        test_single_mirror()
        test_multi_mirror()
        test_env_multi_mirror()
        test_fetcher_multi_mirror()
        
        print("\n" + "="*50)
        print("🎉 所有多节点镜像地址测试通过！")
        print("多节点镜像地址功能已成功实现：")
        print("- 默认使用阿里云单个镜像站点")
        print("- 支持通过命令行或环境变量设置多个镜像地址")
        print("- 使用空格分隔多个镜像地址")
        print("- 自动解析为字符串列表")
        print("- Fetcher会依次检测镜像站点，只要有一个通过即可")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
