# -*- coding: utf-8 -*-
"""
@Time : 2025/12/25 16:34
@Email : Lvan826199@163.com
@公众号 : 梦无矶测开实录
@File : table_utils.py
"""
__author__ = "梦无矶小仔"
"""
表格数据处理工具模块
提供数据读取、清洗、转换、分析等常用功能
"""
import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any, Optional
import json
import csv
from pathlib import Path


class TableUtils:
    """表格数据处理工具类"""

    @staticmethod
    def read_table(
            filepath: str,
            file_type: str = None
    ) -> pd.DataFrame:
        """
        读取表格文件

        Args:
            filepath: 文件路径
            file_type: 文件类型，可选：'csv', 'excel', 'json'
                        如为None则根据扩展名自动判断

        Returns:
            pandas DataFrame对象
        """
        if file_type is None:
            # 根据文件扩展名判断类型
            ext = Path(filepath).suffix.lower()
            if ext in ['.csv', '.tsv']:
                file_type = 'csv'
            elif ext in ['.xlsx', '.xls']:
                file_type = 'excel'
            elif ext == '.json':
                file_type = 'json'
            else:
                raise ValueError(f"不支持的文件格式: {ext}")

        readers = {
            'csv': pd.read_csv,
            'excel': pd.read_excel,
            'json': pd.read_json
        }

        if file_type not in readers:
            raise ValueError(f"不支持的文件类型: {file_type}")

        return readers[file_type](filepath)

    @staticmethod
    def save_table(
            df: pd.DataFrame,
            filepath: str,
            file_type: str = None
    ) -> None:
        """
        保存表格到文件

        Args:
            df: pandas DataFrame
            filepath: 保存路径
            file_type: 文件类型，自动判断或指定
        """
        if file_type is None:
            ext = Path(filepath).suffix.lower()
            if ext in ['.csv', '.tsv']:
                file_type = 'csv'
            elif ext in ['.xlsx', '.xls']:
                file_type = 'excel'
            elif ext == '.json':
                file_type = 'json'
            else:
                file_type = 'csv'  # 默认保存为CSV

        savers = {
            'csv': lambda: df.to_csv(filepath, index=False),
            'excel': lambda: df.to_excel(filepath, index=False),
            'json': lambda: df.to_json(filepath, orient='records', indent=2)
        }

        if file_type not in savers:
            raise ValueError(f"不支持的文件类型: {file_type}")

        savers[file_type]()

    @staticmethod
    def filter_data(
            df: pd.DataFrame,
            conditions: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        根据条件筛选数据

        Args:
            df: 原始DataFrame
            conditions: 筛选条件字典
                {列名: 值} 或 {列名: (操作符, 值)}
                操作符: '>', '<', '==', '!=', 'in', 'not in', 'contains'

        Returns:
            筛选后的DataFrame
        """
        mask = pd.Series([True] * len(df))

        for column, condition in conditions.items():
            if column not in df.columns:
                continue

            if isinstance(condition, tuple) and len(condition) == 2:
                op, value = condition
                if op == '>':
                    mask &= (df[column] > value)
                elif op == '<':
                    mask &= (df[column] < value)
                elif op == '>=':
                    mask &= (df[column] >= value)
                elif op == '<=':
                    mask &= (df[column] <= value)
                elif op == '==':
                    mask &= (df[column] == value)
                elif op == '!=':
                    mask &= (df[column] != value)
                elif op == 'in':
                    mask &= df[column].isin(value)
                elif op == 'not in':
                    mask &= ~df[column].isin(value)
                elif op == 'contains':
                    mask &= df[column].astype(str).str.contains(value)
            else:
                # 直接相等匹配
                mask &= (df[column] == condition)

        return df[mask].reset_index(drop=True)

    @staticmethod
    def aggregate_data(
            df: pd.DataFrame,
            group_by: Union[str, List[str]],
            aggregations: Dict[str, Union[str, List[str]]]
    ) -> pd.DataFrame:
        """
        数据分组聚合

        Args:
            df: 原始DataFrame
            group_by: 分组列名
            aggregations: 聚合操作字典
                {列名: 聚合函数} 或 {列名: [聚合函数列表]}
                聚合函数: 'sum', 'mean', 'count', 'min', 'max', 'std'

        Returns:
            聚合后的DataFrame
        """
        return df.groupby(group_by).agg(aggregations).reset_index()

    @staticmethod
    def merge_tables(
            df1: pd.DataFrame,
            df2: pd.DataFrame,
            on: Union[str, List[str]],
            how: str = 'inner'
    ) -> pd.DataFrame:
        """
        合并两个表格

        Args:
            df1: 左侧表格
            df2: 右侧表格
            on: 合并依据的列
            how: 合并方式，可选：'inner', 'left', 'right', 'outer'

        Returns:
            合并后的DataFrame
        """
        return pd.merge(df1, df2, on=on, how=how)

    @staticmethod
    def clean_data(
            df: pd.DataFrame,
            strategy: str = 'drop',
            fill_value: Any = None,
            columns: List[str] = None
    ) -> pd.DataFrame:
        """
        数据清洗：处理缺失值

        Args:
            df: 原始DataFrame
            strategy: 处理策略，可选：'drop', 'fill'
            fill_value: 填充值（当strategy为'fill'时使用）
            columns: 指定处理的列，None表示处理所有列

        Returns:
            清洗后的DataFrame
        """
        df_clean = df.copy()

        if columns is None:
            columns = df.columns.tolist()

        if strategy == 'drop':
            df_clean = df_clean.dropna(subset=columns)
        elif strategy == 'fill':
            for col in columns:
                if col in df_clean.columns:
                    # 为每一列单独计算填充值
                    col_fill_value = fill_value
                    if col_fill_value is None:
                        if pd.api.types.is_numeric_dtype(df_clean[col]):
                            col_fill_value = df_clean[col].mean()
                        else:
                            mode_values = df_clean[col].mode()
                            col_fill_value = mode_values[0] if not mode_values.empty else ''

                    if col_fill_value is not None:
                        df_clean[col] = df_clean[col].fillna(col_fill_value)

        return df_clean.reset_index(drop=True)

    @staticmethod
    def describe_data(df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成数据描述统计

        Args:
            df: 输入DataFrame

        Returns:
            包含统计信息的字典
        """
        description = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_stats': {},
            'categorical_stats': {}
        }

        # 数值型列统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            description['numeric_stats'] = {
                col: {
                    'mean': float(df[col].mean()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'median': float(df[col].median())
                }
                for col in numeric_cols
            }

        # 分类型列统计
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            description['categorical_stats'] = {
                col: {
                    'unique_count': int(df[col].nunique()),
                    'top_value': df[col].mode()[0] if not df[col].mode().empty else None,
                    'top_count': int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0
                }
                for col in categorical_cols
            }

        return description

    @staticmethod
    def pivot_table(
            df: pd.DataFrame,
            index: Union[str, List[str]],
            columns: Union[str, List[str]],
            values: Union[str, List[str]],
            aggfunc: str = 'mean'
    ) -> pd.DataFrame:
        """
        创建数据透视表

        Args:
            df: 原始DataFrame
            index: 行索引
            columns: 列索引
            values: 数值列
            aggfunc: 聚合函数

        Returns:
            透视表DataFrame
        """
        return pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc
        )