#!/bin/bash
# 测试多架构构建的修复

echo "测试多架构构建修复..."
echo "目标：测试多平台构建时避免 --load 参数错误"
echo ""

# 测试1：单平台构建（应该使用 --load）
echo "=== 测试1：单平台构建 ==="
echo "命令：docker buildx build --platform linux/amd64 --tag openssh-sync:test-amd64 --load ."
echo "预期：成功，使用 --load 参数"
echo ""

# 测试2：多平台构建（应该使用 --output）
echo "=== 测试2：多平台构建 ==="
echo "命令：docker buildx build --platform linux/amd64,linux/arm64 --tag openssh-sync:test-multi --output type=oci,dest=./test-multi.tar ."
echo "预期：成功，使用 --output 参数导出为OCI归档"
echo ""

# 测试3：推送构建（应该使用 --push）
echo "=== 测试3：推送构建 ==="
echo "命令：docker buildx build --platform linux/amd64,linux/arm64 --tag localhost:5000/openssh-sync:test --push ."
echo "预期：成功，使用 --push 参数推送到仓库"
echo ""

echo "使用修复后的构建脚本："
echo "./build-multiarch.sh --platforms linux/amd64                    # 单平台，使用 --load"
echo "./build-multiarch.sh --platforms linux/amd64,linux/arm64       # 多平台，使用 --output"
echo "./build-multiarch.sh --platforms linux/amd64,linux/arm64 --push # 多平台，使用 --push"