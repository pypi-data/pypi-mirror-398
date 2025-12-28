from __future__ import annotations
import pandas as pd
from typing import List, Union
import os
import hashlib

def groupby_choice(df: pd.DataFrame, by: Union[str, List], col_name: any, choice='max', inplace=True):
    """
    取分组后的某列最值,组成的新df. 默认inplace.

    Example::
     df = pd.DataFrame({'key' : ['A', 'A', 'B', 'B', 'C', 'C'],
                       'value' : ['v1', 'v2', 'v3', 'v4','v5', 'v6'],
                       'prob' : [1, 5, 50, 2, 5, 5]})
    >>> df
        key value  prob
    0   A    v1     1
    1   A    v2     5
    2   B    v3    50
    3   B    v4     2
    4   C    v5     5
    5   C    v6     5
    >>> groupby_choice(df, 'key', 'prob', 'max')
    >>>
        key value  prob
    1   A    v2     5
    2   B    v3    50
    4   C    v5     5
    """
    if not inplace:
        df = df.copy(deep=True)
    index_list = []
    for idx, item in df.groupby(by)[col_name]:
        if choice == "max":
            index_list.append(item.idxmax())
        elif choice == "min":
            index_list.append(item.idxmin())
        else:
            raise "Invalid `func` parameter."
    return df.iloc[index_list]


def group_df(df, col_name, interval=5, use_max_min_interval=False, closed='neither', dropna=True):
    """
    Parameters
    ----------
        col_name: 根据 `col_name` 进行分组
        interval: 合并采样间隔
        use_max_min_interval: True使用最大最小区间确定等距采样个数； False使用df的样本数目确定采样个数

    """
    if dropna:
        df = df.dropna(axis=0, how='any', inplace=False)
    df = df.sort_values(by=col_name, ascending=True)
    if use_max_min_interval:
        periods = (df[col_name].max() - df[col_name].min()) / interval
    else:
        periods = len(df) // interval

    bins = pd.interval_range(df[col_name].min(), df[col_name].max(),
                             periods=periods,
                             closed=closed)
    pd_cut = pd.cut(df[col_name], bins=bins)
    for idx, i in enumerate(df.groupby(pd_cut)):
        agg_res = i[1].agg('mean')
        if idx == 0:
            df_grouped = agg_res
        else:
            df_grouped = pd.concat([df_grouped, agg_res], axis=1)
    df_grouped = df_grouped.transpose()
    return df_grouped.dropna().reset_index(inplace=False).drop(['index'], axis=1)


def re_ord_df_col(df, col_name, ord_num=0):
    """Re-order df's column name."""
    tmp_list = df.columns.tolist()
    tmp_list.remove(col_name)
    tmp_list.insert(ord_num, col_name)
    df = df[tmp_list]
    return df


def guess_str_fmt(time_str: str, token: str):
    time_list = time_str.split(token)
    list_len = len(time_list)
    if list_len == 3:
        return f"%Y{token}%m{token}%d"
    elif list_len == 2:
        return f"%Y{token}%m"
    elif list_len == 1:
        if len(time_str) == 4:
            return f"%Y"
        elif len(time_str) == 6:
            return f"%Y%m"
        elif len(time_str) == 8:
            return f"%Y%m%d"
        else:
            return None
    else:
        raise ValueError("Invalid datetime format.")


def guess_datetime_fmt(timeseries: List[str], token_list=('-', '/', ' ', '_', '.')):
    """Guess datetime format."""
    for token in token_list:
        time_format = guess_str_fmt(timeseries[0], token)
        if time_format:
            break
    else:
        raise ValueError("Invalid datetime format.")
    return time_format


def insert_line(df: pd.DataFrame, idx, new_line: Union[pd.Series, pd.DataFrame, dict], ignore_index=True):
    df_head = df.iloc[:idx, :]
    df_tail = df.iloc[idx:, :]
    if isinstance(new_line, dict):
        df_line = pd.DataFrame(new_line)
    elif isinstance(new_line, pd.Series):
        df_line = pd.DataFrame(new_line).T
    else:
        df_line = new_line
    df_new = pd.concat([df_head, df_line, df_tail], ignore_index=ignore_index).reset_index(drop=True)
    return df_new


if __name__ == "__main__":
    ts = ['2022-01', '2022/02']
    df = pd.DataFrame({'date': ts, })
    time_format = guess_datetime_fmt(ts)
    print(time_format)
    df['date'] = pd.to_datetime(ts)
    print(df)
