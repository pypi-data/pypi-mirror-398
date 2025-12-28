import os
from tabulate import tabulate
from datetime import datetime
from maque.io import yaml_dump
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame


def truncate_labels(labels, max_length=50):
    """截断长标签，确保每个标签的长度不超过max_length"""
    truncated_labels = []
    for label in labels:
        if len(label) > max_length:
            truncated_label = label[:max_length] + "..."  # 截断并加上省略号
        else:
            truncated_label = label
        truncated_labels.append(truncated_label)
    return truncated_labels


class MetricsCalculator:
    def __init__(self, df: "DataFrame", pred_col: str = 'predict', label_col: str = 'label',
                 include_macro_micro_avg=False,
                 remove_matrix_zero_row=False,
                 ):
        self.df = df
        self.y_pred = df[pred_col]
        self.y_true = df[label_col]
        self.all_labels = sorted(list(set(self.y_true.unique()).union(set(self.y_pred.unique()))))
        self.needed_labels = None
        self.remove_matrix_zero_row = remove_matrix_zero_row
        self.include_macro_micro_avg = include_macro_micro_avg
        self.metrics = self._calculate_metrics()

    def plot_confusion_matrix(self, save_path: str = None, figsize=(12, 10), font_scale=1.2, font_path=None,
                              x_rotation=45, y_rotation=0):
        import matplotlib.pyplot as plt
        import seaborn as sns
        from matplotlib.font_manager import FontProperties
        import matplotlib
        import warnings
        import warnings

        # 全局设置默认字体，避免警告
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
        matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        # 计算混淆矩阵
        conf_matrix = self.metrics['confusion_matrix']

        # 截断长标签
        all_labels = truncate_labels(self.all_labels, max_length=6)
        num_classes = len(all_labels)  # 获取类的数量

        # 指定中文字体路径
        if font_path:
            font_prop = FontProperties(fname=font_path)
        else:
            font_prop = None

        # 设置动态字体大小，字体大小随着类的数量增加而减小
        dynamic_font_size = max(8, 20 - num_classes)  # 例如：最小字体为8，随类别数增多字体减小
        tick_font_prop = FontProperties(fname=font_path, size=dynamic_font_size) if font_path else None

        # 设置绘图的大小和风格
        plt.figure(figsize=figsize)
        sns.set_theme(font_scale=font_scale)

        # 忽略所有 UserWarning
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)

            # 绘制热力图
            sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=all_labels,
                        yticklabels=all_labels)

            # 设置标题和轴标签
            plt.title("Confusion Matrix", fontproperties=font_prop)
            plt.xlabel("Predicted Labels", fontproperties=font_prop)
            plt.ylabel("True Labels", fontproperties=font_prop)

            # 设置轴标签的字体属性和角度
            plt.xticks(ha="right", fontproperties=tick_font_prop, rotation=x_rotation)
            plt.yticks(fontproperties=tick_font_prop, rotation=y_rotation)

            plt.tight_layout()

            # 保存或显示图表
            if save_path:
                plt.savefig(save_path)
            plt.show()

    def _calculate_metrics(self):
        from sklearn.metrics import precision_score, recall_score, accuracy_score, confusion_matrix, \
            classification_report
        # 计算准确率
        accuracy = accuracy_score(self.y_true, self.y_pred)

        # 计算每个类别的精确率和召回率
        precision = precision_score(self.y_true, self.y_pred, labels=self.all_labels, average='weighted',
                                    zero_division=0)
        recall = recall_score(self.y_true, self.y_pred, labels=self.all_labels, average='weighted', zero_division=0)

        # 计算混淆矩阵
        conf_matrix = confusion_matrix(self.y_true, self.y_pred, labels=self.all_labels)

        # 计算每个类别的精确率、召回率、F1分数等
        report = classification_report(self.y_true, self.y_pred, labels=self.all_labels, output_dict=True,
                                       zero_division=0)
        # 移除宏平均和微平均，默认只保留加权平均
        if not self.include_macro_micro_avg:
            report = {label: metrics for label, metrics in report.items() if
                      label in self.all_labels or label == 'weighted avg'}

        # 从report中移除不需要的类别，具体来说，去除support为0的类别
        report = {label: metrics for label, metrics in report.items()
                  if metrics['support'] > 0}

        self.needed_labels = [label for label in report.keys() if label in self.all_labels]

        # 移除matrix中不需要的行
        needed_idx_list = [self.all_labels.index(label) for label in self.needed_labels]

        if self.remove_matrix_zero_row:
            conf_matrix = conf_matrix[needed_idx_list]

        # 返回结果
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'confusion_matrix': conf_matrix,
            'classification_report': report
        }

    def get_metrics(self):
        return self.metrics

    def format_classification_report_as_markdown(self):
        report = self.metrics['classification_report']
        header = "| Label | Precision | Recall | F1-score | Support |\n"
        separator = "|-------|-----------|--------|----------|---------|\n"
        rows = []
        for label, metrics in report.items():
            if isinstance(metrics, dict):
                rows.append(
                    f"| {label} | {metrics['precision']:.2f} | {metrics['recall']:.2f} | {metrics['f1-score']:.2f} | {metrics['support']:.0f} |")
        return header + separator + "\n".join(rows)

    def clean_label_for_markdown(self, label, max_length=20):
        """清理标签文本，使其适合在markdown表格中显示"""
        # 转换为字符串并替换换行符
        label = str(label).replace('\n', ' ')
        
        # 移除或替换可能破坏markdown格式的字符
        label = label.replace("|", "\\|")
        label = label.replace("-", "\\-")
        label = label.replace("<", "&lt;")
        label = label.replace(">", "&gt;")
        
        # 截断长文本
        if len(label) > max_length:
            label = label[:max_length] + "..."
            
        # 确保标签至少有一个可见字符
        label = label.strip()
        if not label:
            label = "(empty)"
            
        return label

    def format_confusion_matrix_as_markdown(self, max_label_length=20):
        matrix = self.metrics['confusion_matrix']
        
        # 处理标签
        if self.remove_matrix_zero_row:
            labels = self.needed_labels
        else:
            labels = self.all_labels
            
        # 处理所有标签
        processed_labels = [self.clean_label_for_markdown(label, max_label_length) for label in labels]
            
        # 构建表头，确保第一列也有标题
        header = "| 真实值/预测值 | " + " | ".join(processed_labels) + " |\n"
        
        # 修复分隔符，确保每列都有正确的分隔符
        separator_parts = [":---:"] * (len(processed_labels) + 1)  # +1 是为了第一列
        separator = "| " + " | ".join(separator_parts) + " |\n"
        
        rows = []
        for i, row in enumerate(matrix):
            # 处理行标签
            row_label = self.clean_label_for_markdown(labels[i], max_label_length)
            # 格式化数字
            formatted_row = [f"{num:,}" for num in row]
            rows.append(f"| {row_label} | " + " | ".join(formatted_row) + " |")

        return header + separator + "\n".join(rows)


def save_pred_metrics(df: "DataFrame", pred_col: str, label_col: str,
                      record_folder='record', config=None, prompt=None, font_path=None,
                      plot_confusion_matrix=False,
                      ):
    """ 保存预测结果的指标概览和分类报告 """
    metrics_calculator = MetricsCalculator(df, pred_col=pred_col, label_col=label_col)
    metrics = metrics_calculator.get_metrics()

    table = [["指标概览", "Accuracy", "Precision", "Recall"],
             ["值", metrics['accuracy'], metrics['precision'], metrics['recall']]]
    md = f"\n\n### 指标概览\n\n{tabulate(table, headers='firstrow', tablefmt='github')}"
    metrics_md = metrics_calculator.format_classification_report_as_markdown()
    confusion_matrix_md = metrics_calculator.format_confusion_matrix_as_markdown()
    md += (f"\n\n### Classification Report\n{metrics_md}\n"
           f"\n### Confusion Matrix\n{confusion_matrix_md}")
    now = datetime.now().strftime("%m月%d日%H时%M分%S秒")
    record_folder = Path(record_folder)
    record_folder = record_folder / f'记录时间-{now}'
    record_folder.mkdir(parents=True, exist_ok=True)
    console = Console()
    console.print(Markdown(md))

    # save files:
    with open(os.path.join(record_folder, 'metrics.md'), 'w', encoding='utf-8') as f:
        f.write(md)

    if plot_confusion_matrix:
        try:
            metrics_calculator.plot_confusion_matrix(
                save_path=os.path.join(record_folder, 'confusion_matrix.png'),
                font_path=font_path,
                x_rotation=45,
                y_rotation=0,
            )
        except Exception as e:
            print(f"warning: Failed to plot confusion matrix: {e}")

    if prompt:
        yaml_dump(os.path.join(record_folder, 'prompt.yaml'), prompt)
    if config:
        yaml_dump(os.path.join(record_folder, 'config.yaml'), config)

    bad_case_df = df[df[pred_col] != df[label_col]]
    try:
        df.to_excel(os.path.join(record_folder, 'result.xlsx'), index=False, engine='openpyxl')
        bad_case_df.to_excel(os.path.join(record_folder, 'bad_case.xlsx'), index=False, engine='openpyxl')
    except Exception:
        print("No module named 'openpyxl'. Please install it with 'pip install openpyxl'.\n"
              "Save result.csv and bad_case.csv instead.")
        df.to_csv(os.path.join(record_folder, 'result.csv'), index=False)
        bad_case_df.to_csv(os.path.join(record_folder, 'bad_case.csv'), index=False)

