#!/usr/bin/env python3
"""下载前端静态资源以支持离线使用"""

import requests
import os
from pathlib import Path

# 静态资源目录
STATIC_DIR = Path("maque/table_viewer/static")
STATIC_DIR.mkdir(exist_ok=True)

# 需要下载的资源
ASSETS = {
    "vue.global.js": "https://unpkg.com/vue@3/dist/vue.global.js",
    "element-plus.js": "https://unpkg.com/element-plus/dist/index.full.js", 
    "element-plus-icons.js": "https://unpkg.com/@element-plus/icons-vue/dist/index.iife.js",
    "element-plus.css": "https://unpkg.com/element-plus/dist/index.css"
}

def download_file(url: str, filename: str) -> bool:
    """下载文件"""
    try:
        print(f"正在下载 {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        file_path = STATIC_DIR / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"{filename} 下载成功 ({len(response.text)} 字符)")
        return True
        
    except Exception as e:
        print(f"{filename} 下载失败: {e}")
        return False

def main():
    """主函数"""
    print("开始下载前端静态资源...")
    
    success_count = 0
    total_count = len(ASSETS)
    
    for filename, url in ASSETS.items():
        if download_file(url, filename):
            success_count += 1
    
    print(f"\n下载完成: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("所有资源下载成功！现在可以离线使用表格查看器了。")
    else:
        print("部分资源下载失败，可能仍需要网络连接。")

if __name__ == "__main__":
    main()