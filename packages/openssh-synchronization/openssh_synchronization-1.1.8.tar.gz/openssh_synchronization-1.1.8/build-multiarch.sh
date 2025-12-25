#!/bin/bash
# OpenSSH同步工具多架构构建脚本
# 支持构建多平台Docker镜像

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
DOCKER_REGISTRY="docker.io"
IMAGE_NAME="openssh-sync"
IMAGE_TAG="latest"
PLATFORMS="linux/amd64,linux/arm64,linux/arm/v7"
BUILDER_NAME="multiarch-builder"

# 函数：打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 函数：检查依赖
check_dependencies() {
    info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker未安装，请先安装Docker"
    fi
    
    if ! docker buildx version &> /dev/null; then
        error "Docker Buildx未安装，请确保Docker版本 >= 19.03"
    fi
    
    info "依赖检查通过"
}

# 函数：设置构建器
setup_builder() {
    info "设置多架构构建器..."
    
    # 检查构建器是否已存在
    if docker buildx ls | grep -q "$BUILDER_NAME"; then
        info "构建器 $BUILDER_NAME 已存在，使用现有构建器"
    else
        info "创建新的构建器 $BUILDER_NAME"
        docker buildx create --name "$BUILDER_NAME" --use
    fi
    
    # 使用构建器
    docker buildx use "$BUILDER_NAME"
    
    # 启动构建器
    info "启动构建器..."
    docker buildx inspect --bootstrap
    
    info "构建器设置完成"
}

# 函数：安装QEMU模拟器
setup_qemu() {
    info "设置QEMU模拟器..."
    
    # 检查QEMU是否已安装
    if docker run --rm --privileged tonistiigi/binfmt --version &> /dev/null; then
        info "QEMU模拟器已安装"
    else
        info "安装QEMU模拟器..."
        docker run --rm --privileged tonistiigi/binfmt --install all
    fi
    
    info "QEMU模拟器设置完成"
}

# 函数：构建镜像
build_image() {
    local platforms="$1"
    local push_flag="$2"
    
    info "开始构建多架构镜像..."
    info "目标平台: $platforms"
    info "镜像标签: $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    
    # 构建命令
    local build_cmd="docker buildx build"
    build_cmd+=" --platform $platforms"
    build_cmd+=" --tag $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    build_cmd+=" --build-arg VERSION=$(cat VERSION 2>/dev/null || echo '1.1.6')"
    
    if [ "$push_flag" = "push" ]; then
        build_cmd+=" --push"
    else
        # 对于本地构建，如果指定了多个平台，使用 --output 而不是 --load
        if [[ "$platforms" == *","* ]]; then
            build_cmd+=" --output type=oci,dest=./openssh-sync-multiarch.tar"
            info "多平台构建将导出为 OCI 归档文件"
        else
            build_cmd+=" --load"
        fi
    fi
    
    # 添加缓存配置
    build_cmd+=" --cache-to type=local,dest=/tmp/docker-cache"
    build_cmd+=" --cache-from type=local,src=/tmp/docker-cache"
    
    build_cmd+=" ."
    
    info "执行构建命令: $build_cmd"
    
    if eval "$build_cmd"; then
        info "镜像构建成功！"
    else
        error "镜像构建失败！"
    fi
}

# 函数：显示使用帮助
show_help() {
    cat << EOF
OpenSSH同步工具多架构构建脚本

使用方法: $0 [选项]

选项:
    -p, --platforms PLATFORMS   指定目标平台 (默认: $PLATFORMS)
    -t, --tag TAG               镜像标签 (默认: $IMAGE_TAG)
    -r, --registry REGISTRY     Docker仓库地址 (默认: $DOCKER_REGISTRY)
    -n, --name NAME             镜像名称 (默认: $IMAGE_NAME)
    --push                      构建并推送镜像到仓库
    --setup-only                仅设置构建环境，不构建镜像
    --local                     本地构建，不推送
    -h, --help                  显示帮助信息

示例:
    $0                          # 本地构建默认平台
    $0 --push                   # 构建并推送多架构镜像
    $0 --platforms linux/amd64  # 仅构建amd64架构
    $0 --setup-only             # 仅设置构建环境

支持的平台:
    linux/amd64     - x86_64架构
    linux/arm64     - ARM 64位架构
    linux/arm/v7    - ARM 32位架构 (ARMv7)
    linux/arm/v6    - ARM 32位架构 (ARMv6)
    linux/386       - i386架构
    linux/ppc64le   - PowerPC 64位小端架构
    linux/s390x     - IBM System z架构

EOF
}

# 主函数
main() {
    local action="build"
    local push_flag="load"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--platforms)
                PLATFORMS="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -r|--registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            -n|--name)
                IMAGE_NAME="$2"
                shift 2
                ;;
            --push)
                push_flag="push"
                shift
                ;;
            --setup-only)
                action="setup"
                shift
                ;;
            --local)
                push_flag="load"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "未知参数: $1"
                ;;
        esac
    done
    
    # 检查依赖
    check_dependencies
    
    # 设置构建环境
    setup_builder
    setup_qemu
    
    # 如果仅设置环境，则退出
    if [ "$action" = "setup" ]; then
        info "构建环境设置完成"
        info "支持的构建平台:"
        docker buildx ls
        exit 0
    fi
    
    # 构建镜像
    build_image "$PLATFORMS" "$push_flag"
    
    # 显示构建结果
    info "构建完成！"
    if [ "$push_flag" = "push" ]; then
        info "镜像已推送到: $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
        info "支持的架构:"
        docker buildx imagetools inspect "$DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
    else
        if [ -f "./openssh-sync-multiarch.tar" ]; then
            info "多架构镜像已导出为 OCI 归档文件: openssh-sync-multiarch.tar"
            info "文件大小: $(du -h openssh-sync-multiarch.tar | cut -f1)"
        else
            info "本地镜像构建完成: $DOCKER_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
            info "当前平台镜像已加载到本地Docker"
        fi
    fi
}

# 运行主函数
main "$@"