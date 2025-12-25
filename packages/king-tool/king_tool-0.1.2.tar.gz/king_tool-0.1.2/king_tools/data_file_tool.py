#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @Project : king-tool
# @File    : data_file_tool.py
# @IDE     : PyCharm
# @Author  : ZH
# @Time    : 2025/12/22 17:29
import os
import csv
from typing import List, Dict, Any, Union
import pandas as pd


class DataFileTool:
    """通用数据文件工具类：支持 CSV 和 Excel 的读写"""

    # ======================
    # CSV 相关方法
    # ======================

    @staticmethod
    def read_csv(file_path: str, encoding: str = 'utf-8', fieldnames: List[str] = None) -> List[Dict[str, Any]]:
        """读取 CSV 文件为 list[dict]"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV 文件不存在: {file_path}")
        with open(file_path, mode='r', encoding=encoding) as f:
            if fieldnames:
                reader = csv.DictReader(f, fieldnames=fieldnames)
            else:
                reader = csv.DictReader(f)  # 自动用第一行作 header
            return list(reader)

    @staticmethod
    def write_csv(
            data: List[Dict[str, Any]],
            output_dir: str,
            filename: str
    ) -> str:
        """将 list[dict] 写入 CSV 文件，返回完整路径"""
        if not data:
            raise ValueError("写入 CSV 的数据为空")
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        fieldnames = data[0].keys()
        with open(file_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return file_path

    # ======================
    # Excel 相关方法
    # ======================

    @staticmethod
    def read_excel(
            file_path: str,
            sheet_name: Union[str, int] = 0
    ) -> List[Dict[str, Any]]:
        """读取 Excel 文件为 list[dict]"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel 文件不存在: {file_path}")
        df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
        return df.to_dict(orient='records')

    @staticmethod
    def write_excel(
            data: List[Dict[str, Any]],
            output_dir: str,
            filename: str,
            sheet_name: str = 'Sheet1'
    ) -> str:
        """将 list[dict] 写入 Excel 文件，返回完整路径"""
        if not data:
            raise ValueError("写入 Excel 的数据为空")
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        df = pd.DataFrame(data)
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        return file_path
