"""系统工具命令组

包含端口管理、IP获取、压缩解压、文件分割合并、SSH密钥生成、计时器等系统工具。
"""
from __future__ import annotations

import os
import time
import sys
from pathlib import Path
from rich import print


class SystemGroup:
    """系统工具命令组"""

    def __init__(self, parent):
        self.parent = parent

    @staticmethod
    def kill(ports, view: bool = False):
        """杀死指定端口的进程

        跨平台支持 Linux/macOS/Windows

        Args:
            ports: 端口号，可以是单个整数或逗号分隔的多个端口，如 "8080" 或 "8080,3000,5000"
            view: 仅查看进程信息，不执行杀死操作

        Examples:
            spr system kill 8080
            spr system kill 8080,3000,5000
            spr system kill 8080 --view  # 仅查看
        """
        import psutil
        import platform

        # 处理端口参数
        if isinstance(ports, str):
            port_list = [int(p.strip()) for p in ports.split(',') if p.strip()]
        elif isinstance(ports, (int, float)):
            port_list = [int(ports)]
        elif isinstance(ports, (list, tuple)):
            port_list = [int(p) for p in ports]
        else:
            print(f"[red]无效的端口参数: {ports}[/red]")
            return False

        if not port_list:
            print("[yellow]请提供要杀死的端口号[/yellow]")
            return False

        found_any = False

        for port in port_list:
            processes_found = []

            # 使用 psutil 跨平台查找进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    connections = proc.connections(kind='inet')
                    for conn in connections:
                        if hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                            processes_found.append({
                                'pid': proc.pid,
                                'name': proc.info['name'],
                                'port': port,
                                'process': proc
                            })
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue

            if not processes_found:
                print(f"[yellow]端口 {port} 没有找到运行的进程[/yellow]")
                continue

            found_any = True

            for pinfo in processes_found:
                if view:
                    print(f"[cyan]👁️  {pinfo['name']} (PID: {pinfo['pid']}) 占用端口 {pinfo['port']}[/cyan]")
                else:
                    try:
                        pinfo['process'].terminate()
                        # 等待进程结束
                        try:
                            pinfo['process'].wait(timeout=3)
                        except psutil.TimeoutExpired:
                            # 强制杀死
                            pinfo['process'].kill()
                        print(f"[green]☠️  已杀死 {pinfo['name']} (PID: {pinfo['pid']}) 端口 {pinfo['port']}[/green]")
                    except psutil.NoSuchProcess:
                        print(f"[yellow]进程 {pinfo['pid']} 已不存在[/yellow]")
                    except psutil.AccessDenied:
                        print(f"[red]无权限杀死进程 {pinfo['pid']}，请使用管理员/root权限运行[/red]")
                    except Exception as e:
                        print(f"[red]杀死进程 {pinfo['pid']} 失败: {e}[/red]")

        if not found_any:
            print(f"[yellow]🙃 没有找到占用指定端口的进程[/yellow]")

        return found_any

    @staticmethod
    def get_ip(env: str = "inner"):
        """获取本机IP地址

        Args:
            env: "inner" 获取内网IP，"outer" 获取外网IP

        Examples:
            spr system get_ip
            spr system get_ip --env=outer
        """
        import socket

        if env == "inner":
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(('8.8.8.8', 80))
                    ip = s.getsockname()[0]
                    print(f"[green]内网IP: {ip}[/green]")
                    return ip
            except Exception as e:
                print(f"[red]获取内网IP失败: {e}[/red]")
                return None
        elif env == "outer":
            try:
                import requests
                ip = requests.get('http://ifconfig.me/ip', timeout=5).text.strip()
                print(f"[green]外网IP: {ip}[/green]")
                return ip
            except ImportError:
                print("[red]需要安装 requests 库: pip install requests[/red]")
                return None
            except Exception as e:
                print(f"[red]获取外网IP失败: {e}[/red]")
                return None
        else:
            print(f"[red]无效的 env 参数: {env}，应为 'inner' 或 'outer'[/red]")
            return None

    @staticmethod
    def pack(source_path: str, target_path: str = None, format: str = 'gztar'):
        """压缩文件或文件夹

        Args:
            source_path: 源文件/文件夹路径
            target_path: 目标压缩包路径（不含扩展名），默认与源同名
            format: 压缩格式，支持 "zip", "tar", "gztar"(默认), "bztar", "xztar"

        Examples:
            spr system pack my_folder
            spr system pack my_folder --format=zip
            spr system pack ./data --target_path=backup
        """
        import shutil

        if target_path is None:
            target_path = Path(source_path).name

        try:
            new_path = shutil.make_archive(target_path, format, root_dir=source_path)
            print(f"[green]✓ 压缩完成: {new_path}[/green]")
            return new_path
        except Exception as e:
            print(f"[red]压缩失败: {e}[/red]")
            return None

    @staticmethod
    def unpack(filename: str, extract_dir: str = None, format: str = None):
        """解压文件

        Args:
            filename: 压缩包路径
            extract_dir: 解压目标目录，默认为压缩包同名目录
            format: 压缩格式，默认自动检测。支持 "zip", "tar", "gztar", "bztar", "xztar"

        Examples:
            spr system unpack archive.tar.gz
            spr system unpack data.zip --extract_dir=./output
        """
        import shutil
        from shutil import _find_unpack_format, _UNPACK_FORMATS

        file_path = Path(filename)
        if not file_path.exists():
            print(f"[red]文件不存在: {filename}[/red]")
            return None

        # 自动确定解压目录名
        if extract_dir is None:
            name = file_path.name
            file_format = _find_unpack_format(filename)
            if file_format:
                file_postfix_list = _UNPACK_FORMATS[file_format][0]
                for postfix in file_postfix_list:
                    if name.endswith(postfix):
                        target_name = name[:-len(postfix)]
                        break
                else:
                    target_name = name.replace('.', '_')
            else:
                target_name = name.replace('.', '_')
            extract_dir = f"./{target_name}/"

        extract_path = Path(extract_dir)
        if not extract_path.exists():
            extract_path.mkdir(parents=True)

        try:
            shutil.unpack_archive(filename, extract_dir, format=format)
            print(f"[green]✓ 解压完成: {extract_path.absolute()}[/green]")
            return str(extract_path.absolute())
        except Exception as e:
            print(f"[red]解压失败: {e}[/red]")
            return None

    @staticmethod
    def split(file_path: str, chunk_size: str = "1G"):
        """将大文件分割成多个块

        Args:
            file_path: 原始文件路径
            chunk_size: 每个块的大小，支持 K/M/G 后缀，默认 1G

        Examples:
            spr system split large_file.dat
            spr system split video.mp4 --chunk_size=500M
            spr system split data.bin --chunk_size=100M
        """
        # 解析大小
        size_str = str(chunk_size).upper().strip()
        multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3}

        if size_str[-1] in multipliers:
            chunk_bytes = int(float(size_str[:-1]) * multipliers[size_str[-1]])
        else:
            chunk_bytes = int(size_str)

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            print(f"[red]文件不存在: {file_path}[/red]")
            return None

        file_size = file_path_obj.stat().st_size
        total_chunks = (file_size + chunk_bytes - 1) // chunk_bytes

        print(f"[blue]分割文件: {file_path}[/blue]")
        print(f"文件大小: {file_size / 1024**2:.2f} MB")
        print(f"块大小: {chunk_bytes / 1024**2:.2f} MB")
        print(f"预计分割为 {total_chunks} 个块")

        try:
            with open(file_path, 'rb') as f:
                chunk_number = 0
                while True:
                    chunk = f.read(chunk_bytes)
                    if not chunk:
                        break
                    chunk_file = f"{file_path}_part_{chunk_number:03d}"
                    with open(chunk_file, 'wb') as cf:
                        cf.write(chunk)
                    print(f"  [green]✓[/green] {chunk_file} ({len(chunk) / 1024**2:.2f} MB)")
                    chunk_number += 1

            print(f"[green]✓ 分割完成，共 {chunk_number} 个块[/green]")
            return chunk_number
        except Exception as e:
            print(f"[red]分割失败: {e}[/red]")
            return None

    @staticmethod
    def merge(input_prefix: str, input_dir: str = '.', output_path: str = None):
        """合并分割后的文件块

        Args:
            input_prefix: 分割文件的前缀（原文件名）
            input_dir: 分割文件所在目录，默认当前目录
            output_path: 合并后的文件路径，默认为 input_prefix

        Examples:
            spr system merge large_file.dat
            spr system merge video.mp4 --input_dir=./chunks
            spr system merge data.bin --output_path=restored.bin
        """
        import glob

        if output_path is None:
            output_path = os.path.join(input_dir, input_prefix)

        # 查找所有分块文件
        pattern = os.path.join(input_dir, f"{input_prefix}_part_*")
        parts = sorted(glob.glob(pattern))

        if not parts:
            print(f"[red]没有找到匹配的分块文件: {pattern}[/red]")
            return None

        print(f"[blue]合并文件块[/blue]")
        print(f"找到 {len(parts)} 个分块文件")

        try:
            total_size = 0
            with open(output_path, 'wb') as output_file:
                for part in parts:
                    with open(part, 'rb') as part_file:
                        data = part_file.read()
                        output_file.write(data)
                        total_size += len(data)
                    print(f"  [green]✓[/green] {Path(part).name}")

            print(f"[green]✓ 合并完成: {output_path} ({total_size / 1024**2:.2f} MB)[/green]")
            return output_path
        except Exception as e:
            print(f"[red]合并失败: {e}[/red]")
            return None

    @staticmethod
    def gen_key(name: str, email: str = None, key_type: str = 'rsa'):
        """生成SSH密钥对

        Args:
            name: 密钥名称，将保存为 ~/.ssh/id_{type}_{name}
            email: 关联的邮箱地址
            key_type: 密钥类型，"rsa"(默认) 或 "ed25519"(推荐)

        Examples:
            spr system gen_key github
            spr system gen_key myserver --email=me@example.com
            spr system gen_key legacy --key_type=rsa
        """
        import subprocess

        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(exist_ok=True)

        if key_type == 'ed25519':
            key_path = ssh_dir / f'id_ed25519_{name}'
            cmd = ['ssh-keygen', '-t', 'ed25519', '-f', str(key_path), '-N', '']
        else:
            key_path = ssh_dir / f'id_rsa_{name}'
            cmd = ['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', str(key_path), '-N', '']

        if email:
            cmd.extend(['-C', email])

        if key_path.exists():
            print(f"[yellow]密钥已存在: {key_path}[/yellow]")
            response = input("是否覆盖? (y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return None

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[red]生成密钥失败: {result.stderr}[/red]")
                return None

            # 读取并显示公钥
            pub_key_path = str(key_path) + '.pub'
            with open(pub_key_path, 'r', encoding='utf-8') as f:
                pub_key = f.read().strip()

            print(f"[green]✓ 密钥生成成功[/green]")
            print(f"\n[cyan]私钥路径:[/cyan] {key_path}")
            print(f"[cyan]公钥路径:[/cyan] {pub_key_path}")
            print(f"\n[cyan]公钥内容:[/cyan]")
            print(f"[dim]{pub_key}[/dim]")

            # 显示配置提示
            config_path = ssh_dir / 'config'
            print(f"""
[yellow]提示: 你可能需要在 {config_path} 中添加以下配置:[/yellow]

[dim]# 远程服务器
Host {name}
  HostName <服务器IP或域名>
  User <用户名>
  Port 22
  IdentityFile {key_path}

# 或 Git 服务
Host {name}
  HostName github.com
  User git
  IdentityFile {key_path}
  IdentitiesOnly yes[/dim]
""")
            return str(key_path)
        except FileNotFoundError:
            print("[red]ssh-keygen 命令不可用，请确保已安装 OpenSSH[/red]")
            return None
        except Exception as e:
            print(f"[red]生成密钥失败: {e}[/red]")
            return None

    @staticmethod
    def timer(interval: float = 0.05):
        """交互式计时器工具

        支持开始、暂停、记录点、停止功能

        快捷键:
            Space/S: 开始 / 暂停
            L: 记录点 (Lap)
            Q: 停止并退出

        Args:
            interval: 刷新间隔（秒），默认 0.05

        Examples:
            spr system timer
            spr system timer --interval=0.1
        """
        def format_time(seconds):
            """格式化时间显示"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
            elif minutes > 0:
                return f"{minutes:02d}:{secs:05.2f}"
            else:
                return f"{secs:.2f}"

        # 跨平台非阻塞键盘输入
        class KeyReader:
            def __init__(self):
                self.is_windows = os.name == 'nt'
                if self.is_windows:
                    import msvcrt
                    self.msvcrt = msvcrt
                else:
                    import termios
                    import tty
                    import select
                    self.termios = termios
                    self.tty = tty
                    self.select = select
                    self.fd = sys.stdin.fileno()
                    self.old_settings = termios.tcgetattr(self.fd)

            def setup(self):
                if not self.is_windows:
                    self.tty.setraw(self.fd)

            def cleanup(self):
                if not self.is_windows:
                    self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.old_settings)

            def get_key(self):
                """非阻塞获取按键，返回 None 如果没有按键"""
                if self.is_windows:
                    if self.msvcrt.kbhit():
                        ch = self.msvcrt.getch()
                        return ch.decode('utf-8', errors='ignore').lower()
                    return None
                else:
                    if self.select.select([sys.stdin], [], [], 0)[0]:
                        ch = sys.stdin.read(1)
                        return ch.lower()
                    return None

        # 进入 raw 模式前使用 rich 格式
        print("[cyan]═══════════════════════════════════════[/cyan]")
        print("[cyan]           交互式计时器[/cyan]")
        print("[cyan]═══════════════════════════════════════[/cyan]")
        print()
        print("快捷键:")
        print("  [green]S / Space[/green]  开始 / 暂停")
        print("  [yellow]L[/yellow]          记录点 (Lap)")
        print("  [red]Q[/red]          停止并退出")
        print()
        print("[yellow]按 S 开始计时...[/yellow]")
        print()

        key_reader = KeyReader()
        key_reader.setup()

        # raw 模式下使用 ANSI 颜色码和 \r\n 换行
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        NL = "\r\n"

        try:
            # 等待开始
            while True:
                key = key_reader.get_key()
                if key in ('s', ' '):
                    break
                if key == 'q':
                    key_reader.cleanup()
                    print("[yellow]已退出[/yellow]")
                    return
                time.sleep(0.05)

            t0 = time.time()
            total_paused = 0.0
            suspend_start = None
            paused = False
            laps = []
            last_lap_time = 0.0

            sys.stdout.write(f"{GREEN}▶ 计时开始{RESET}{NL}{NL}")
            sys.stdout.flush()

            while True:
                time.sleep(interval)
                ct = time.time()

                # 检查按键
                key = key_reader.get_key()
                if key == 'q':
                    break
                elif key in ('s', ' '):
                    paused = not paused
                    if paused:
                        suspend_start = ct
                        current_time = ct - t0 - total_paused
                        sys.stdout.write(f"\r\033[K{YELLOW}⏸ {format_time(current_time)} [暂停 - 按S继续]{RESET}")
                        sys.stdout.flush()
                    else:
                        if suspend_start:
                            total_paused += ct - suspend_start
                            suspend_start = None
                        sys.stdout.write(NL)
                        sys.stdout.flush()
                elif key == 'l' and not paused:
                    current_time = ct - t0 - total_paused
                    lap_time = current_time - last_lap_time
                    laps.append((current_time, lap_time))
                    last_lap_time = current_time
                    sys.stdout.write(f"\r\033[K{YELLOW}Lap {len(laps)}: {format_time(current_time)} ({CYAN}+{format_time(lap_time)}{YELLOW}){RESET}{NL}")
                    sys.stdout.flush()

                # 更新显示
                if not paused:
                    current_time = ct - t0 - total_paused
                    sys.stdout.write(f"\r{GREEN}▶ {format_time(current_time)}{RESET}")
                    sys.stdout.flush()

            # 计算最终时间
            final_time = time.time() - t0 - total_paused
            if suspend_start:
                final_time -= (time.time() - suspend_start)

            sys.stdout.write(f"{NL}{NL}")
            sys.stdout.write(f"{RED}■ 计时停止{RESET}{NL}{NL}")
            sys.stdout.write(f"{CYAN}═══════════════════════════════════════{RESET}{NL}")
            sys.stdout.write(f"{BOLD}总计时间: {format_time(final_time)}{RESET}{NL}")

            if laps:
                sys.stdout.write(f"{NL}{YELLOW}记录点:{RESET}{NL}")
                for i, (total, lap) in enumerate(laps, 1):
                    sys.stdout.write(f"  Lap {i}: {format_time(total)} ({CYAN}+{format_time(lap)}{RESET}){NL}")

            sys.stdout.write(f"{CYAN}═══════════════════════════════════════{RESET}{NL}")
            sys.stdout.flush()

        except Exception as e:
            sys.stdout.write(f"{NL}错误: {e}{NL}")
        finally:
            key_reader.cleanup()
