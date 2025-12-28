#!/usr/bin/env python
# coding: utf-8
"""
Optimized Parallel Tar with stdin piping, compression support, and timing.
"""

import os
import subprocess
import argparse
import shutil
import sys
import time  # 导入 time 模块用于计时
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_command(cmd):
    """检查指定的命令是否存在于系统的PATH中。"""
    if shutil.which(cmd) is None:
        print(f"错误: 必需的命令 '{cmd}' 未找到。", file=sys.stderr)
        print(f"请确保 '{cmd}' 已安装并且在您的系统PATH中。", file=sys.stderr)
        sys.exit(1)


def parse_size_to_bytes(size_str):
    """将带有单位的尺寸字符串 (如 '5G', '100M') 解析为字节。"""
    size_str = size_str.strip().upper()
    units = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    try:
        if size_str and size_str[-1] in units:
            num = float(size_str[:-1])
            unit = size_str[-1]
            return int(num * units[unit])
        else:
            return int(size_str)
    except (ValueError, TypeError):
        print(f"错误: 无法解析尺寸字符串 '{size_str}'。", file=sys.stderr)
        sys.exit(1)


def run_tar_job(job_info):
    """
    为单个文件块执行 tar 命令。
    此版本通过管道将文件列表传递给 tar 的 stdin，避免了临时文件。
    """
    file_list, archive_path, source_dir, job_id, compression_args = job_info

    # 基本命令: -c (创建), --no-recursion (不递归), -f (指定文件), -C (切换目录), -T - (从stdin读取列表)
    tar_cmd = (
        ["tar"]
        + compression_args
        + ["-cf", archive_path, "-C", source_dir, "--no-recursion", "-T", "-"]
    )

    # 将文件列表（Python列表）转换为 tar -T- 所需的格式（换行符分隔的字符串）
    # 必须编码为字节串才能传递给 stdin
    files_to_pipe = "\n".join(file_list).encode("utf-8")

    try:
        # 使用 Popen 以便我们可以访问 stdin
        process = subprocess.Popen(
            tar_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # 将文件列表写入 stdin 并关闭它，然后等待进程完成
        stdout, stderr = process.communicate(input=files_to_pipe)

        if process.returncode != 0:
            # 如果 tar 命令失败，则格式化错误信息
            raise subprocess.CalledProcessError(
                returncode=process.returncode, cmd=tar_cmd, stderr=stderr
            )

        return f"任务 {job_id} ({os.path.basename(archive_path)}) 成功。"
    except subprocess.CalledProcessError as e:
        error_message = (
            f"错误: 任务 {job_id} ({os.path.basename(archive_path)}) 失败。\n"
        )
        # stderr 是字节串，需要解码
        error_message += (
            f"错误信息: {e.stderr.decode('utf-8', errors='ignore').strip()}"
        )
        return error_message
    except Exception as e:
        return f"错误: 任务 {job_id} 发生意外异常: {e}"


def archive_by_size(
    source_dir, dest_dir, max_size_str, parallel_jobs, compression, compression_level
):
    """
    根据文件大小将源目录打包，并使用线程池控制并行度。
    """
    # --- 新增：记录开始时间 ---
    start_time = time.time()

    # --- 1. 检查和准备 ---
    print("--- 步骤 1: 检查与准备 ---")
    check_command("tar")

    source_dir = os.path.abspath(source_dir)
    dest_dir = os.path.abspath(dest_dir)
    max_size_bytes = parse_size_to_bytes(max_size_str)

    if not os.path.isdir(source_dir):
        print(f"错误: 源目录 '{source_dir}' 不存在。", file=sys.stderr)
        return

    os.makedirs(dest_dir, exist_ok=True)

    # 根据压缩选项确定文件扩展名和 tar 参数
    compression_map = {
        "none": (".tar", []),
        "gzip": (".tar.gz", ["-z"]),
        "zstd": (
            ".tar.zst",
            ["--zstd", f"--compress-program=zstd -{compression_level}"],
        ),
    }
    if compression not in compression_map:
        print(f"错误: 不支持的压缩格式 '{compression}'。", file=sys.stderr)
        return

    archive_ext, compression_args = compression_map[compression]

    # --- 2. 扫描文件并按大小分组 ---
    print(f"--- 步骤 2: 扫描文件并按最大 {max_size_str} 每包进行分组 ---")
    job_definitions = []
    current_chunk_files = []
    current_chunk_size = 0
    part_num = 1

    # 使用 os.walk 遍历目录
    for root, _, files in os.walk(source_dir):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, source_dir)

            try:
                if not os.path.islink(full_path):
                    file_size = os.path.getsize(full_path)
                else:
                    continue
            except OSError as e:
                print(f"警告: 无法访问文件 {full_path}，已跳过。错误: {e}")
                continue

            if current_chunk_files and (
                current_chunk_size + file_size > max_size_bytes
            ):
                archive_name = f"archive_part_{part_num:04d}{archive_ext}"
                archive_path = os.path.join(dest_dir, archive_name)
                # 直接将文件列表添加到任务定义中，而不是写入文件
                job_definitions.append(
                    (
                        list(current_chunk_files),
                        archive_path,
                        source_dir,
                        part_num,
                        compression_args,
                    )
                )

                part_num += 1
                current_chunk_files = []
                current_chunk_size = 0

            current_chunk_files.append(relative_path)
            current_chunk_size += file_size

    if current_chunk_files:
        archive_name = f"archive_part_{part_num:04d}{archive_ext}"
        archive_path = os.path.join(dest_dir, archive_name)
        job_definitions.append(
            (
                list(current_chunk_files),
                archive_path,
                source_dir,
                part_num,
                compression_args,
            )
        )

    if not job_definitions:
        print("警告: 源目录中没有文件可打包。")
        return

    print(f"分组完成，总共将生成 {len(job_definitions)} 个归档包。")

    # --- 3. 使用线程池并行执行打包 ---
    print(f"\n--- 步骤 3: 并行启动打包任务 (最多 {parallel_jobs} 个任务同时运行) ---")
    with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
        futures = [executor.submit(run_tar_job, job) for job in job_definitions]
        for future in as_completed(futures):
            result = future.result()
            print(f"  -> {result}")

    print("\n----------------------------------------")
    print("所有打包任务已成功完成！")
    print(f"归档文件位于: {dest_dir}")

    # --- 新增：计算并打印总耗时 ---
    end_time = time.time()
    duration = end_time - start_time
    print(f"总耗时: {duration:.2f} 秒。")
    print("----------------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="根据指定的最大文件大小，快速、并行地打包一个文件夹。此版本通过管道向tar传递文件列表以提高性能，并支持压缩。",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("source_dir", type=str, help="要打包的源文件夹路径。")
    parser.add_argument("dest_dir", type=str, help="用于存放打包文件的目标文件夹。")
    parser.add_argument(
        "-s",
        "--max-size",
        type=str,
        default="5G",
        help="每个归档包内容物的最大预估大小。\n支持单位: K, M, G, T (例如: '2G', '500M')。默认为 '5G'。",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=os.cpu_count() or 8,
        help="并行的任务数量 (即同时运行多少个 tar 进程)。默认为系统的CPU核心数。",
    )
    parser.add_argument(
        "-c",
        "--compression",
        type=str,
        default="none",
        choices=["none", "gzip", "zstd"],
        help="选择压缩算法。\n"
        " - none: 不压缩，速度最快，文件最大 (.tar)\n"
        " - gzip: 通用压缩，兼容性好 (.tar.gz)\n"
        " - zstd: 现代高效压缩，速度和压缩率俱佳 (.tar.zst)\n"
        "默认为 'none'。",
    )
    parser.add_argument(
        "--level",
        dest="compression_level",
        type=int,
        default=3,
        help="压缩级别 (仅对 zstd 有效)。范围 1-19。\n"
        "较低的级别速度更快，压缩率较低。默认为 3。",
    )

    args = parser.parse_args()
    archive_by_size(
        args.source_dir,
        args.dest_dir,
        args.max_size,
        args.jobs,
        args.compression,
        args.compression_level,
    )
