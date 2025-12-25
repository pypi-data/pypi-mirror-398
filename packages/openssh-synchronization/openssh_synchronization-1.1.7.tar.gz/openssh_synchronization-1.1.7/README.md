# OpenSSH 资源同步工具

一个用于从阿里云镜像同步 OpenSSH 资源的 Python 工具，支持定时检测和版本过滤。

## 功能特性

- ✅ 从阿里云镜像同步 OpenSSH 资源
- ✅ 支持设置检测间隔时间（最小12小时）
- ✅ 版本过滤（只同步大于等于 openssh-10.2p1 的版本）
- ✅ 只同步 tar.gz 文件
- ✅ 无限循环后台守护进程
- ✅ Docker 容器化支持
- ✅ **clang编译器优化构建**
- ✅ 命令行接口，易于使用
- ✅ 基于 pyproject.toml 最新标准
- ✅ systemd 服务管理（注册、状态查看、删除）
- ✅ 自动服务注册功能
- ✅ 服务健康状态监控

## 安装

### 从 PyPI 安装

```bash
pip install openssh-synchronization
```

#### 使用清华大学 PyPI 镜像源加速安装

```bash
# 临时使用清华镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openssh-synchronization

# 或者设置清华镜像源为默认源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install openssh-synchronization
```

### Docker 安装

#### 从远程仓库拉取镜像

```bash
# 从腾讯云容器镜像服务拉取镜像
docker pull ccr.ccs.tencentyun.com/liumou/openssh-synchronization:latest
```

#### 运行容器

```bash
# 直接运行（推荐使用环境变量配置）
docker run -d \
  --name openssh-sync \
  -v /path/to/downloads:/data/openssh \
  -e CHECK_INTERVAL=24 \
  -e DOWNLOAD_DIR=/data/openssh \
  -e MIN_VERSION=10.3.0 \
  -e DEBUG=false \
  ccr.ccs.tencentyun.com/liumou/openssh-synchronization:latest
```

#### 查看日志

```bash
# 查看容器日志
docker logs openssh-sync

# 实时查看日志
docker logs -f openssh-sync
```

## 快速开始

### 查看帮助

```bash
openssh-sync --help
```

### 列出可用版本

```bash
openssh-sync list
```

输出示例：

```bash
🔍 正在获取OpenSSH版本列表...
📋 找到 3 个符合条件的版本:
------------------------------------------------------------
🔸 openssh-10.2p1
   文件: openssh-10.2p1.tar.gz
   大小: 1.9 MB

🔸 openssh-10.1p1
   文件: openssh-10.1p1.tar.gz
   大小: 1.9 MB

💡 提示: 使用 'openssh-sync sync' 命令下载这些版本
```

![image-20251110-084439](images/QQ20251110-084439.png)

### 执行一次性同步

```bash
# 使用默认配置
openssh-sync sync

# 自定义参数
openssh-sync sync --interval 48 --dir /opt/openssh --min-version 10.3.0
```

### 启动定时同步服务

```bash
# 启动守护进程
openssh-sync daemon --interval 24 --dir /tmp/openssh

# 使用配置文件
openssh-sync daemon --config-file config.json

# 启动守护进程并自动注册为systemd服务
openssh-sync daemon --auto-register
```

### systemd 服务管理

```bash
# 注册为systemd服务
openssh-sync register

# 强制重新注册服务
openssh-sync register --force

# 查看服务状态
openssh-sync status

# 删除服务
openssh-sync unregister
```

### 生成配置文件

```bash
# 生成默认配置文件
openssh-sync config

# 生成自定义配置文件
openssh-sync config --interval 48 --dir /opt/openssh --extract --output my-config.json
```

## 配置说明

### 环境变量配置

OpenSSH同步工具支持通过环境变量配置参数，优先级：命令行参数 > 环境变量 > 默认值

| 环境变量 | 说明 | 示例值 | 默认值 |
|----------|------|--------|--------|
| `CHECK_INTERVAL` | 检查间隔时间（小时） | `24` | `24` |
| `DOWNLOAD_DIR` | 下载目录路径 | `/tmp/openssh` | `./downloads` |
| `MIN_VERSION` | 最小版本要求 | `10.2.1` | `10.2.1` |
| `DEBUG` | 启用调试模式 | `true` | `false` |

**使用示例：**

```bash
# 通过环境变量配置
CHECK_INTERVAL=36 DOWNLOAD_DIR=/tmp/openssh MIN_VERSION=10.3.1 DEBUG=true openssh-sync sync

# 容器环境推荐用法
docker run -d \
  -e CHECK_INTERVAL=24 \
  -e DOWNLOAD_DIR=/data/openssh \
  -e MIN_VERSION=10.3.0 \
  -e DEBUG=false \
  openssh-sync
```

### 命令行参数

| 参数 | 说明 | 示例值 | 默认值 |
|------|------|--------|--------|
| `--interval`, `-i` | 检查间隔时间（小时） | `24` | `24` |
| `--dir`, `-d` | 下载目录路径 | `/tmp/openssh` | `./downloads` |
| `--min-version` | 最小版本要求 | `10.2.1` | `10.2.1` |
| `--debug` | 启用调试模式 | `--debug` | `False` |
| `--config-file` | 配置文件路径 | `/etc/openssh-sync.json` | `None` |

### 配置文件格式

生成的 JSON 配置文件示例：

```json
{
  "check_interval": 24,
  "download_dir": "./downloads",
  "min_version": [10, 2, 1],
  "mirror_url": "https://mirrors.aliyun.com/openssh/portable",
  "timeout": 30,
  "debug": false
}
```

### systemd 服务配置

OpenSSH同步工具注册为systemd服务后，会创建以下配置：

**服务文件位置：** `/etc/systemd/system/openssh-sync.service`

**服务配置内容：**

```ini
[Unit]
Description=OpenSSH Synchronization Service

[Service]
ExecStart=/usr/local/bin/openssh-sync daemon
WorkingDirectory=/opt/openssh
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
```

**服务管理命令：**

```bash
# 启动服务
sudo systemctl start openssh-sync

# 停止服务
sudo systemctl stop openssh-sync

# 重启服务
sudo systemctl restart openssh-sync

# 查看服务状态
sudo systemctl status openssh-sync

# 启用开机自启
sudo systemctl enable openssh-sync

# 禁用开机自启
sudo systemctl disable openssh-sync

# 查看服务日志
sudo journalctl -u openssh-sync -f
```

## API 使用

### 基本用法

```python
from openssh_sync import Config, OpenSSHSync

# 创建配置
config = Config(
    check_interval=24,           # 检查间隔：24小时
    download_dir="/tmp/openssh"  # 下载目录
)

# 创建同步实例
sync_tool = OpenSSHSync(config)

# 执行同步
success = sync_tool.sync_files()

if success:
    print("同步成功")
else:
    print("同步失败")
```

### 高级用法

```python
from openssh_sync import create_sync, create_config_from_dict

# 从字典创建配置
config_dict = {
    'check_interval': 48,
    'download_dir': '/opt/openssh',
    'min_version': [10, 3, 0],
    'debug': True
}

config = create_config_from_dict(config_dict)
sync_tool = create_sync(config)

# 获取文件列表
files = sync_tool.get_file_list()
for file_info in files:
    print(f"版本: {file_info['version']}, 文件: {file_info['filename']}")

# 启动定时同步
sync_tool.start_scheduled_sync()
```

## 项目结构

```bash
openssh-synchronization/
├── pyproject.toml          # 项目配置
├── README.md               # 项目说明
├── LICENSE                 # 许可证
├── .gitignore             # Git忽略文件
└── openssh_sync/          # 主程序包
    ├── __init__.py        # 包初始化
    ├── main.py            # 主程序逻辑
    ├── config.py          # 配置管理
    ├── utils.py           # 工具函数
    └── cli.py             # 命令行接口
```

## 开发

### 安装开发依赖

```bash
pip install -e .[dev]
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black openssh_sync/
isort openssh_sync/
```

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 技术支持

如有问题，请提交 [Issue](https://gitee.com/yourusername/openssh-synchronization/issues) 或联系开发者。
