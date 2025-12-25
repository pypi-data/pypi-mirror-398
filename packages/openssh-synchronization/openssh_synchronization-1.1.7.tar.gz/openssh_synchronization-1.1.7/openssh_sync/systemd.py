#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenSSH同步服务的systemd管理模块
使用plsm库实现服务的注册、状态检查和注销功能
"""

import os
import sys
import shutil
import pwd
import grp
from typing import Optional, Dict

from plsm import ServiceManager, ServiceConfig, ServiceStatus

SERVICE_NAME = 'openssh-sync'


def get_service_manager(sudo: bool = True) -> ServiceManager:
    """
    获取服务管理器实例
    
    Args:
        sudo: 是否使用sudo权限
        
    Returns:
        ServiceManager: 服务管理器实例
    """
    return ServiceManager(sudo=sudo)


def get_service_info() -> Optional[ServiceStatus]:
    """
    获取服务信息
    
    Returns:
        Optional[ServiceStatus]: 服务状态信息，如果服务不存在则返回None
    """
    manager = get_service_manager()
    return manager.get_service_info(SERVICE_NAME)


def create_service_config() -> ServiceConfig:
    """
    创建服务配置
    
    Returns:
        ServiceConfig: 服务配置对象
    """
    # 获取当前用户和用户组
    current_user = pwd.getpwuid(os.getuid()).pw_name
    current_group = grp.getgrgid(os.getgid()).gr_name
    
    # 尝试获取已安装的命令路径
    command_path = shutil.which('openssh-sync')
    
    if command_path:
        # 如果找到了已安装的命令，使用它
        exec_start = f'{command_path} daemon'
    else:
        # 如果没有找到，回退到直接调用Python脚本
        executable = sys.executable
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cli.py')
        exec_start = f'{executable} {script_path} daemon'
    
    # 创建服务配置
    return ServiceConfig(
        name=SERVICE_NAME,
        description='OpenSSH Synchronization Service',
        exec_start=exec_start,
        working_directory='/opt/openssh',
        user=current_user,
        group=current_group,
        restart='always'
    )


def register_service(force: bool = False) -> Dict[str, bool]:
    """
    注册服务
    
    Args:
        force: 是否强制重新注册
        
    Returns:
        Dict[str, bool]: 包含注册、启用、启动状态的结果字典
    """
    manager = get_service_manager()
    service_info = get_service_info()
    
    if service_info and not force:
        # 服务已存在且非强制注册
        return {'registered': False, 'enabled': False, 'started': False, 'already_exists': True}
    
    # 如果服务存在且强制注册，则先移除
    if service_info and force:
        manager.remove_service(SERVICE_NAME)
    
    # 创建服务配置
    config = create_service_config()
    
    # 创建服务
    registered = manager.create_service(config)
    
    if registered:
        # 启用服务
        enabled = manager.enable_service(SERVICE_NAME)
        # 启动服务
        started = manager.start_service(SERVICE_NAME)
        return {
            'registered': True,
            'enabled': enabled,
            'started': started,
            'already_exists': False
        }
    else:
        return {
            'registered': False,
            'enabled': False,
            'started': False,
            'already_exists': False
        }


def unregister_service(force: bool = False) -> bool:
    """
    注销服务
    
    Args:
        force: 是否强制删除（即使服务正在运行）
        
    Returns:
        bool: 注销是否成功
    """
    manager = get_service_manager()
    service_info = get_service_info()
    
    if not service_info:
        return False
    
    # 如果服务正在运行，先停止
    if service_info.status.value == 'active':
        if force:
            manager.stop_service(SERVICE_NAME)
        else:
            return False
    
    # 删除服务
    return manager.remove_service(SERVICE_NAME)


def get_service_status() -> Dict[str, any]:
    """
    获取服务状态
    
    Returns:
        Dict[str, any]: 包含服务状态、加载状态、运行状态、健康状态的字典
    """
    manager = get_service_manager()
    service_info = get_service_info()
    
    if not service_info:
        return {'exists': False}
    
    # 检查服务健康状态
    is_healthy = manager.is_service_healthy(SERVICE_NAME)
    
    return {
        'exists': True,
        'status': service_info.status.value,
        'loaded': service_info.loaded,
        'running': service_info.running,
        'healthy': is_healthy
    }


def get_service_logs(lines: int = 10) -> Optional[str]:
    """
    获取服务日志
    
    Args:
        lines: 日志行数
        
    Returns:
        Optional[str]: 日志内容，如果获取失败则返回None
    """
    manager = get_service_manager()
    try:
        return manager.get_service_logs(SERVICE_NAME, lines=lines)
    except Exception:
        return None


def get_service_config_content() -> Optional[str]:
    """
    获取服务配置文件内容
    
    Returns:
        Optional[str]: 配置文件内容，如果文件不存在或无权限则返回None
    """
    service_file_path = f"/etc/systemd/system/{SERVICE_NAME}.service"
    try:
        with open(service_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, PermissionError):
        return None
