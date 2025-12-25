#!/usr/bin/env python3
"""测试HTML生成器功能"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openssh_sync.html_generator import create_html_generator

def test_html_generator():
    """测试HTML生成器"""
    print("🧪 测试HTML生成器功能...")
    
    # 创建HTML生成器
    download_dir = "data/openssh"
    html_generator = create_html_generator(download_dir)
    
    # 扫描文件
    print("📁 扫描下载目录中的文件...")
    files = html_generator.scan_downloaded_files()
    print(f"找到 {len(files)} 个文件:")
    for file_info in files:
        print(f"  - {file_info['filename']} ({file_info['size']})")
    
    # 生成HTML
    print("\n🌐 生成HTML文件...")
    success = html_generator.generate_index_html()
    
    if success:
        print("✅ HTML生成成功!")
        
        # 检查生成的HTML文件
        index_path = os.path.join(download_dir, "index.html")
        if os.path.exists(index_path):
            print(f"📄 HTML文件已生成: {index_path}")
            
            # 显示文件大小
            file_size = os.path.getsize(index_path)
            print(f"📏 HTML文件大小: {file_size} 字节")
            
            # 显示文件内容预览
            print("\n📋 HTML文件内容预览:")
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print("❌ HTML文件未生成")
    else:
        print("❌ HTML生成失败")
    
    return success

if __name__ == "__main__":
    test_html_generator()