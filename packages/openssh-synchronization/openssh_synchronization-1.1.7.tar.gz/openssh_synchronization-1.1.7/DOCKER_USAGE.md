# Docker 容器管理脚本使用说明

## 概述

`docker_manager.py` 是一个完整的 Docker 容器管理脚本，用于构建和运行 OpenSSH 同步工具的容器镜像。

## 功能特性

- ✅ **镜像构建**: 自动构建 Docker 镜像
- ✅ **容器运行**: 一键启动容器服务
- ✅ **状态监控**: 实时查看容器状态
- ✅ **日志查看**: 查看容器运行日志
- ✅ **容器管理**: 停止、删除容器
- ✅ **资源清理**: 清理所有容器和镜像
- ✅ **参数配置**: 支持自定义配置参数

## 快速开始

### 1. 构建镜像

```bash
python docker_manager.py build
```

可选参数:
- `--tag`: 指定镜像标签 (默认: latest)
- `--no-cache`: 不使用缓存构建

### 2. 运行容器

```bash
python docker_manager.py run
```

可选参数:
- `--check-interval`: 检查间隔(小时) (默认: 24)
- `--min-version`: 最小版本号 (默认: 10.2.1)
- `--debug`: 启用调试模式

### 3. 查看状态

```bash
python docker_manager.py status
```

### 4. 查看日志

```bash
python docker_manager.py logs
```

可选参数:
- `--tail`: 显示最后多少行日志 (默认: 100)
- `--follow`: 持续跟踪日志

### 5. 停止容器

```bash
python docker_manager.py stop
```

### 6. 清理资源

```bash
python docker_manager.py cleanup
```

## 详细使用示例

### 构建特定版本的镜像

```bash
python docker_manager.py build --tag v1.0.0 --no-cache
```

### 以调试模式运行容器

```bash
python docker_manager.py run --debug --check-interval 12 --min-version 10.3.0
```

### 实时监控日志

```bash
python docker_manager.py logs --follow --tail 50
```

### 完整的部署流程

```bash
# 1. 构建镜像
python docker_manager.py build --no-cache

# 2. 运行容器
python docker_manager.py run --check-interval 24 --min-version 10.2.1

# 3. 检查状态
python docker_manager.py status

# 4. 查看日志
python docker_manager.py logs --tail 20
```

## 环境要求

- Python 3.6+
- Docker 已安装并运行
- 项目根目录包含有效的 Dockerfile

## 数据持久化

容器会自动创建 `data/openssh` 目录用于存储下载的 OpenSSH 文件，确保数据在容器重启后不会丢失。

## 故障排除

### Docker 未安装

```bash
# 检查 Docker 是否安装
docker --version

# 如果未安装，请先安装 Docker
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io

# CentOS/RHEL:
sudo yum install docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 权限问题

如果遇到权限问题，请将当前用户添加到 docker 组：

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 端口冲突

如果端口已被占用，脚本会自动处理容器命名冲突。

## 配置文件

脚本会自动读取项目中的 `Dockerfile` 和 `docker-compose.yml` 配置，无需额外配置。

## 安全说明

- 容器以非 root 用户运行
- 数据目录具有适当的权限设置
- 支持健康检查机制
- 自动重启策略确保服务可用性

## 技术支持

如有问题，请检查：
1. Docker 服务是否正常运行
2. 项目目录是否包含完整的源代码
3. 网络连接是否正常
4. 查看详细日志获取错误信息

---

**注意**: 在生产环境中使用前，请确保充分测试所有功能。