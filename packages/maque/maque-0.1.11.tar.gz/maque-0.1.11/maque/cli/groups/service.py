"""服务管理命令组"""
import os
import json
import subprocess
import time
import signal
import psutil
from pathlib import Path
from rich import print
from rich.table import Table
from rich.console import Console


class ServiceGroup:
    """服务管理命令组"""
    
    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()
        self.services_config_file = Path.home() / '.maque' / 'services.json'
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.services_config_file.parent.mkdir(exist_ok=True)
    
    def _load_services_config(self):
        """加载服务配置"""
        if self.services_config_file.exists():
            with open(self.services_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_services_config(self, config):
        """保存服务配置"""
        self._ensure_config_dir()
        with open(self.services_config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def list(self, status: bool = True):
        """列出已注册的服务
        
        Args:
            status: 是否显示服务状态，默认True
        """
        config = self._load_services_config()
        
        if not config:
            print("[yellow]没有已注册的服务[/yellow]")
            print("使用 'maque service register' 注册服务")
            return
        
        print("[bold blue]已注册的服务[/bold blue]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("服务名", style="cyan")
        table.add_column("端口", style="green")
        table.add_column("命令", style="yellow")
        if status:
            table.add_column("状态", style="blue")
            table.add_column("PID", style="dim")
        
        for service_name, service_info in config.items():
            port = str(service_info.get('port', 'N/A'))
            command = service_info.get('command', 'N/A')
            
            if status:
                service_status, pid = self._get_service_status(service_info)
                pid_str = str(pid) if pid else "N/A"
                
                status_color = {
                    'running': '[green]运行中[/green]',
                    'stopped': '[red]已停止[/red]',
                    'unknown': '[yellow]未知[/yellow]'
                }.get(service_status, service_status)
                
                table.add_row(service_name, port, command, status_color, pid_str)
            else:
                table.add_row(service_name, port, command)
        
        self.console.print(table)
    
    def register(
        self,
        name: str,
        command: str,
        port: int = None,
        working_dir: str = None,
        env_vars: str = None,
        description: str = None
    ):
        """注册新服务
        
        Args:
            name: 服务名称
            command: 启动命令
            port: 服务端口（可选）
            working_dir: 工作目录（可选）
            env_vars: 环境变量，格式: "KEY1=VALUE1,KEY2=VALUE2"
            description: 服务描述
            
        Examples:
            maque service register ollama "ollama serve" --port=11434
            maque service register my-api "python app.py" --port=8000 --working_dir="/path/to/app"
        """
        config = self._load_services_config()
        
        if name in config:
            print(f"[yellow]服务 '{name}' 已存在，是否覆盖？[/yellow]")
            response = input("(y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
        
        # 解析环境变量
        env_dict = {}
        if env_vars:
            for pair in env_vars.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    env_dict[key.strip()] = value.strip()
        
        service_config = {
            'command': command,
            'working_dir': working_dir or os.getcwd(),
            'env_vars': env_dict,
            'description': description or '',
            'created_at': str(time.time())
        }
        
        if port:
            service_config['port'] = port
        
        config[name] = service_config
        self._save_services_config(config)
        
        print(f"[green]✓ 服务 '{name}' 已注册[/green]")
    
    def unregister(self, name: str, force: bool = False):
        """注销服务
        
        Args:
            name: 服务名称
            force: 强制注销（不询问确认）
        """
        config = self._load_services_config()
        
        if name not in config:
            print(f"[red]服务 '{name}' 不存在[/red]")
            return
        
        # 检查服务是否在运行
        status, pid = self._get_service_status(config[name])
        if status == 'running':
            print(f"[yellow]警告: 服务 '{name}' 正在运行 (PID: {pid})[/yellow]")
            if not force:
                response = input("是否先停止服务并注销？(y/N): ")
                if response.lower() != 'y':
                    print("操作已取消")
                    return
                self.stop(name)
        
        del config[name]
        self._save_services_config(config)
        print(f"[green]✓ 服务 '{name}' 已注销[/green]")
    
    def start(self, name: str, detach: bool = True):
        """启动服务
        
        Args:
            name: 服务名称
            detach: 是否后台运行，默认True
        """
        config = self._load_services_config()
        
        if name not in config:
            print(f"[red]服务 '{name}' 不存在[/red]")
            print("使用 'maque service list' 查看已注册的服务")
            return
        
        service_info = config[name]
        status, pid = self._get_service_status(service_info)
        
        if status == 'running':
            print(f"[yellow]服务 '{name}' 已在运行 (PID: {pid})[/yellow]")
            return
        
        print(f"[blue]启动服务 '{name}'...[/blue]")
        
        # 准备环境
        env = os.environ.copy()
        env.update(service_info.get('env_vars', {}))
        
        working_dir = service_info.get('working_dir', os.getcwd())
        command = service_info['command']
        
        try:
            if detach:
                # 后台启动
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=working_dir,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                
                # 等待一小段时间确认启动
                time.sleep(2)
                if process.poll() is None:
                    # 保存PID信息
                    config[name]['pid'] = process.pid
                    config[name]['last_started'] = str(time.time())
                    self._save_services_config(config)
                    
                    print(f"[green]✓ 服务 '{name}' 已启动 (PID: {process.pid})[/green]")
                else:
                    print(f"[red]✗ 服务 '{name}' 启动失败[/red]")
            else:
                # 前台启动
                print(f"[blue]在前台运行服务 '{name}'...[/blue]")
                print(f"命令: {command}")
                print(f"工作目录: {working_dir}")
                print("按 Ctrl+C 停止服务\n")
                
                subprocess.run(command, shell=True, cwd=working_dir, env=env)
                
        except KeyboardInterrupt:
            print(f"\n[yellow]服务 '{name}' 已中断[/yellow]")
        except Exception as e:
            print(f"[red]启动服务失败: {e}[/red]")
    
    def stop(self, name: str, timeout: int = 10):
        """停止服务
        
        Args:
            name: 服务名称
            timeout: 超时时间（秒），默认10秒
        """
        config = self._load_services_config()
        
        if name not in config:
            print(f"[red]服务 '{name}' 不存在[/red]")
            return
        
        service_info = config[name]
        status, pid = self._get_service_status(service_info)
        
        if status != 'running':
            print(f"[yellow]服务 '{name}' 未在运行[/yellow]")
            return
        
        print(f"[blue]停止服务 '{name}' (PID: {pid})...[/blue]")
        
        try:
            process = psutil.Process(pid)
            
            # 优雅停止
            process.terminate()
            
            # 等待进程结束
            try:
                process.wait(timeout=timeout)
                print(f"[green]✓ 服务 '{name}' 已停止[/green]")
            except psutil.TimeoutExpired:
                # 强制终止
                print(f"[yellow]服务超时，强制终止...[/yellow]")
                process.kill()
                process.wait(timeout=5)
                print(f"[green]✓ 服务 '{name}' 已强制停止[/green]")
            
            # 清理PID信息
            if 'pid' in config[name]:
                del config[name]['pid']
            config[name]['last_stopped'] = str(time.time())
            self._save_services_config(config)
            
        except psutil.NoSuchProcess:
            print(f"[yellow]进程不存在，清理服务状态[/yellow]")
            if 'pid' in config[name]:
                del config[name]['pid']
            self._save_services_config(config)
        except Exception as e:
            print(f"[red]停止服务失败: {e}[/red]")
    
    def restart(self, name: str):
        """重启服务
        
        Args:
            name: 服务名称
        """
        print(f"[blue]重启服务 '{name}'...[/blue]")
        self.stop(name)
        time.sleep(1)
        self.start(name)
    
    def status(self, name: str = None):
        """显示服务状态
        
        Args:
            name: 服务名称，不指定则显示所有服务状态
        """
        config = self._load_services_config()
        
        if not config:
            print("[yellow]没有已注册的服务[/yellow]")
            return
        
        if name:
            if name not in config:
                print(f"[red]服务 '{name}' 不存在[/red]")
                return
            
            self._show_service_detail(name, config[name])
        else:
            # 显示所有服务状态
            self.list(status=True)
    
    def _show_service_detail(self, name, service_info):
        """显示单个服务的详细信息"""
        status, pid = self._get_service_status(service_info)
        
        print(f"[bold blue]服务详情: {name}[/bold blue]\n")
        
        detail_table = Table(show_header=False, box=None)
        detail_table.add_column("属性", style="cyan")
        detail_table.add_column("值", style="green")
        
        detail_table.add_row("状态", {
            'running': '[green]运行中[/green]',
            'stopped': '[red]已停止[/red]',
            'unknown': '[yellow]未知[/yellow]'
        }.get(status, status))
        
        if pid:
            detail_table.add_row("PID", str(pid))
        
        detail_table.add_row("命令", service_info.get('command', 'N/A'))
        detail_table.add_row("工作目录", service_info.get('working_dir', 'N/A'))
        
        if service_info.get('port'):
            detail_table.add_row("端口", str(service_info['port']))
        
        if service_info.get('description'):
            detail_table.add_row("描述", service_info['description'])
        
        # 环境变量
        env_vars = service_info.get('env_vars', {})
        if env_vars:
            env_str = ", ".join([f"{k}={v}" for k, v in env_vars.items()])
            detail_table.add_row("环境变量", env_str)
        
        # 时间信息
        if service_info.get('last_started'):
            start_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                     time.localtime(float(service_info['last_started'])))
            detail_table.add_row("最后启动", start_time)
        
        if service_info.get('last_stopped'):
            stop_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.localtime(float(service_info['last_stopped'])))
            detail_table.add_row("最后停止", stop_time)
        
        self.console.print(detail_table)
    
    def _get_service_status(self, service_info):
        """获取服务状态"""
        pid = service_info.get('pid')
        
        if not pid:
            return 'stopped', None
        
        try:
            process = psutil.Process(pid)
            if process.is_running():
                return 'running', pid
            else:
                return 'stopped', None
        except psutil.NoSuchProcess:
            return 'stopped', None
        except Exception:
            return 'unknown', pid
    
    def logs(self, name: str, lines: int = 50, follow: bool = False):
        """查看服务日志
        
        Args:
            name: 服务名称
            lines: 显示行数，默认50行
            follow: 是否持续跟踪日志，默认False
        """
        config = self._load_services_config()
        
        if name not in config:
            print(f"[red]服务 '{name}' 不存在[/red]")
            return
        
        service_info = config[name]
        log_file = Path.home() / '.maque' / 'logs' / f'{name}.log'
        
        if not log_file.exists():
            print(f"[yellow]服务 '{name}' 的日志文件不存在[/yellow]")
            print(f"预期位置: {log_file}")
            return
        
        try:
            if follow:
                print(f"[blue]跟踪服务 '{name}' 的日志 (按 Ctrl+C 停止)[/blue]\n")
                # 简单的tail -f实现
                import subprocess
                subprocess.run(['tail', '-f', str(log_file)])
            else:
                print(f"[blue]服务 '{name}' 的最近 {lines} 行日志[/blue]\n")
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    for line in recent_lines:
                        print(line.rstrip())
                        
        except KeyboardInterrupt:
            print(f"\n[yellow]停止跟踪日志[/yellow]")
        except Exception as e:
            print(f"[red]读取日志失败: {e}[/red]")
    
    def health(self, name: str = None):
        """检查服务健康状态
        
        Args:
            name: 服务名称，不指定则检查所有服务
        """
        config = self._load_services_config()
        
        if not config:
            print("[yellow]没有已注册的服务[/yellow]")
            return
        
        services_to_check = [name] if name else list(config.keys())
        
        print("[bold blue]服务健康检查[/bold blue]\n")
        
        health_table = Table(show_header=True, header_style="bold magenta")
        health_table.add_column("服务名", style="cyan")
        health_table.add_column("状态", style="green")
        health_table.add_column("端口检查", style="yellow")
        health_table.add_column("响应时间", style="blue")
        
        for service_name in services_to_check:
            if service_name not in config:
                continue
                
            service_info = config[service_name]
            status, pid = self._get_service_status(service_info)
            
            # 端口检查
            port_status = "N/A"
            response_time = "N/A"
            
            if service_info.get('port'):
                port_check, resp_time = self._check_port_health(service_info['port'])
                port_status = "[green]正常[/green]" if port_check else "[red]异常[/red]"
                response_time = f"{resp_time:.2f}ms" if resp_time else "N/A"
            
            status_display = {
                'running': '[green]运行中[/green]',
                'stopped': '[red]已停止[/red]',
                'unknown': '[yellow]未知[/yellow]'
            }.get(status, status)
            
            health_table.add_row(service_name, status_display, port_status, response_time)
        
        self.console.print(health_table)
    
    def _check_port_health(self, port):
        """检查端口健康状态"""
        import socket
        import time
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            response_time = (time.time() - start_time) * 1000
            return result == 0, response_time
        except Exception:
            return False, None