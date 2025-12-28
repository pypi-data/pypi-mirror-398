"""数据处理命令组"""
import json
import csv
from pathlib import Path
from maque.io import jsonl_load
from typing import Union, Optional, List
from rich import print
from rich.table import Table
from rich.console import Console


class DataGroup:
    """数据处理命令组"""
    
    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()
    
    def table_viewer(
        self,
        file_path: str = None,
        port: int = 8080,
        host: str = "127.0.0.1",
        sheet_name: Union[str, int] = 0,
        image_columns: str = None,
        auto_detect_images: bool = True,
        auto_open: bool = True,
        **kwargs
    ):
        """启动交互式表格查看器
        
        Args:
            file_path: 表格文件路径（支持.xlsx, .xls, .csv格式）
            port: 服务器端口，默认8080
            host: 服务器主机地址，默认127.0.0.1
            sheet_name: Excel文件的sheet名称或索引，默认为0
            image_columns: 指定图片列名，用逗号分隔
            auto_detect_images: 是否自动检测图片列，默认True
            auto_open: 是否自动打开浏览器，默认True
            
        Examples:
            maque data table-viewer data.xlsx
            maque data table-viewer "products.csv" --port=9090
        """
        # 直接调用 table_viewer 实现，避免循环引用
        from maque.table_viewer import start_table_viewer
        
        # 处理 image_columns 参数
        if image_columns:
            image_columns = [col.strip() for col in image_columns.split(',')]
        
        return start_table_viewer(
            file_path=file_path,
            port=port,
            host=host,
            sheet_name=sheet_name,
            image_columns=image_columns,
            auto_detect_images=auto_detect_images,
            auto_open=auto_open
        )
    
    def convert(
        self,
        input_file: str,
        output_file: str = None,
        sheet_name: Union[str, int] = 0,
        encoding: str = "utf-8",
        delimiter: str = ",",
        **kwargs
    ):
        """数据格式转换
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径，不指定则自动生成
            sheet_name: Excel sheet名称或索引
            encoding: 文件编码，默认utf-8
            delimiter: CSV分隔符，默认逗号
            **kwargs: 其他pandas读取参数
            
        Examples:
            maque data convert input.xlsx output.csv
            maque data convert data.csv data.xlsx
            maque data convert file.xlsx --sheet_name="Sheet2"
        """
        import pandas as pd
        
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"[red]输入文件不存在: {input_file}[/red]")
            return False
        
        # 自动生成输出文件名
        if not output_file:
            if input_path.suffix.lower() == '.csv':
                output_file = str(input_path.with_suffix('.xlsx'))
            else:
                output_file = str(input_path.with_suffix('.csv'))
        
        output_path = Path(output_file)
        
        try:
            # 读取输入文件
            input_ext = input_path.suffix.lower()
            if input_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(input_file, sheet_name=sheet_name, **kwargs)
                print(f"[green]✓[/green] 读取Excel文件: {input_file} (sheet: {sheet_name})")
            elif input_ext == '.csv':
                df = pd.read_csv(input_file, encoding=encoding, delimiter=delimiter, **kwargs)
                print(f"[green]✓[/green] 读取CSV文件: {input_file}")
            else:
                print(f"[red]不支持的输入格式: {input_ext}[/red]")
                return False
            
            # 写入输出文件
            output_ext = output_path.suffix.lower()
            if output_ext in ['.xlsx', '.xls']:
                df.to_excel(output_file, index=False)
                print(f"[green]✓[/green] 保存为Excel文件: {output_file}")
            elif output_ext == '.csv':
                df.to_csv(output_file, index=False, encoding=encoding)
                print(f"[green]✓[/green] 保存为CSV文件: {output_file}")
            elif output_ext == '.json':
                df.to_json(output_file, orient='records', ensure_ascii=False, indent=2)
                print(f"[green]✓[/green] 保存为JSON文件: {output_file}")
            else:
                print(f"[red]不支持的输出格式: {output_ext}[/red]")
                return False
            
            print(f"数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
            return True
            
        except Exception as e:
            print(f"[red]转换失败: {e}[/red]")
            return False
    
    def stats(
        self,
        file_path: str,
        sheet_name: Union[str, int] = 0,
        columns: str = None,
        output_file: str = None,
        **kwargs
    ):
        """数据统计分析
        
        Args:
            file_path: 文件路径
            sheet_name: Excel sheet名称或索引
            columns: 分析的列名，用逗号分隔，不指定则分析所有数值列
            output_file: 统计结果保存文件（可选）
            **kwargs: 其他pandas读取参数
            
        Examples:
            maque data stats data.csv
            maque data stats data.xlsx --columns="age,price"
            maque data stats file.csv --output_file="stats.json"
        """
        import pandas as pd
        import numpy as np
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            print(f"[red]文件不存在: {file_path}[/red]")
            return
        
        try:
            # 读取文件
            file_ext = file_path_obj.suffix.lower()
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            elif file_ext == '.csv':
                df = pd.read_csv(file_path, **kwargs)
            else:
                print(f"[red]不支持的文件格式: {file_ext}[/red]")
                return
            
            print(f"[blue]数据统计分析: {file_path}[/blue]")
            print(f"数据形状: {df.shape[0]} 行 × {df.shape[1]} 列\n")
            
            # 选择要分析的列
            if columns:
                col_list = [col.strip() for col in columns.split(',')]
                missing_cols = [col for col in col_list if col not in df.columns]
                if missing_cols:
                    print(f"[yellow]警告: 以下列不存在: {missing_cols}[/yellow]")
                col_list = [col for col in col_list if col in df.columns]
                df_analyze = df[col_list]
            else:
                # 自动选择数值列
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_columns:
                    print("[yellow]未找到数值列，显示所有列的基本信息[/yellow]")
                    df_analyze = df
                else:
                    df_analyze = df[numeric_columns]
            
            # 基本统计信息
            stats_dict = {}
            
            print("[bold cyan]基本信息[/bold cyan]")
            info_table = Table(show_header=True, header_style="bold magenta")
            info_table.add_column("指标", style="cyan")
            info_table.add_column("值", style="green")
            
            info_table.add_row("总行数", str(df.shape[0]))
            info_table.add_row("总列数", str(df.shape[1]))
            info_table.add_row("缺失值总数", str(df.isnull().sum().sum()))
            info_table.add_row("内存使用", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            self.console.print(info_table)
            
            stats_dict['basic_info'] = {
                'rows': df.shape[0],
                'columns': df.shape[1],
                'missing_values': int(df.isnull().sum().sum()),
                'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024**2, 2)
            }
            
            # 数值列统计
            numeric_cols = df_analyze.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                print(f"\n[bold cyan]数值列统计 ({len(numeric_cols)} 列)[/bold cyan]")
                desc = df_analyze[numeric_cols].describe()
                
                # 创建统计表格
                stats_table = Table(show_header=True, header_style="bold magenta")
                stats_table.add_column("统计量", style="cyan")
                for col in numeric_cols[:5]:  # 限制显示列数
                    stats_table.add_column(col, style="green")
                
                for stat in ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']:
                    row_data = [stat]
                    for col in numeric_cols[:5]:
                        value = desc.loc[stat, col]
                        if stat == 'count':
                            row_data.append(f"{int(value)}")
                        else:
                            row_data.append(f"{value:.2f}")
                    stats_table.add_row(*row_data)
                
                self.console.print(stats_table)
                
                if len(numeric_cols) > 5:
                    print(f"[dim]... 还有 {len(numeric_cols) - 5} 列未显示[/dim]")
                
                stats_dict['numeric_stats'] = desc.to_dict()
            
            # 文本列信息
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            if text_cols:
                print(f"\n[bold cyan]文本列信息 ({len(text_cols)} 列)[/bold cyan]")
                
                text_table = Table(show_header=True, header_style="bold magenta")
                text_table.add_column("列名", style="cyan")
                text_table.add_column("唯一值数量", style="green")
                text_table.add_column("最常见值", style="yellow")
                text_table.add_column("缺失值", style="red")
                
                text_stats = {}
                for col in text_cols[:10]:  # 限制显示列数
                    unique_count = df[col].nunique()
                    most_common = df[col].mode().iloc[0] if not df[col].mode().empty else "N/A"
                    missing_count = df[col].isnull().sum()
                    
                    text_table.add_row(
                        col,
                        str(unique_count),
                        str(most_common)[:20] + "..." if len(str(most_common)) > 20 else str(most_common),
                        str(missing_count)
                    )
                    
                    text_stats[col] = {
                        'unique_count': int(unique_count),
                        'most_common': str(most_common),
                        'missing_count': int(missing_count)
                    }
                
                self.console.print(text_table)
                
                if len(text_cols) > 10:
                    print(f"[dim]... 还有 {len(text_cols) - 10} 列未显示[/dim]")
                
                stats_dict['text_stats'] = text_stats
            
            # 缺失值分析
            missing_data = df.isnull().sum()
            missing_data = missing_data[missing_data > 0]
            
            if len(missing_data) > 0:
                print(f"\n[bold cyan]缺失值分析[/bold cyan]")
                missing_table = Table(show_header=True, header_style="bold magenta")
                missing_table.add_column("列名", style="cyan")
                missing_table.add_column("缺失数量", style="red")
                missing_table.add_column("缺失比例", style="yellow")
                
                missing_stats = {}
                for col, count in missing_data.items():
                    percentage = (count / len(df)) * 100
                    missing_table.add_row(col, str(count), f"{percentage:.2f}%")
                    missing_stats[col] = {
                        'missing_count': int(count),
                        'missing_percentage': round(percentage, 2)
                    }
                
                self.console.print(missing_table)
                stats_dict['missing_data'] = missing_stats
            
            # 保存统计结果
            if output_file:
                output_path = Path(output_file)
                if output_path.suffix.lower() == '.json':
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(stats_dict, f, ensure_ascii=False, indent=2)
                elif output_path.suffix.lower() == '.csv':
                    # 将基本统计保存为CSV
                    if 'numeric_stats' in stats_dict:
                        pd.DataFrame(stats_dict['numeric_stats']).to_csv(output_file)
                else:
                    print(f"[yellow]不支持的输出格式，使用JSON格式[/yellow]")
                    output_file = output_path.with_suffix('.json')
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(stats_dict, f, ensure_ascii=False, indent=2)
                
                print(f"\n[green]✓ 统计结果已保存到: {output_file}[/green]")
            
        except Exception as e:
            print(f"[red]分析失败: {e}[/red]")
    
    def validate(
        self,
        file_path: str,
        schema_file: str = None,
        rules: str = None,
        output_file: str = None,
        **kwargs
    ):
        """数据验证
        
        Args:
            file_path: 数据文件路径
            schema_file: 验证模式文件（JSON格式）
            rules: 验证规则，用分号分隔，格式: "column:rule"
            output_file: 验证结果保存文件
            **kwargs: 其他参数
            
        Examples:
            maque data validate data.csv --rules="age:>0;price:>0"
            maque data validate data.xlsx --schema_file=schema.json
        """
        import pandas as pd
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            print(f"[red]文件不存在: {file_path}[/red]")
            return False
        
        try:
            # 读取数据
            file_ext = file_path_obj.suffix.lower()
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, **kwargs)
            elif file_ext == '.csv':
                df = pd.read_csv(file_path, **kwargs)
            else:
                print(f"[red]不支持的文件格式: {file_ext}[/red]")
                return False
            
            print(f"[blue]数据验证: {file_path}[/blue]")
            print(f"数据形状: {df.shape[0]} 行 × {df.shape[1]} 列\n")
            
            validation_results = []
            total_errors = 0
            
            # 使用规则验证
            if rules:
                rule_list = rules.split(';')
                for rule in rule_list:
                    if ':' not in rule:
                        continue
                    
                    column, condition = rule.split(':', 1)
                    column = column.strip()
                    condition = condition.strip()
                    
                    if column not in df.columns:
                        validation_results.append({
                            'rule': rule,
                            'column': column,
                            'status': 'error',
                            'message': f'列 "{column}" 不存在',
                            'failed_rows': []
                        })
                        total_errors += 1
                        continue
                    
                    try:
                        # 简单的验证规则解析
                        if condition.startswith('>'):
                            threshold = float(condition[1:])
                            mask = df[column] <= threshold
                        elif condition.startswith('<'):
                            threshold = float(condition[1:])
                            mask = df[column] >= threshold
                        elif condition.startswith('!='):
                            value = condition[2:].strip()
                            mask = df[column] == value
                        elif condition == 'not_null':
                            mask = df[column].isnull()
                        else:
                            validation_results.append({
                                'rule': rule,
                                'column': column,
                                'status': 'error',
                                'message': f'不支持的验证规则: {condition}',
                                'failed_rows': []
                            })
                            continue
                        
                        failed_indices = df[mask].index.tolist()
                        failed_count = len(failed_indices)
                        
                        validation_results.append({
                            'rule': rule,
                            'column': column,
                            'status': 'pass' if failed_count == 0 else 'fail',
                            'message': f'{failed_count} 行违反规则' if failed_count > 0 else '通过验证',
                            'failed_rows': failed_indices[:10]  # 只保留前10个失败行
                        })
                        
                        total_errors += failed_count
                        
                    except Exception as e:
                        validation_results.append({
                            'rule': rule,
                            'column': column,
                            'status': 'error',
                            'message': f'验证出错: {e}',
                            'failed_rows': []
                        })
            
            # 显示验证结果
            print("[bold cyan]验证结果[/bold cyan]")
            
            result_table = Table(show_header=True, header_style="bold magenta")
            result_table.add_column("规则", style="cyan")
            result_table.add_column("列名", style="blue")
            result_table.add_column("状态", style="green")
            result_table.add_column("消息", style="yellow")
            
            for result in validation_results:
                status_color = {
                    'pass': '[green]✓ 通过[/green]',
                    'fail': '[red]✗ 失败[/red]',
                    'error': '[red]✗ 错误[/red]'
                }.get(result['status'], result['status'])
                
                result_table.add_row(
                    result['rule'],
                    result['column'],
                    status_color,
                    result['message']
                )
            
            self.console.print(result_table)
            
            # 总结
            passed = sum(1 for r in validation_results if r['status'] == 'pass')
            failed = sum(1 for r in validation_results if r['status'] in ['fail', 'error'])
            
            print(f"\n[bold]验证总结[/bold]")
            print(f"通过: [green]{passed}[/green]")
            print(f"失败: [red]{failed}[/red]")
            print(f"错误行数: [red]{total_errors}[/red]")
            
            # 保存结果
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'file_path': file_path,
                        'validation_time': str(pd.Timestamp.now()),
                        'data_shape': df.shape,
                        'summary': {
                            'passed': passed,
                            'failed': failed,
                            'total_errors': total_errors
                        },
                        'results': validation_results
                    }, f, ensure_ascii=False, indent=2)
                
                print(f"[green]✓ 验证结果已保存到: {output_file}[/green]")
            
            return total_errors == 0
            
        except Exception as e:
            print(f"[red]验证失败: {e}[/red]")
            return False
    
    def sample(
        self,
        file_path: str,
        n: int = 100,
        method: str = "random",
        output_file: str = None,
        seed: int = None,
        **kwargs
    ):
        """数据采样

        Args:
            file_path: 数据文件路径（支持 .csv, .xlsx, .xls, .jsonl, .json）
            n: 采样数量
            method: 采样方法 (random, head, tail)
            output_file: 输出文件路径
            seed: 随机种子
            **kwargs: 其他参数

        Examples:
            maque data sample large_data.csv --n=1000
            maque data sample data.xlsx --method=head --n=50
            maque data sample train.jsonl --n=500 --seed=42
        """
        import pandas as pd
        import random

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            print(f"[red]文件不存在: {file_path}[/red]")
            return False

        try:
            # 读取数据
            file_ext = file_path_obj.suffix.lower()
            is_jsonl = file_ext == '.jsonl'

            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, **kwargs)
            elif file_ext == '.csv':
                df = pd.read_csv(file_path, **kwargs)
            elif file_ext == '.jsonl':
                data = jsonl_load(file_path)
                df = pd.DataFrame(data)
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    print(f"[red]JSON文件必须是数组格式[/red]")
                    return False
            else:
                print(f"[red]不支持的文件格式: {file_ext}[/red]")
                print("支持的格式: .csv, .xlsx, .xls, .jsonl, .json")
                return False

            print(f"[blue]数据采样: {file_path}[/blue]")
            print(f"原始数据: {df.shape[0]} 行 × {df.shape[1]} 列")

            # 采样
            if n >= len(df):
                print(f"[yellow]警告: 采样数量({n})大于等于数据行数({len(df)})，返回全部数据[/yellow]")
                sampled_df = df
            else:
                if method == "random":
                    if seed is not None:
                        sampled_df = df.sample(n=n, random_state=seed)
                    else:
                        sampled_df = df.sample(n=n)
                elif method == "head":
                    sampled_df = df.head(n)
                elif method == "tail":
                    sampled_df = df.tail(n)
                else:
                    print(f"[red]不支持的采样方法: {method}[/red]")
                    print("支持的方法: random, head, tail")
                    return False

            print(f"采样结果: {sampled_df.shape[0]} 行 × {sampled_df.shape[1]} 列")

            # 保存结果
            if not output_file:
                output_file = file_path_obj.stem + f"_sample_{n}" + file_path_obj.suffix

            output_path = Path(output_file)
            output_ext = output_path.suffix.lower()

            if output_ext in ['.xlsx', '.xls']:
                sampled_df.to_excel(output_file, index=False)
            elif output_ext == '.csv':
                sampled_df.to_csv(output_file, index=False)
            elif output_ext == '.jsonl':
                # 保存为 JSONL 格式
                with open(output_file, 'w', encoding='utf-8') as f:
                    for _, row in sampled_df.iterrows():
                        f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
            elif output_ext == '.json':
                # 保存为 JSON 格式
                sampled_df.to_json(output_file, orient='records', ensure_ascii=False, indent=2)
            else:
                # 默认保持原格式，如果无法识别则用 CSV
                if is_jsonl:
                    output_file = str(output_path.with_suffix('.jsonl'))
                    with open(output_file, 'w', encoding='utf-8') as f:
                        for _, row in sampled_df.iterrows():
                            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
                else:
                    output_file = str(output_path.with_suffix('.csv'))
                    sampled_df.to_csv(output_file, index=False)

            print(f"[green]✓ 采样结果已保存到: {output_file}[/green]")
            return True

        except Exception as e:
            print(f"[red]采样失败: {e}[/red]")
            return False
