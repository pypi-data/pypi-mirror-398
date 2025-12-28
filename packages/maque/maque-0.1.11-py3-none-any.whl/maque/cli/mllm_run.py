import pandas as pd
import asyncio
import os
import json
from datetime import datetime
from rich import print
from maque.utils.helper_parser import split_image_paths
from maque.utils.helper_metrics import calc_binary_metrics
from pathlib import Path
from typing import Optional, List, Dict, Any
from maque.mllm.mllm_client import MllmClient

qianfan_apikey = os.environ.get("qianfan_apikey", "sk-123")
if qianfan_apikey == "sk-123":
    # 警告
    print(
        "[yellow]未在环境变量中设置`qianfan_apikey`，现使用默认sk-123作为API key[/yellow]"
    )


class ConfigManager:
    """配置管理类，负责配置的保存、加载和管理"""

    CONFIG_FILE = "batch_processor_config.json"

    # 完整的可修改配置项列表
    MODIFIABLE_ITEMS = {
        1: {"name": "文件选择", "key": "file_path", "display": "文件"},
        2: {"name": "文本列", "key": "text_col", "display": "文本列"},
        3: {"name": "图像列", "key": "image_col", "display": "图像列"},
        4: {"name": "数据筛选", "key": "filter_config", "display": "筛选条件"},
        5: {"name": "模型选择", "key": "model_info", "display": "模型"},
        6: {"name": "提示模板", "key": "custom_prompt", "display": "Prompt"},
        7: {"name": "行数范围", "key": "rows_range", "display": "处理行数"},
        8: {"name": "预处理图像", "key": "preprocess_msg", "display": "预处理"},
        9: {"name": "并发数量", "key": "concurrency_limit", "display": "并发数"},
        10: {"name": "QPS限制", "key": "max_qps", "display": "QPS"},
        11: {"name": "结果解析", "key": "parse_config", "display": "解析设置"},
        12: {"name": "分类模式", "key": "use_cls", "display": "分类模式"},
        13: {"name": "系统提示", "key": "system_prompt", "display": "系统提示"},
    }

    def __init__(self):
        self.config_path = self.CONFIG_FILE

    def load_last_config(self) -> Optional[Dict[str, Any]]:
        """加载上次的配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("last_config")
        except Exception as e:
            print(f"[red]加载配置失败: {e}[/red]")
        return None

    def save_config(self, config: Dict[str, Any]):
        """保存配置"""
        try:
            # 加载现有配置
            existing_data = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

            # 更新配置
            config_to_save = config.copy()
            config_to_save["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            existing_data["last_config"] = config_to_save

            # 更新最近文件列表
            if "file_path" in config:
                recent_files = existing_data.get("recent_files", [])
                if config["file_path"] in recent_files:
                    recent_files.remove(config["file_path"])
                recent_files.insert(0, config["file_path"])
                existing_data["recent_files"] = recent_files[:10]  # 保留最近10个

            # 保存到文件
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[red]保存配置失败: {e}[/red]")

    def get_recent_files(self) -> List[str]:
        """获取最近使用的文件列表"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("recent_files", [])
        except Exception:
            pass
        return []

    def display_config_preview(self, config: Dict[str, Any]) -> str:
        """显示配置预览"""
        if not config:
            return "无历史配置"

        preview = []
        preview.append("上次配置预览:")
        preview.append("-" * 40)

        # 文件信息
        if "file_path" in config:
            preview.append(f"文件: {config['file_path']}")

        # 列信息
        text_col = config.get("text_col", "无")
        image_col = config.get("image_col", "无")
        preview.append(f"文本列: {text_col}  |  图像列: {image_col}")

        # 筛选信息
        filter_config = config.get("filter_config")
        if filter_config:
            filter_col, filter_values = filter_config
            preview.append(
                f"筛选: {filter_col} = {filter_values[:3]}{'...' if len(filter_values) > 3 else ''}"
            )
        else:
            preview.append("筛选: 无")

        # 模型信息
        model_info = config.get("model_info", {})
        model_name = model_info.get("name", model_info.get("model", "未知"))
        preview.append(f"模型: {model_name}")

        # Prompt信息
        custom_prompt = config.get("custom_prompt")
        preview.append(f"Prompt: {'自定义' if custom_prompt else '默认'}")

        # 行数信息
        rows_range = config.get("rows_range", (0, 0))
        start_row, end_row = rows_range
        if start_row == 0 and end_row == 0:
            preview.append("行数范围: 未知")
        elif start_row == 0:
            preview.append(f"行数范围: 前{end_row}行")
        else:
            preview.append(f"行数范围: 第{start_row + 1}-{end_row}行")

        # 处理参数
        preprocess = "是" if config.get("preprocess_msg", False) else "否"
        concurrency = config.get("concurrency_limit", 100)
        qps = config.get("max_qps", 25)
        use_cls = "是" if config.get("use_cls", False) else "否"
        system_prompt = "是" if config.get("system_prompt") else "否"
        preview.append(f"预处理: {preprocess}  |  并发: {concurrency}  |  QPS: {qps}")
        preview.append(f"分类模式: {use_cls}  |  系统提示: {system_prompt}")

        # 时间信息
        if "timestamp" in config:
            preview.append(f"最后使用: {config['timestamp']}")

        return "\n".join(preview)

    def get_config_differences(self, config: Dict[str, Any]) -> List[str]:
        """获取与默认配置的差异（这里简化处理）"""
        # 这个方法可以用来检测配置项的变化，目前简化返回所有可修改项
        return list(range(1, len(self.MODIFIABLE_ITEMS) + 1))


class BatchProcessor:
    def __init__(
        self,
        model: str = "vkk8o2py_wenxiaoyan_mllm_bj",
        base_url: str = None,
        concurrency_limit: int = 100,
        max_qps: int = 25,
    ):
        self.model = model
        self.base_url = base_url or "https://qianfan.baidubce.com/v2"
        self.client = MllmClient(
            base_url=self.base_url,
            api_key=qianfan_apikey,
            model=model,
            concurrency_limit=concurrency_limit,
            max_qps=max_qps,
        )

    def set_model(self, model: str, base_url: str = None):
        """切换模型和base_url"""
        self.model = model
        if base_url:
            self.base_url = base_url
            # 重新创建client
            self.client = MllmClient(
                base_url=self.base_url,
                api_key=os.environ.get("qianfan_apikey", "sk-123"),
                model=model,
                concurrency_limit=self.client.concurrency_limit,
                max_qps=self.client.max_qps,
            )
        else:
            self.client.model = model

    def set_custom_prompt(self, prompt_template: str):
        """设置自定义提示模板"""
        self.custom_prompt = prompt_template

    def create_messages_for_row(
        self,
        row_data: Dict[str, Any],
        text_col: Optional[str],
        image_col: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        use_cls: bool = False,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """为单行数据创建messages格式"""
        # 处理文本内容，如果没有文本列则使用"无"
        if text_col is None:
            text_content = "无"
        else:
            text_content = str(row_data.get(text_col, ""))

        # 使用自定义提示模板或默认模板
        if custom_prompt:
            text_prompt = custom_prompt.format(text_content=text_content)
        elif hasattr(self, "custom_prompt"):
            text_prompt = self.custom_prompt.format(text_content=text_content)
        else:
            # 根据模型选择不同的提示模板
            if "xiaoyan" in self.model:
                if use_cls:
                    text_prompt = f"用户query文本: {text_content}\n\n 请判断以上图文内容的分类标签是?"
                else:
                    text_prompt = (
                        f"用户query文本: {text_content}\n\n 请审核以上图文内容。"
                    )
            else:
                if use_cls:
                    text_prompt = (
                        f"文本: {text_content}\n\n 请判断以上图文内容的风险类型是什么"
                    )
                else:
                    text_prompt = f"文本: {text_content}\n\n 请审核以上图文内容。"

        content = [{"type": "text", "text": text_prompt}]

        if image_col is not None:
            assert image_col in row_data, (
                f"{image_col} not found in row_data: {row_data}"
            )

        # 处理图像列
        if image_col and row_data.get(image_col):
            path_str = str(row_data[image_col])
            if path_str and not pd.isna(path_str):
                path_list = split_image_paths(path_str)
                for path in path_list:
                    if path.strip():
                        content.append(
                            {"type": "image_url", "image_url": {"url": path}}
                        )

        messages = []

        # 添加系统提示（如果提供）
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": content})

        return messages

    async def process_table(
        self,
        table_path: str,
        text_col: Optional[str],
        image_col: Optional[str] = None,
        sheet_name: Optional[str] = None,
        preprocess_msg: bool = False,
        custom_prompt: Optional[str] = None,
    ) -> pd.DataFrame:
        """批量处理表格数据"""
        df = self._load_dataframe(table_path, sheet_name)
        messages_list = self._create_messages_list(
            df, text_col, image_col, custom_prompt
        )
        results = await self._call_llm_batch(messages_list, preprocess_msg)
        df = self._add_results_to_dataframe(df, results)
        output_path = self._save_results(df, table_path)

        print(f"结果已保存到: {output_path}")
        return df

    def _load_dataframe(
        self, table_path: str, sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """加载数据表格"""
        if sheet_name is not None:
            return pd.read_excel(table_path, sheet_name=sheet_name)
        else:
            return (
                pd.read_excel(table_path)
                if table_path.endswith(".xlsx")
                else pd.read_csv(table_path)
            )

    def _create_messages_list(
        self,
        df: pd.DataFrame,
        text_col: Optional[str],
        image_col: Optional[str],
        custom_prompt: Optional[str] = None,
        use_cls: bool = False,
        system_prompt: Optional[str] = None,
    ) -> List[List[Dict[str, Any]]]:
        """为每行创建messages"""
        messages_list = []
        for _, row in df.iterrows():
            messages = self.create_messages_for_row(
                row.to_dict(),
                text_col,
                image_col,
                custom_prompt,
                use_cls,
                system_prompt,
            )
            messages_list.append(messages)
        return messages_list

    async def _call_llm_batch(
        self, messages_list: List[List[Dict[str, Any]]], preprocess_msg: bool
    ) -> List[str]:
        """批量调用LLM"""
        return await self.client.call_llm(
            messages_list=messages_list,
            preprocess_msg=preprocess_msg,
            safety={"input_level": "none", "input_image_level": "none"},
        )

    def _add_results_to_dataframe(
        self, df: pd.DataFrame, results: List[str]
    ) -> pd.DataFrame:
        """将结果添加到DataFrame"""
        if "response" in df.columns:
            df.rename(columns={"response": "response_original"}, inplace=True)
        df["response"] = results
        return df

    def _save_results(self, df: pd.DataFrame, table_path: str) -> str:
        """保存结果"""
        output_path = Path(table_path).stem + "_result.xlsx"
        df.to_excel(output_path, index=False, engine="openpyxl")
        return output_path

    def calculate_metrics(
        self,
        df: pd.DataFrame,
        response_col: str = "response",
        label_col: Optional[str] = None,
        parse_response_to_pred: bool = True,
        pred_parsed_tag: str = "一级标签",
        record_root_dir: str = "record",
    ):
        """计算评估指标"""
        calc_binary_metrics(
            df,
            response_col=response_col,
            label_col=label_col,
            parse_response_to_pred=parse_response_to_pred,
            pred_parsed_tag=pred_parsed_tag,
            record_root_dir=record_root_dir,
        )


async def example_usage():
    """使用示例"""
    processor = BatchProcessor()

    # 配置处理参数
    table_path = "多模态输入流-剩余未标注数据.xlsx"
    text_col = "feed_content"
    image_col = "image_src"
    sheet_name = None
    preprocess_msg = False

    # 处理表格
    result_df = await processor.process_table(
        table_path=table_path,
        text_col=text_col,
        image_col=image_col,
        sheet_name=sheet_name,
        preprocess_msg=preprocess_msg,
    )

    print(f"处理完成，共处理 {len(result_df)} 行数据")

    # 计算指标
    processor.calculate_metrics(result_df)


class InteractiveRunner:
    def __init__(self):
        self.processor = None
        self.models_config = self.load_models_config()
        self.config_manager = ConfigManager()
        self.current_config = {}  # 存储当前会话的配置

    def load_models_config(self) -> dict:
        """加载模型配置，优先加载当前目录的配置"""
        # 当前目录的配置文件
        current_config_path = "models_config.json"
        # 默认配置文件路径
        default_config_path = Path(__file__).parent / "models_config.json"

        config_path = (
            current_config_path
            if os.path.exists(current_config_path)
            else default_config_path
        )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: 找不到配置文件 {config_path}，使用内置默认配置")
            return {
                "models": [
                    {
                        "name": "文小言 (wenxiaoyan)",
                        "model": "vkk8o2py_wenxiaoyan_mllm_bj",
                        "base_url": "https://qianfan.baidubce.com/v2",
                        "description": "百度文小言多模态大模型",
                        "parse_response_to_pred": True,
                        "pred_parsed_tag": "一级标签",
                    }
                ]
            }
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误 {e}，使用内置默认配置")
            return self.load_models_config()  # 递归调用使用默认配置

    def scan_files(self) -> List[str]:
        """扫描当前目录下的表格文件"""
        files = []
        for file in os.listdir("."):
            if file.endswith((".xlsx", ".csv")):
                files.append(file)
        return files

    def select_file(self) -> str:
        """选择文件"""
        files = self.scan_files()
        if not files:
            print("当前目录下没有找到.xlsx或.csv文件")
            return None

        print("\n请选择要处理的文件:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")

        while True:
            try:
                choice = int(input("请输入文件编号: "))
                if 1 <= choice <= len(files):
                    return files[choice - 1]
                else:
                    print(f"请输入1-{len(files)}之间的数字")
            except ValueError:
                print("请输入有效数字")

    def select_columns(self, df: pd.DataFrame) -> tuple:
        """选择文本列和图像列"""
        columns = list(df.columns)
        print("\n表格列信息:")
        for i, col in enumerate(columns, 1):
            sample_data = str(df[col].iloc[0])[:50] if len(df) > 0 else "无数据"
            print(f"{i}. {col} (示例: {sample_data})")

        # 选择文本列 (支持无文本列)
        print("\n请选择文本列 (输入0表示无文本列):")
        for i, col in enumerate(columns, 1):
            print(f"{i}. {col}")
        print("0. 无文本列")

        while True:
            try:
                choice = int(input("请选择文本列编号: "))
                if choice == 0:
                    text_col = None
                    break
                elif 1 <= choice <= len(columns):
                    text_col = columns[choice - 1]
                    break
                else:
                    print(f"请输入0-{len(columns)}之间的数字")
            except ValueError:
                print("请输入有效数字")

        # 选择图像列
        print("\n请选择图像列 (输入0表示无图像列):")
        for i, col in enumerate(columns, 1):
            print(f"{i}. {col}")
        print("0. 无图像列")

        while True:
            try:
                choice = int(input("请选择图像列编号: "))
                if choice == 0:
                    image_col = None
                    break
                elif 1 <= choice <= len(columns):
                    image_col = columns[choice - 1]
                    break
                else:
                    print(f"请输入0-{len(columns)}之间的数字")
            except ValueError:
                print("请输入有效数字")

        return text_col, image_col

    def select_filter_column(self, df: pd.DataFrame) -> Optional[tuple]:
        """选择筛选列及筛选值"""
        columns = list(df.columns)
        print("\n数据筛选 (可选):")
        print("0. 不筛选数据")
        for i, col in enumerate(columns, 1):
            print(f"{i}. 筛选列 '{col}'")

        while True:
            try:
                choice = int(input("请选择是否筛选数据: "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(columns):
                    filter_col = columns[choice - 1]
                    break
                else:
                    print(f"请输入0-{len(columns)}之间的数字")
            except ValueError:
                print("请输入有效数字")

        # 统计该列的值分布
        value_counts = df[filter_col].value_counts().head(50)  # 最多显示50个
        print(f"\n列 '{filter_col}' 的值分布:")
        print("-" * 40)
        for i, (value, count) in enumerate(value_counts.items(), 1):
            print(f"{i:2d}. {value} (出现{count}次)")

        # 选择筛选值
        print("\n筛选方式:")
        print("1. 正选 - 保留选中的值")
        print("2. 反选 - 排除选中的值，保留其他值")

        # 选择筛选方式
        while True:
            try:
                filter_mode = int(input("请选择筛选方式 (1/2): "))
                if filter_mode in [1, 2]:
                    break
                else:
                    print("请输入1或2")
            except ValueError:
                print("请输入有效数字")

        mode_text = "保留" if filter_mode == 1 else "排除"
        print(f"\n请选择要{mode_text}的值 (可多选，用逗号分隔编号，如: 1,3,5):")

        while True:
            try:
                choices_input = input("筛选值编号: ").strip()
                if not choices_input:
                    print("请输入至少一个编号")
                    continue

                choices = [int(x.strip()) for x in choices_input.split(",")]
                selected_indices = []

                for choice in choices:
                    if 1 <= choice <= len(value_counts):
                        selected_indices.append(choice - 1)
                    else:
                        print(f"编号 {choice} 超出范围，请重新输入")
                        break
                else:
                    # 所有选择都有效
                    if filter_mode == 1:
                        # 正选：保留选中的值
                        selected_values = [
                            value_counts.index[i] for i in selected_indices
                        ]
                        print(f"已选择保留值: {selected_values}")
                    else:
                        # 反选：保留未选中的值
                        all_indices = set(range(len(value_counts)))
                        remaining_indices = all_indices - set(selected_indices)
                        selected_values = [
                            value_counts.index[i] for i in remaining_indices
                        ]
                        excluded_values = [
                            value_counts.index[i] for i in selected_indices
                        ]
                        print(f"已排除值: {excluded_values}")
                        print(f"将保留值: {selected_values}")

                    return filter_col, selected_values

            except ValueError:
                print("请输入有效的数字编号")

    def apply_filter(
        self, df: pd.DataFrame, filter_config: Optional[tuple]
    ) -> pd.DataFrame:
        """应用数据筛选"""
        if filter_config is None:
            return df

        filter_col, selected_values = filter_config
        filtered_df = df[df[filter_col].isin(selected_values)].copy()
        print(f"筛选后数据: {len(filtered_df)} 行 (原始: {len(df)} 行)")
        return filtered_df

    def select_model(self) -> tuple:
        """选择模型和base_url"""
        models = self.models_config.get("models", [])

        print("\n请选择模型:")
        for i, model_info in enumerate(models, 1):
            print(f"{i}. {model_info['name']} - {model_info['description']}")

        while True:
            try:
                choice = int(input("请选择模型编号: "))
                if 1 <= choice <= len(models):
                    selected = models[choice - 1]

                    if selected["model"] == "custom":
                        # 自定义模型
                        base_url = input("请输入base_url: ")
                        model = input("请输入model名称: ")
                        # 自定义模型返回基本信息，解析配置后续处理
                        return {
                            "model": model,
                            "base_url": base_url,
                            "name": "自定义模型",
                            "description": "用户自定义",
                            "parse_response_to_pred": False,
                            "pred_parsed_tag": None,
                        }
                    else:
                        return selected
                else:
                    print(f"请输入1-{len(models)}之间的数字")
            except ValueError:
                print("请输入有效数字")

    def select_prompt(self) -> Optional[str]:
        """选择提示模板"""
        print("\n请选择提示模板:")
        print("1. 使用默认提示模板")
        print("2. 自定义提示模板")

        while True:
            try:
                choice = int(input("请选择: "))
                if choice == 1:
                    return None
                elif choice == 2:
                    print("\n请输入自定义提示模板 (使用{text_content}作为文本占位符):")
                    return input("提示模板: ")
                else:
                    print("请输入1或2")
            except ValueError:
                print("请输入有效数字")

    def select_rows(self, df: pd.DataFrame) -> tuple:
        """选择要处理的行数范围"""
        total_rows = len(df)
        print(f"\n行数选择 (总共 {total_rows} 行):")
        print("1. 处理所有行")
        print("2. 指定行数 (从第1行开始)")
        print("3. 指定行数范围 (从第n行到第m行)")

        while True:
            try:
                choice = int(input("请选择: "))
                if choice == 1:
                    return 0, total_rows
                elif choice == 2:
                    while True:
                        try:
                            count = int(input(f"请输入要处理的行数 (1-{total_rows}): "))
                            if 1 <= count <= total_rows:
                                return 0, count
                            print(f"行数必须在1-{total_rows}之间")
                        except ValueError:
                            print("请输入有效数字")
                elif choice == 3:
                    while True:
                        try:
                            start = (
                                int(input(f"起始行号 (1-{total_rows}): ")) - 1
                            )  # 转为0基索引
                            end = int(
                                input(f"结束行号 ({start + 2}-{total_rows}): ")
                            )  # 显示基于1的索引
                            if 0 <= start < end <= total_rows:
                                return start, end
                            print("请确保起始行号小于结束行号，且在有效范围内")
                        except ValueError:
                            print("请输入有效数字")
                else:
                    print("请输入1、2或3")
            except ValueError:
                print("请输入有效数字")

    def select_config(self) -> dict:
        """选择处理配置"""
        print("\n配置选项:")

        # 预处理选择
        while True:
            preprocess = input("是否预处理图像? (y/n): ").lower()
            if preprocess in ["y", "yes", "n", "no"]:
                preprocess_msg = preprocess in ["y", "yes"]
                break
            print("请输入y或n")

        # 并发数设置
        while True:
            try:
                concurrency = int(input("并发数量 (默认100): ") or "100")
                if concurrency > 0:
                    break
                print("并发数必须大于0")
            except ValueError:
                print("请输入有效数字")

        # QPS设置
        while True:
            try:
                qps = int(input("最大QPS (默认25): ") or "25")
                if qps > 0:
                    break
                print("QPS必须大于0")
            except ValueError:
                print("请输入有效数字")

        # 分类模式选择
        while True:
            use_cls_input = input("是否使用分类模式? (y/n, 默认n): ").lower() or "n"
            if use_cls_input in ["y", "yes", "n", "no"]:
                use_cls = use_cls_input in ["y", "yes"]
                break
            print("请输入y或n")

        # 系统提示选择
        system_prompt = None
        while True:
            system_input = input("是否添加系统提示? (y/n, 默认n): ").lower() or "n"
            if system_input in ["y", "yes"]:
                system_prompt = input("请输入系统提示内容: ").strip()
                if not system_prompt:
                    print("系统提示不能为空")
                    continue
                break
            elif system_input in ["n", "no"]:
                break
            else:
                print("请输入y或n")

        return {
            "preprocess_msg": preprocess_msg,
            "concurrency_limit": concurrency,
            "max_qps": qps,
            "use_cls": use_cls,
            "system_prompt": system_prompt,
        }

    def select_metrics_config(
        self, df: pd.DataFrame, model_config: dict
    ) -> Optional[dict]:
        """选择指标计算配置"""
        while True:
            analyze = input("\n是否需要分析结果? (y/n): ").lower()
            if analyze in ["y", "yes"]:
                # 选择标签列
                columns = list(df.columns)
                print("\n选择标签列 (输入0表示无标签列):")
                for i, col in enumerate(columns, 1):
                    print(f"{i}. {col}")
                print("0. 无标签列")

                while True:
                    try:
                        choice = int(input("请选择标签列编号: "))
                        if choice == 0:
                            label_col = None
                            break
                        elif 1 <= choice <= len(columns):
                            label_col = columns[choice - 1]
                            break
                        else:
                            print(f"请输入0-{len(columns)}之间的数字")
                    except ValueError:
                        print("请输入有效数字")

                # 获取模型的默认解析配置
                default_parse = model_config.get("parse_response_to_pred", False)
                default_tag = model_config.get("pred_parsed_tag", None)

                # 选择是否解析响应
                print(f"\n解析响应设置 (模型默认: {default_parse}):")
                print("1. 使用模型默认配置")
                print("2. 自定义配置")

                while True:
                    try:
                        parse_choice = int(input("请选择: "))
                        if parse_choice == 1:
                            parse_response_to_pred = default_parse
                            pred_parsed_tag = default_tag
                            break
                        elif parse_choice == 2:
                            # 自定义解析配置
                            while True:
                                parse_input = input(
                                    "是否解析响应为预测结果? (y/n): "
                                ).lower()
                                if parse_input in ["y", "yes"]:
                                    parse_response_to_pred = True
                                    pred_parsed_tag = input(
                                        "请输入解析标签 (pred_parsed_tag): "
                                    )
                                    break
                                elif parse_input in ["n", "no"]:
                                    parse_response_to_pred = False
                                    pred_parsed_tag = None
                                    break
                                else:
                                    print("请输入y或n")
                            break
                        else:
                            print("请输入1或2")
                    except ValueError:
                        print("请输入有效数字")

                return {
                    "label_col": label_col,
                    "parse_response_to_pred": parse_response_to_pred,
                    "pred_parsed_tag": pred_parsed_tag,
                }
            elif analyze in ["n", "no"]:
                return None
            print("请输入y或n")

    def select_config_mode(self) -> str:
        """选择配置模式"""
        last_config = self.config_manager.load_last_config()

        print("=== 批量处理工具 ===")

        if last_config:
            print("\n检测到历史配置！")
            print("1. 快速开始 (使用上次配置)")
            print("2. 修改配置 (基于上次配置修改)")
            print("3. 从头配置")

            while True:
                try:
                    choice = int(input("\n请选择模式 (1/2/3): "))
                    if choice == 1:
                        self.current_config = last_config.copy()
                        return "quick_start"
                    elif choice == 2:
                        self.current_config = last_config.copy()
                        return "modify_config"
                    elif choice == 3:
                        return "fresh_start"
                    else:
                        print("请输入1、2或3")
                except ValueError:
                    print("请输入有效数字")
        else:
            print("\n首次使用，开始配置...")
            return "fresh_start"

    def select_modifications(self) -> List[int]:
        """选择需要修改的配置项"""
        print("\n" + self.config_manager.display_config_preview(self.current_config))

        print(f"\n请选择要修改的项目 (可多选，用逗号分隔编号):")
        for item_id, item_info in self.config_manager.MODIFIABLE_ITEMS.items():
            print(f"{item_id:2d}. {item_info['display']}")
        print(" 0. 不修改，直接使用上述配置")

        while True:
            try:
                choices_input = input("\n修改项编号: ").strip()
                if choices_input == "0" or not choices_input:
                    return []

                choices = [int(x.strip()) for x in choices_input.split(",")]
                valid_choices = []

                for choice in choices:
                    if 1 <= choice <= len(self.config_manager.MODIFIABLE_ITEMS):
                        valid_choices.append(choice)
                    else:
                        print(f"编号 {choice} 超出范围，请重新输入")
                        break
                else:
                    return valid_choices

            except ValueError:
                print("请输入有效的数字编号")

    async def run(self):
        """运行交互式处理流程"""
        # 1. 选择配置模式
        config_mode = self.select_config_mode()

        if config_mode == "quick_start":
            # 快速开始模式：直接使用历史配置
            await self.run_with_config()
            return
        elif config_mode == "modify_config":
            # 修改配置模式：选择性修改
            modifications = self.select_modifications()
            if not modifications:
                await self.run_with_config()
                return
            await self.run_with_selective_config(modifications)
            return
        else:
            # 从头配置模式：完整流程
            await self.run_full_config()

    async def run_full_config(self):
        """完整配置流程"""
        print("\n=== 完整配置模式 ===")

        # 1. 选择文件
        file_path = self.select_file()
        if not file_path:
            return
        self.current_config["file_path"] = file_path

        # 继续完整流程配置
        await self._complete_config_flow(file_path)

    async def _complete_config_flow(self, file_path: str):
        """完成配置流程并执行处理"""
        # 2. 加载并选择列
        df_preview = (
            pd.read_excel(file_path)
            if file_path.endswith(".xlsx")
            else pd.read_csv(file_path)
        )
        text_col, image_col = self.select_columns(df_preview)

        # 检查是否至少有一列被选择
        if text_col is None and image_col is None:
            print("错误：必须至少选择一个文本列或图像列")
            return

        # 更新配置
        self.current_config.update({"text_col": text_col, "image_col": image_col})

        # 3. 数据筛选
        filter_config = self.select_filter_column(df_preview)
        df_filtered = self.apply_filter(df_preview, filter_config)
        self.current_config["filter_config"] = filter_config

        # 4. 选择模型
        model_info = self.select_model()
        self.current_config["model_info"] = model_info

        # 5. 选择提示模板
        custom_prompt = self.select_prompt()
        self.current_config["custom_prompt"] = custom_prompt

        # 6. 选择行数范围
        start_row, end_row = self.select_rows(df_filtered)
        df_to_process = df_filtered.iloc[start_row:end_row].copy()
        self.current_config["rows_range"] = (start_row, end_row)

        # 7. 配置参数
        config = self.select_config()
        self.current_config.update(
            {
                "preprocess_msg": config["preprocess_msg"],
                "concurrency_limit": config["concurrency_limit"],
                "max_qps": config["max_qps"],
                "use_cls": config["use_cls"],
                "system_prompt": config["system_prompt"],
            }
        )

        # 保存配置
        self.config_manager.save_config(self.current_config)

        # 执行处理
        model_name = model_info["model"]
        base_url = model_info["base_url"]
        await self._execute_processing(
            df_to_process,
            model_name,
            base_url,
            model_info,
            custom_prompt,
            config,
            start_row,
            end_row,
        )

    async def run_with_config(self):
        """使用现有配置运行"""
        print("\n=== 快速开始模式 ===")
        print("使用历史配置直接处理...")

        # 验证配置文件是否存在
        file_path = self.current_config.get("file_path")
        if not file_path or not os.path.exists(file_path):
            print(f"错误：配置中的文件 {file_path} 不存在")
            # 重新选择文件
            file_path = self.select_file()
            if not file_path:
                return
            self.current_config["file_path"] = file_path

        # 从配置中恢复数据并执行
        await self._execute_from_config()

    async def run_with_selective_config(self, modifications: List[int]):
        """选择性修改配置并运行"""
        print("\n=== 修改配置模式 ===")
        print(
            f"需要修改的配置项: {[self.config_manager.MODIFIABLE_ITEMS[i]['display'] for i in modifications]}"
        )

        file_path = self.current_config.get("file_path")

        # 按顺序处理需要修改的配置项
        for item_id in modifications:
            item_info = self.config_manager.MODIFIABLE_ITEMS[item_id]
            print(f"\n正在修改: {item_info['display']}")

            if item_id == 1:  # 文件选择
                file_path = self.select_file()
                if not file_path:
                    return
                self.current_config["file_path"] = file_path

            elif item_id in [2, 3]:  # 文本列或图像列
                if not file_path or not os.path.exists(file_path):
                    print("错误：需要先选择有效的文件")
                    continue
                df_preview = (
                    pd.read_excel(file_path)
                    if file_path.endswith(".xlsx")
                    else pd.read_csv(file_path)
                )
                text_col, image_col = self.select_columns(df_preview)
                self.current_config.update(
                    {"text_col": text_col, "image_col": image_col}
                )

            elif item_id == 4:  # 数据筛选
                if not file_path:
                    print("错误：需要先选择文件")
                    continue
                df_preview = (
                    pd.read_excel(file_path)
                    if file_path.endswith(".xlsx")
                    else pd.read_csv(file_path)
                )
                filter_config = self.select_filter_column(df_preview)
                self.current_config["filter_config"] = filter_config

            elif item_id == 5:  # 模型选择
                model_info = self.select_model()
                self.current_config["model_info"] = model_info

            elif item_id == 6:  # 提示模板
                custom_prompt = self.select_prompt()
                self.current_config["custom_prompt"] = custom_prompt

            elif item_id == 7:  # 行数范围
                if not file_path:
                    print("错误：需要先选择文件")
                    continue
                df_preview = (
                    pd.read_excel(file_path)
                    if file_path.endswith(".xlsx")
                    else pd.read_csv(file_path)
                )
                # 应用筛选
                filter_config = self.current_config.get("filter_config")
                df_filtered = self.apply_filter(df_preview, filter_config)
                start_row, end_row = self.select_rows(df_filtered)
                self.current_config["rows_range"] = (start_row, end_row)

            elif item_id in [8, 9, 10, 12, 13]:  # 预处理、并发、QPS、分类模式、系统提示
                config = self.select_config()
                self.current_config.update(
                    {
                        "preprocess_msg": config["preprocess_msg"],
                        "concurrency_limit": config["concurrency_limit"],
                        "max_qps": config["max_qps"],
                        "use_cls": config["use_cls"],
                        "system_prompt": config["system_prompt"],
                    }
                )

        # 保存更新后的配置
        self.config_manager.save_config(self.current_config)

        # 执行处理
        await self._execute_from_config()

    async def _execute_from_config(self):
        """从配置中执行处理"""
        file_path = self.current_config["file_path"]

        # 加载数据
        df_preview = (
            pd.read_excel(file_path)
            if file_path.endswith(".xlsx")
            else pd.read_csv(file_path)
        )

        # 应用筛选
        filter_config = self.current_config.get("filter_config")
        df_filtered = self.apply_filter(df_preview, filter_config)

        # 获取行数范围
        rows_range = self.current_config.get("rows_range", (0, len(df_filtered)))
        start_row, end_row = rows_range
        df_to_process = df_filtered.iloc[start_row:end_row].copy()

        # 获取模型信息
        model_info = self.current_config["model_info"]
        model_name = model_info["model"]
        base_url = model_info["base_url"]

        # 获取其他配置
        custom_prompt = self.current_config.get("custom_prompt")
        config = {
            "preprocess_msg": self.current_config.get("preprocess_msg", False),
            "concurrency_limit": self.current_config.get("concurrency_limit", 100),
            "max_qps": self.current_config.get("max_qps", 25),
            "use_cls": self.current_config.get("use_cls", False),
            "system_prompt": self.current_config.get("system_prompt"),
        }

        # 执行处理
        await self._execute_processing(
            df_to_process,
            model_name,
            base_url,
            model_info,
            custom_prompt,
            config,
            start_row,
            end_row,
        )

    async def _execute_processing(
        self,
        df_to_process,
        model_name,
        base_url,
        model_info,
        custom_prompt,
        config,
        start_row,
        end_row,
    ):
        """执行实际的处理逻辑"""
        text_col = self.current_config.get("text_col")
        image_col = self.current_config.get("image_col")
        file_path = self.current_config["file_path"]

        # 8. 创建处理器
        self.processor = BatchProcessor(
            model=model_name,
            base_url=base_url,
            concurrency_limit=config["concurrency_limit"],
            max_qps=config["max_qps"],
        )

        # 显示请求预览
        self._show_request_preview(
            df_to_process,
            text_col,
            image_col,
            custom_prompt,
            config,
            start_row,
            end_row,
            model_name,
            base_url,
        )

        print("\n开始调用模型...")
        print(f"模型信息: {model_name}")
        print(f"API地址: {base_url}")
        print("正在处理...")

        result_df = await self._process_selected_rows(
            file_path,
            df_to_process,
            text_col,
            image_col,
            config["preprocess_msg"],
            custom_prompt,
            start_row,
        )

        print(f"\n处理完成，共处理 {len(result_df)} 行数据")

        # 9. 选择是否分析结果
        metrics_config = self.select_metrics_config(result_df, model_info)
        if metrics_config:
            print("\n开始分析结果...")
            self.processor.calculate_metrics(
                result_df,
                label_col=metrics_config["label_col"],
                parse_response_to_pred=metrics_config["parse_response_to_pred"],
                pred_parsed_tag=metrics_config["pred_parsed_tag"],
            )
            print("分析完成!")

    async def _process_selected_rows(
        self,
        file_path: str,
        df_to_process: pd.DataFrame,
        text_col: Optional[str],
        image_col: Optional[str],
        preprocess_msg: bool,
        custom_prompt: Optional[str],
        start_row: int,
    ) -> pd.DataFrame:
        """处理选定的行"""
        # 从全局配置获取新参数
        use_cls = self.current_config.get("use_cls", False)
        system_prompt = self.current_config.get("system_prompt")

        # 生成消息列表
        messages_list = self.processor._create_messages_list(
            df_to_process, text_col, image_col, custom_prompt, use_cls, system_prompt
        )

        # 批量调用API
        results = await self.processor._call_llm_batch(messages_list, preprocess_msg)

        # 将结果添加到DataFrame
        df_result = df_to_process.copy()
        if "response" in df_result.columns:
            df_result.rename(columns={"response": "response_original"}, inplace=True)
        df_result["response"] = results

        # 保存结果 - 使用带行号范围的文件名
        file_stem = Path(file_path).stem
        if start_row == 0 and len(df_to_process) < len(
            pd.read_excel(file_path)
            if file_path.endswith(".xlsx")
            else pd.read_csv(file_path)
        ):
            # 从第一行开始但不是全部
            output_path = f"{file_stem}_result_rows1-{len(df_to_process)}.xlsx"
        elif start_row > 0:
            # 指定范围
            output_path = f"{file_stem}_result_rows{start_row + 1}-{start_row + len(df_to_process)}.xlsx"
        else:
            # 全部行
            output_path = f"{file_stem}_result.xlsx"

        df_result.to_excel(output_path, index=False, engine="openpyxl")
        print(f"结果已保存到: {output_path}")

        return df_result

    def _show_request_preview(
        self,
        df: pd.DataFrame,
        text_col: Optional[str],
        image_col: Optional[str],
        custom_prompt: Optional[str],
        config: dict,
        start_row: int,
        end_row: int,
        model_name: str,
        base_url: str,
    ):
        """显示请求预览信息"""
        print("\n" + "=" * 50)
        print("请求预览信息")
        print("=" * 50)

        # 基本信息
        print(f"模型: {model_name}")
        print(f"Base URL: {base_url}")
        print(f"处理范围: 第{start_row + 1}行到第{end_row}行 (共{len(df)}行)")
        print(f"文本列: {text_col if text_col else '无'}")
        print(f"图像列: {image_col if image_col else '无'}")
        print(f"预处理图像: {'是' if config['preprocess_msg'] else '否'}")
        print(f"并发数: {config['concurrency_limit']}")
        print(f"QPS限制: {config['max_qps']}")
        print(f"分类模式: {'是' if config.get('use_cls', False) else '否'}")
        if config.get("system_prompt"):
            print(
                f"系统提示: {config['system_prompt'][:50]}{'...' if len(config['system_prompt']) > 50 else ''}"
            )

        # 创建临时处理器生成示例消息
        temp_processor = BatchProcessor(model=model_name, base_url=base_url)
        if custom_prompt:
            temp_processor.set_custom_prompt(custom_prompt)

        # 获取第一行数据作为示例
        if len(df) > 0:
            first_row = df.iloc[0].to_dict()
            sample_messages = temp_processor.create_messages_for_row(
                row_data=first_row,
                text_col=text_col,
                image_col=image_col,
                custom_prompt=custom_prompt,
                use_cls=config.get("use_cls", False),
                system_prompt=config.get("system_prompt"),
            )

            print(f"\n第{start_row + 1}行请求示例 (原始messages格式):")
            print("-" * 50)
            import json

            print(json.dumps(sample_messages, indent=2, ensure_ascii=False))
            print("-" * 50)

        # 确认继续
        while True:
            confirm = input(f"\n确认开始处理 {len(df)} 行数据? (y/n): ").lower()
            if confirm in ["y", "yes"]:
                break
            elif confirm in ["n", "no"]:
                print("已取消处理")
                exit(0)
            else:
                print("请输入y或n")


def parse_existing_results(file_path: str):
    """解析已存在的结果文件"""
    print("=== 结果文件解析工具 ===")
    print(f"文件路径: {file_path}")

    # 加载数据
    try:
        df = pd.read_excel(file_path)
        print(f"成功加载数据，共 {len(df)} 行")
    except Exception as e:
        print(f"错误：无法加载文件 {file_path}: {e}")
        return

    # 创建临时的InteractiveRunner来使用配置选择功能
    runner = InteractiveRunner()

    # 选择解析配置 - 使用通用的默认配置
    default_config = {"parse_response_to_pred": False, "pred_parsed_tag": None}

    metrics_config = runner.select_metrics_config(df, default_config)
    if metrics_config is None:
        print("已取消解析")
        return

    # 执行解析
    processor = BatchProcessor()
    print("\n开始解析结果...")
    processor.calculate_metrics(
        df,
        label_col=metrics_config["label_col"],
        parse_response_to_pred=metrics_config["parse_response_to_pred"],
        pred_parsed_tag=metrics_config["pred_parsed_tag"],
    )
    print("解析完成!")


def choose_interface():
    """选择界面模式"""
    print("🤖 MLLM Judge - 多模态内容审核系统")
    print("=" * 50)
    print("选择界面模式:")
    print("1. 📱 图形界面 (GUI) - 推荐")
    print("2. 💻 命令行界面 (CLI)")
    print("3. ❌ 退出")

    while True:
        try:
            choice = input("\n请选择 (1-3): ").strip()
            if choice == "1":
                return "gui"
            elif choice == "2":
                return "cli"
            elif choice == "3":
                return "exit"
            else:
                print("请输入有效选择 (1-3)")
        except KeyboardInterrupt:
            print("\n👋 已退出")
            return "exit"


async def run_cli():
    """运行CLI模式"""
    runner = InteractiveRunner()
    await runner.run()


def run_gui():
    """运行GUI模式"""
    try:
        from run_gui import MLLMJudgeApp

        app = MLLMJudgeApp()
        app.run()
    except ImportError:
        print("❌ GUI模式需要安装Textual库:")
        print("   pip install textual textual-dev")
        print("\n🔄 正在启动CLI模式...")
        return False
    except Exception as e:
        print(f"❌ GUI启动失败: {e}")
        print("\n🔄 正在启动CLI模式...")
        return False
    return True


async def main():
    """主函数"""
    interface_mode = choose_interface()

    if interface_mode == "gui":
        success = run_gui()
        if not success:
            print("\n" + "=" * 50)
            await run_cli()
    elif interface_mode == "cli":
        await run_cli()
    else:
        print("👋 再见！")


if __name__ == "__main__":
    asyncio.run(main())
