#!/bin/bash
# 测试clang编译器配置

echo "=== 测试clang编译器配置 ==="
echo ""

# 测试1：检查clang是否安装
echo "1. 检查clang安装状态："
docker run --rm python:3.11-slim bash -c "clang --version || echo 'clang未安装'"
echo ""

# 测试2：构建镜像并检查编译器
echo "2. 构建Docker镜像并验证clang："
echo "命令：docker build --no-cache -t openssh-sync:clang-test ."
echo ""

# 测试3：检查构建后的二进制文件
echo "3. 验证编译后的二进制文件："
echo "构建完成后可以运行："
echo "docker run --rm openssh-sync:clang-test bash -c 'file /app/openssh-sync'"
echo "预期输出应显示使用clang编译的信息"
echo ""

echo "=== 编译优化特性 ==="
echo "✅ 使用clang替代gcc，提供更好的优化"
echo "✅ 启用链接时优化(LTO)，减少二进制文件大小"
echo "✅ Nuitka编译器优化Python代码执行效率"
echo ""

echo "如需构建测试镜像，请运行："
echo "docker build --no-cache -t openssh-sync:clang-test ."