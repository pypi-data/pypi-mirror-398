# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型评估指标工具
"""

from maque.ai_platform.metrics import MetricsCalculator, save_pred_metrics
from maque.utils.helper_parser import parse_generic_tags
from pathlib import Path
import pandas as pd


def calc_binary_metrics(
    df: pd.DataFrame,
    response_col="response",
    label_col="labels",
    parse_response_to_pred=False,
    pred_parsed_tag="answer",
    record_root_dir="record",
):
    """
    计算交叉二分类指标

    Args:
    df (pd.DataFrame): 包含预测结果和标签的数据框。
    response_col (str, optional): 预测结果所在的列名，默认为 'response'。
    label_col (str, optional): 标签所在的列名，默认为 'labels'。
    parse_response_to_pred (bool, optional): 是否将预测结果解析为特定的格式，默认为 False。
    record_root_dir (str, optional): 记录根目录，默认为 'record'。 会将预测结果保存到record_root_dir文件夹下。

    Returns:
    pd.DataFrame: 包含每个标签下的二分类指标的数据框。

    """

    # 如果需要将预测结果解析为特定的格式
    if parse_response_to_pred:
        parsed_results = [parse_generic_tags(response) for response in df[response_col]]
        parsed_dict = {}
        all_keys = set()
        for d in parsed_results:
            all_keys |= set(d.keys())
        for d in parsed_results:
            for key in all_keys:
                parsed_dict.setdefault(key, []).append(d.get(key, "不规范"))
        df["parsed_results"] = parsed_results
        for param, values in parsed_dict.items():
            df[f"parsed_{param}"] = values
        df["preds"] = df[f"parsed_{pred_parsed_tag}"]
    else:
        # 如果不需要解析预测结果，则直接处理
        df["preds"] = df[response_col].apply(
            lambda x: x if not pd.isna(x) else "不规范"
        )

    df["binary_pred"] = df["preds"].apply(
        lambda x: "白" if x in ["正常", "不违规", "[不违规]"] else "黑"
    )

    if label_col is None:
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        p = Path(f"{record_root_dir}/binary_pred-{timestamp}.xlsx")
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(p, index=False, engine="openpyxl")
    else:
        # 保存预测指标
        # save_pred_metrics(
        #     df=df,
        #     pred_col="preds",
        #     label_col=label_col,
        #     record_folder=f"{record_root_dir}",
        # )

        df["binary_label"] = df[label_col].apply(
            lambda x: "白" if x in ["正常", "不违规", "[不违规]"] else "黑"
        )

        # 替换 target_label 列的 无害 为 不违规
        save_pred_metrics(
            df,
            pred_col="binary_pred",
            label_col="binary_label",
            record_folder=f"{record_root_dir}/binary",
        )
        # 计算labels 列下的每个值groupby的指标
        metrics_dict = {}
        for name, _df in df.groupby(label_col):
            metrics_calculator = MetricsCalculator(
                _df, pred_col="binary_pred", label_col="binary_label"
            )
            metrics = metrics_calculator.get_metrics()
            classification_report = metrics["classification_report"]
            # 判断分类报告中是否存在'黑'类别
            if "黑" in classification_report:
                binary_recall, support = (
                    classification_report["黑"]["recall"],
                    classification_report["黑"]["support"],
                )
                metrics_dict[name] = {
                    "binary_recall": binary_recall,
                    "binary_true": len(_df[_df["binary_pred"] == "黑"]),
                    "support": support,
                }
            else:
                # 如果不存在'黑'类别，则使用'白'类别
                binary_recall, support = (
                    classification_report["白"]["recall"],
                    classification_report["白"]["support"],
                )
                metrics_dict[name] = {
                    "binary_recall": binary_recall,
                    "binary_true": len(_df[_df["binary_pred"] == "白"]),
                    "support": support,
                }
        binary_metrics_df = pd.DataFrame(metrics_dict).T
        markdown_str = f"{binary_metrics_df.to_markdown()}"

        with open(f"{record_root_dir}/binary_metrics.md", "w") as f:
            f.write(markdown_str)
        print(markdown_str)
        return binary_metrics_df
