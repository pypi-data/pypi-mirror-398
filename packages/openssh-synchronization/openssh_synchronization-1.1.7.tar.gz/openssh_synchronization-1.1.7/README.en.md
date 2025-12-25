# OpenSSH Synchronization Tool

A Python tool for synchronizing OpenSSH resources from Alibaba Cloud mirror, supporting scheduled detection and version filtering.

## Features

- ✅ Synchronize OpenSSH resources from Alibaba Cloud mirror
- ✅ Set detection interval (minimum 12 hours)
- ✅ Version filtering (only sync versions >= openssh-10.2p1)
- ✅ Only sync tar.gz files
- ✅ Infinite loop background daemon process
- ✅ Docker containerization support
- ✅ Command-line interface, easy to use
- ✅ Based on the latest pyproject.toml standard

## Installation

### Install from PyPI

```bash
pip install openssh-synchronization
```

### Docker Installation

#### Pull Image from Remote Registry

```bash
# Pull image from Tencent Cloud Container Registry
docker pull ccr.ccs.tencentyun.com/liumou/openssh-synchronization:latest
```

#### Run Container

```bash
# Direct run (recommended using environment variables)
docker run -d \
  --name openssh-sync \
  -v /path/to/downloads:/data/openssh \
  -e CHECK_INTERVAL=24 \
  -e DOWNLOAD_DIR=/data/openssh \
  -e MIN_VERSION=10.3.0 \
  -e DEBUG=false \
  ccr.ccs.tencentyun.com/liumou/openssh-synchronization:latest

# Use docker-compose
docker-compose up -d
```

#### View Logs

```bash
# View container logs
docker logs openssh-sync

# Real-time log viewing
docker logs -f openssh-sync
```

## Quick Start

### View Help

```bash
openssh-sync --help
```

### List Available Versions

```bash
openssh-sync list
```

Example output:
```
🔍 Fetching OpenSSH version list...
📋 Found 3 matching versions:
------------------------------------------------------------
🔸 openssh-10.2p1
   File: openssh-10.2p1.tar.gz
   Size: 1.9 MB

🔸 openssh-10.1p1
   File: openssh-10.1p1.tar.gz
   Size: 1.9 MB

💡 Tip: Use 'openssh-sync sync' command to download these versions
```

**Screenshot:**
![OpenSSH Synchronization Tool Screenshot](images/QQ20251110-084439.png)

### Execute One-time Synchronization

```bash
# Use default configuration
openssh-sync sync

# Custom parameters
openssh-sync sync --interval 48 --dir /opt/openssh --min-version 10.3.0
```

### Start Timed Synchronization Service

```bash
# Start daemon process
openssh-sync daemon --interval 24 --dir /tmp/openssh

# Use configuration file
openssh-sync daemon --config-file config.json
```

### Generate Configuration File

```bash
# Generate default configuration file
openssh-sync config

# Generate custom configuration file
openssh-sync config --interval 48 --dir /opt/openssh --extract --output my-config.json
```

## Configuration

### Environment Variable Configuration

OpenSSH synchronization tool supports parameter configuration through environment variables. Priority: command-line parameters > environment variables > default values

| Environment Variable | Description | Example Value | Default Value |
|---------------------|-------------|---------------|---------------|
| `CHECK_INTERVAL` | Check interval time (hours) | `24` | `24` |
| `DOWNLOAD_DIR` | Download directory path | `/tmp/openssh` | `./downloads` |
| `MIN_VERSION` | Minimum version requirement | `10.2.1` | `10.2.1` |
| `DEBUG` | Enable debug mode | `true` | `false` |

**Usage Examples:**
```bash
# Configure via environment variables
CHECK_INTERVAL=36 DOWNLOAD_DIR=/tmp/openssh MIN_VERSION=10.3.1 DEBUG=true openssh-sync sync

# Recommended usage in container environment
docker run -d \
  -e CHECK_INTERVAL=24 \
  -e DOWNLOAD_DIR=/data/openssh \
  -e MIN_VERSION=10.3.0 \
  -e DEBUG=false \
  openssh-sync
```

### Command-line Parameters

| Parameter | Description | Example Value | Default Value |
|-----------|-------------|---------------|---------------|
| `--interval`, `-i` | Check interval time (hours) | `24` | `24` |
| `--dir`, `-d` | Download directory path | `/tmp/openssh` | `./downloads` |
| `--min-version` | Minimum version requirement | `10.2.1` | `10.2.1` |
| `--debug` | Enable debug mode | `--debug` | `False` |
| `--config-file` | Configuration file path | `/etc/openssh-sync.json` | `None` |

### Configuration File Format

Generated JSON configuration file example:

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

## API Usage

### Basic Usage

```python
from openssh_sync import Config, OpenSSHSync

# Create configuration
config = Config(
    check_interval=24,           # Check interval: 24 hours
    download_dir="/tmp/openssh"  # Download directory
)

# Create synchronization instance
sync_tool = OpenSSHSync(config)

# Execute synchronization
success = sync_tool.sync_files()

if success:
    print("Synchronization successful")
else:
    print("Synchronization failed")
```

### Advanced Usage

```python
from openssh_sync import create_sync, create_config_from_dict

# Create configuration from dictionary
config_dict = {
    'check_interval': 48,
    'download_dir': '/opt/openssh',
    'min_version': [10, 3, 0],
    'debug': True
}

config = create_config_from_dict(config_dict)
sync_tool = create_sync(config)
```

## Architecture

This tool is designed for synchronizing OpenSSH resources in internal network environments from the internet resource: https://mirrors.aliyun.com/openssh/portable/

## Contribution

1. Fork the repository
2. Create Feat_xxx branch
3. Commit your code
4. Create Pull Request

## Gitee Features

1. You can use Readme_XXX.md to support different languages, such as Readme_en.md, Readme_zh.md
2. Gitee blog [blog.gitee.com](https://blog.gitee.com)
3. Explore open source project [https://gitee.com/explore](https://gitee.com/explore)
4. The most valuable open source project [GVP](https://gitee.com/gvp)
5. The manual of Gitee [https://gitee.com/help](https://gitee.com/help)
6. The most popular members [https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)
