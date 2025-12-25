#!/usr/bin/env python
# coding: utf-8
"""
parallel_untar.py
Unpacks various tar archives (.tar, .tar.gz, .tar.zst) in parallel.
"""

import os
import subprocess
import argparse
import shutil
import sys
import glob
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_command(cmd):
    """检查指定的命令是否存在于系统的PATH中。"""
    if shutil.which(cmd) is None:
        print(f"错误: 必需的命令 '{cmd}' 未找到。", file=sys.stderr)
        print(f"请确保 '{cmd}' 已安装并且在您的系统PATH中。", file=sys.stderr)
        sys.exit(1)


def run_untar_job(archive_path, dest_dir):
    """
    为单个归档文件执行 'tar -xf' 解压命令。
    现代 tar 会自动检测压缩格式 (gzip, zstd, etc.)。
    """
    job_name = os.path.basename(archive_path)
    # -x: 提取 (extract)
    # -f: 指定文件 (file)
    # -C: 指定目标目录 (Change directory)
    tar_cmd = ["tar", "-xf", archive_path, "-C", dest_dir]

    try:
        subprocess.run(
            tar_cmd, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        return f"文件 '{job_name}' 解压成功。"
    except subprocess.CalledProcessError as e:
        error_message = f"错误: 解压 '{job_name}' 失败。\n"
        error_message += f"错误信息: {e.stderr.strip()}"
        return error_message
    except Exception as e:
        return f"错误: 解压 '{job_name}' 时发生意外异常: {e}"


def parallel_unpack(source_dir, dest_dir, parallel_jobs):
    """
    并行地将源目录中的所有 .tar, .tar.gz, .tar.zst 文件解压到目标目录。
    """
    # --- 新增：记录开始时间 ---
    start_time = time.time()

    # --- 1. 检查和准备 ---
    print("--- 步骤 1: 检查与准备 ---")
    check_command("tar")

    source_dir = os.path.abspath(source_dir)
    dest_dir = os.path.abspath(dest_dir)

    if not os.path.isdir(source_dir):
        print(f"错误: 源目录 '{source_dir}' 不存在或不是一个目录。", file=sys.stderr)
        return

    # 创建目标目录，如果不存在的话
    os.makedirs(dest_dir, exist_ok=True)

    # --- 2. 查找所有要解压的归档文件 ---
    print(f"--- 步骤 2: 在 '{source_dir}' 中查找归档文件 ---")

    # --- 已修改：查找多种压缩格式 ---
    patterns = ["*.tar", "*.tar.gz", "*.tar.zst"]
    archive_files = []
    for pattern in patterns:
        archive_files.extend(glob.glob(os.path.join(source_dir, pattern)))

    if not archive_files:
        print(f"在 '{source_dir}' 中未找到任何支持的归档文件 ({', '.join(patterns)})。")
        return

    print(f"找到 {len(archive_files)} 个归档文件，准备解压。")

    # --- 3. 使用线程池并行执行解压 ---
    print(f"\n--- 步骤 3: 并行启动解压任务 (最多 {parallel_jobs} 个任务同时运行) ---")

    with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
        # 提交所有解压任务
        futures = {
            executor.submit(run_untar_job, archive, dest_dir): archive
            for archive in archive_files
        }

        # 等待任务完成并打印结果
        for future in as_completed(futures):
            result = future.result()
            print(f"  -> {result}")

    print("\n----------------------------------------")
    print("所有解压任务已完成！")
    print(f"文件已解压至: {dest_dir}")

    # --- 新增：计算并打印总耗时 ---
    end_time = time.time()
    duration = end_time - start_time
    print(f"总耗时: {duration:.2f} 秒。")
    print("----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="并行地将一个目录中的所有 .tar, .tar.gz, .tar.zst 归档文件解压到目标位置。",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("source_dir", type=str, help="包含归档文件的源文件夹路径。")
    parser.add_argument("dest_dir", type=str, help="用于存放解压后文件的目标文件夹。")
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=os.cpu_count() or 4,
        help="并行的解压任务数量 (即同时运行多少个 tar 进程)。\n"
        "默认为系统的CPU核心数。",
    )

    args = parser.parse_args()
    parallel_unpack(args.source_dir, args.dest_dir, args.jobs)
