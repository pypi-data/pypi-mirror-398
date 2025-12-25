#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSSH同步工具容器镜像构建及运行管理脚本

该脚本提供完整的Docker容器管理功能，包括：
- 构建镜像
- 运行容器
- 停止容器
- 删除容器
- 查看容器状态
- 查看容器日志

使用方法：
    python docker_manager.py [命令] [选项]

示例：
    python docker_manager.py build
    python docker_manager.py run
    python docker_manager.py stop
    python docker_manager.py status
"""

import os
import sys
import subprocess
import argparse
import time
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any


class DockerManager:
    """Docker容器管理器"""
    
    def __init__(self, project_root: str = "."):
        """
        初始化Docker管理器
        
        参数:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root).resolve()
        self.image_name = "openssh-synchronization"
        self.container_name = "openssh-synchronization"
        self.data_dir = self.project_root / "data"
        
        # 检测系统架构
        self.arch = self.detect_architecture()
        print(f"🔍 检测到系统架构: {self.arch}")
        
        # 根据架构设置私有仓库配置
        self.registry_url = "harbor.liumou.site"
        if self.arch == "arm64":
            self.registry_repo = "arm64/openssh-synchronization"
        elif self.arch == "amd64":
            self.registry_repo = "x86/openssh-synchronization"
        else:
            # 默认使用arm64
            self.registry_repo = "arm64/openssh-synchronization"
            print(f"⚠️  未知架构 {self.arch}，默认使用 arm64 仓库")
        
    def run_command(self, command: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """
        运行命令并返回结果
        
        参数:
            command: 命令列表
            capture_output: 是否捕获输出
            
        返回:
            命令执行结果
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=capture_output,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            print(f"❌ 执行命令失败: {' '.join(command)}")
            print(f"错误: {e}")
            sys.exit(1)
    
    def detect_architecture(self) -> str:
        """
        检测系统架构
        
        返回:
            架构类型 (arm64, amd64, 或其他)
        """
        machine = platform.machine().lower()
        
        if machine in ['arm64', 'aarch64', 'armv8']:
            return 'arm64'
        elif machine in ['x86_64', 'amd64']:
            return 'amd64'
        elif machine in ['i386', 'i686']:
            return 'x86'
        else:
            return machine  # 返回原始架构名称
    
    def check_docker_installed(self) -> bool:
        """检查Docker是否已安装"""
        result = self.run_command(["docker", "--version"], capture_output=True)
        return result.returncode == 0
    
    def build_image(self, tag: str = "latest", no_cache: bool = False, registry_tag: str = "latest") -> bool:
        """
        构建Docker镜像
        
        参数:
            tag: 镜像标签
            no_cache: 是否不使用缓存
            registry_tag: 私有仓库标签（如：v1.0.0）
            
        返回:
            构建成功返回True，失败返回False
        """
        print("🚀 开始构建Docker镜像...")
        
        # 检查Docker是否安装
        if not self.check_docker_installed():
            print("❌ Docker未安装，请先安装Docker")
            return False
        
        # 构建命令
        build_cmd = ["docker", "build", "-t", f"{self.image_name}:{tag}", "."]
        if no_cache:
            build_cmd.append("--no-cache")
        
        # 添加私有仓库标签
        registry_image = f"{self.registry_url}/{self.registry_repo}:{registry_tag}"
        build_cmd.extend(["-t", registry_image])
        
        print(f"📦 构建命令: {' '.join(build_cmd)}")
        
        # 执行构建
        result = self.run_command(build_cmd)
        
        if result.returncode == 0:
            print(f"✅ 镜像构建成功: {self.image_name}:{tag}")
            registry_image = f"{self.registry_url}/{self.registry_repo}:{registry_tag}"
            print(f"✅ 私有仓库镜像构建成功: {registry_image}")
            return True
        else:
            print(f"❌ 镜像构建失败")
            return False
    
    def push_image(self, registry_tag: str = "latest") -> bool:
        """
        推送镜像到私有仓库
        
        参数:
            registry_tag: 私有仓库标签
            
        返回:
            推送成功返回True，失败返回False
        """
        print(f"🚀 开始推送镜像到私有仓库...")
        
        # 构建完整的镜像名称
        registry_image = f"{self.registry_url}/{self.registry_repo}:{registry_tag}"
        
        # 推送镜像
        push_cmd = ["docker", "push", registry_image]
        
        print(f"📤 推送命令: {' '.join(push_cmd)}")
        result = self.run_command(push_cmd)
        
        if result.returncode == 0:
            print(f"✅ 镜像推送成功: {registry_image}")
            return True
        else:
            print(f"❌ 镜像推送失败")
            return False
        """
        推送镜像到私有仓库
        
        参数:
            registry_tag: 私有仓库标签
            
        返回:
            推送成功返回True，失败返回False
        """
        print(f"🚀 开始推送镜像到私有仓库...")
        
        # 构建完整的镜像名称
        registry_image = f"{self.registry_url}/{self.registry_repo}:{registry_tag}"
        
        # 推送镜像
        push_cmd = ["docker", "push", registry_image]
        
        print(f"📤 推送命令: {' '.join(push_cmd)}")
        result = self.run_command(push_cmd)
        
        if result.returncode == 0:
            print(f"✅ 镜像推送成功: {registry_image}")
            return True
        else:
            print(f"❌ 镜像推送失败")
            return False

    def run_container(self, 
                     tag: str = "latest",
                     check_interval: int = 24,
                     min_version: str = "10.2.1",
                     debug: bool = False,
                     detach: bool = True,
                     mount_path: str = None) -> bool:
        """
        运行Docker容器
        
        参数:
            tag: 镜像标签
            check_interval: 检查间隔(小时)
            min_version: 最小版本
            debug: 是否启用调试模式
            detach: 是否在后台运行
            mount_path: 挂载路径，如果为None则使用默认路径
            
        返回:
            运行是否成功
        """
        print("🚀 启动Docker容器...")
        
        # 处理挂载路径
        if mount_path is None:
            # 使用默认路径
            mount_path = str(self.data_dir / "openssh")
            print(f"📁 使用默认挂载路径: {mount_path}")
        else:
            # 使用用户指定的路径
            mount_path = Path(mount_path).resolve()
            print(f"📁 使用用户指定挂载路径: {mount_path}")
        
        # 创建挂载目录
        Path(mount_path).mkdir(parents=True, exist_ok=True)
        
        # 运行命令
        run_cmd = [
            "docker", "run",
            "--name", self.container_name,
            "-v", f"{mount_path}:/data/openssh",
            "-e", f"CHECK_INTERVAL={check_interval}",
            "-e", f"MIN_VERSION={min_version}",
            "-e", f"DEBUG={str(debug).lower()}",
            "--restart", "unless-stopped"
        ]
        
        if detach:
            run_cmd.append("-d")
        
        run_cmd.append(f"{self.image_name}:{tag}")
        
        print(f"📦 运行命令: {' '.join(run_cmd)}")
        
        # 执行运行
        result = self.run_command(run_cmd)
        
        if result.returncode == 0:
            print(f"✅ 容器启动成功: {self.container_name}")
            print(f"📂 数据挂载路径: {mount_path}")
            if detach:
                print("💡 容器在后台运行，使用 'status' 命令查看状态")
            return True
        else:
            print("❌ 容器启动失败")
            return False
    
    def stop_container(self) -> bool:
        """停止运行中的容器"""
        print("🛑 停止容器...")
        
        # 检查容器是否存在
        if not self.container_exists():
            print("⚠️  容器不存在或未运行")
            return False
        
        # 停止容器
        result = self.run_command(["docker", "stop", self.container_name])
        
        if result.returncode == 0:
            print(f"✅ 容器停止成功: {self.container_name}")
            return True
        else:
            print("❌ 容器停止失败")
            return False
    
    def remove_container(self, force: bool = False) -> bool:
        """
        删除容器
        
        参数:
            force: 是否强制删除
            
        返回:
            删除是否成功
        """
        print("🗑️  删除容器...")
        
        # 检查容器是否存在
        if not self.container_exists():
            print("⚠️  容器不存在")
            return False
        
        # 删除容器
        rm_cmd = ["docker", "rm", self.container_name]
        if force:
            rm_cmd.append("-f")
        
        result = self.run_command(rm_cmd)
        
        if result.returncode == 0:
            print(f"✅ 容器删除成功: {self.container_name}")
            return True
        else:
            print("❌ 容器删除失败")
            return False
    
    def container_exists(self) -> bool:
        """检查容器是否存在"""
        result = self.run_command(
            ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
            capture_output=True
        )
        return self.container_name in result.stdout
    
    def container_status(self) -> Dict[str, Any]:
        """获取容器状态信息"""
        status_info = {
            "exists": False,
            "running": False,
            "status": "",
            "image": "",
            "created": "",
            "ports": ""
        }
        
        # 检查容器状态
        result = self.run_command(
            ["docker", "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}|{{.Status}}|{{.Image}}|{{.CreatedAt}}|{{.Ports}}"],
            capture_output=True
        )
        
        if result.stdout.strip():
            parts = result.stdout.strip().split('|')
            if len(parts) >= 5:
                status_info.update({
                    "exists": True,
                    "running": "Up" in parts[1],
                    "status": parts[1],
                    "image": parts[2],
                    "created": parts[3],
                    "ports": parts[4]
                })
        
        return status_info
    
    def show_status(self) -> None:
        """显示容器状态"""
        print("📊 容器状态信息:")
        
        status = self.container_status()
        
        if not status["exists"]:
            print("❌ 容器不存在")
            return
        
        print(f"📦 容器名称: {self.container_name}")
        print(f"🔧 镜像: {status['image']}")
        print(f"📈 状态: {status['status']}")
        print(f"🕐 创建时间: {status['created']}")
        print(f"🔗 端口映射: {status['ports']}")
        
        if status["running"]:
            print("✅ 容器正在运行")
        else:
            print("❌ 容器已停止")
    
    def show_logs(self, follow: bool = False, tail: int = 100) -> None:
        """
        显示容器日志
        
        参数:
            follow: 是否持续跟踪日志
            tail: 显示最后多少行日志
        """
        if not self.container_exists():
            print("❌ 容器不存在")
            return
        
        log_cmd = ["docker", "logs", self.container_name, f"--tail={tail}"]
        if follow:
            log_cmd.append("-f")
        
        print(f"📋 显示容器日志 (最后{tail}行):")
        self.run_command(log_cmd)
    
    def cleanup(self) -> bool:
        """清理容器和镜像"""
        print("🧹 开始清理...")
        
        # 停止并删除容器
        if self.container_exists():
            self.stop_container()
            self.remove_container(force=True)
        
        # 删除镜像
        result = self.run_command(
            ["docker", "images", "-q", self.image_name],
            capture_output=True
        )
        
        if result.stdout.strip():
            image_ids = result.stdout.strip().split('\n')
            for image_id in image_ids:
                if image_id:
                    self.run_command(["docker", "rmi", "-f", image_id])
            print(f"✅ 镜像删除成功: {self.image_name}")
        
        print("✅ 清理完成")
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OpenSSH同步工具容器管理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python docker_manager.py build           # 构建镜像
  python docker_manager.py build -nc       # 构建镜像不使用缓存
  python docker_manager.py run            # 运行容器（使用默认路径）
  python docker_manager.py run -d         # 以调试模式运行（简化形式）
  python docker_manager.py run -mp /custom/path  # 使用自定义挂载路径
  python docker_manager.py run -t v1.0 -ci 48 -mv 9.0  # 使用多个简化参数
  python docker_manager.py stop           # 停止容器
  python docker_manager.py stop -F        # 强制停止容器
  python docker_manager.py status         # 查看状态
  python docker_manager.py logs           # 查看日志
  python docker_manager.py logs -f -tl 50  # 持续跟踪最后50行日志
  python docker_manager.py cleanup        # 清理所有资源
  python docker_manager.py cleanup -F     # 强制清理所有资源
        """
    )
    
    parser.add_argument("command", choices=["build", "run", "stop", "status", "logs", "cleanup"], 
                       help="要执行的命令")
    parser.add_argument("-t", "--tag", default="latest", help="镜像标签 (默认: latest)")
    parser.add_argument("-ci", "--check-interval", type=int, default=24, 
                       help="检查间隔(小时) (默认: 24)")
    parser.add_argument("-mv", "--min-version", default="10.2.1", 
                       help="最小版本号 (默认: 10.2.1)")
    parser.add_argument("-d", "--debug", action="store_true", 
                       help="启用调试模式")
    parser.add_argument("-mp", "--mount-path", 
                       help="挂载路径，如果不指定则使用默认路径 ./data/openssh")
    parser.add_argument("--no-cache", action="store_true", 
                       help="构建时不使用缓存")
    parser.add_argument("--registry-tag", type=str,
                       help="私有仓库镜像标签（如：v1.0.0）")
    parser.add_argument("--push", action="store_true",
                       help="构建完成后推送到私有仓库")
    parser.add_argument("-f", "--follow", action="store_true", 
                       help="持续跟踪日志 (仅logs命令)")
    parser.add_argument("-tl", "--tail", type=int, default=100, 
                       help="显示最后多少行日志 (默认: 100)")
    parser.add_argument("-F", "--force", action="store_true", 
                       help="强制操作")
    
    args = parser.parse_args()
    
    # 创建管理器实例
    manager = DockerManager()
    
    # 执行命令
    if args.command == "build":
        success = manager.build_image(tag=args.tag, no_cache=args.no_cache, registry_tag=args.registry_tag)
        if success:
            print("✅ 构建完成！")
            # 如果需要推送到私有仓库
            if args.push:
                print("🔄 开始推送到私有仓库...")
                push_success = manager.push_image(args.registry_tag or "latest")
                if push_success:
                    print("✅ 推送完成！")
                else:
                    print("❌ 推送失败！")
                    return 1
        else:
            print("❌ 构建失败！")
            return 1
    elif args.command == "run":
        manager.run_container(
            tag=args.tag,
            check_interval=args.check_interval,
            min_version=args.min_version,
            debug=args.debug,
            mount_path=args.mount_path
        )
    elif args.command == "stop":
        manager.stop_container()
    elif args.command == "status":
        manager.show_status()
    elif args.command == "logs":
        manager.show_logs(follow=args.follow, tail=args.tail)
    elif args.command == "cleanup":
        manager.cleanup()


if __name__ == "__main__":
    main()