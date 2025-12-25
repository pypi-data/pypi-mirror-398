#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @Project : king-tool
# @File    : media_encoder_tool.py
# @IDE     : PyCharm
# @Author  : ZH
# @Time    : 2025/12/22 17:36
import base64
import os
import re


class MediaEncoderTool:
    """媒体编码工具类：支持字符串/Base64/图片/音频互转"""

    @staticmethod
    def str_to_base64(text: str, encoding: str = 'utf-8') -> str:
        """
        将字符串编码为 Base64
        :param text: 原始字符串
        :param encoding: 字符编码，默认 utf-8
        :return: Base64 字符串（无前缀）
        """
        return base64.b64encode(text.encode(encoding)).decode('ascii')

    @staticmethod
    def _extract_base64_data(b64_str: str) -> bytes:
        """
        从 Base64 字符串中提取原始字节（自动去除 data:...;base64, 前缀）
        """
        # 移除可能的 data URL 前缀，例如 "data:image/png;base64,"
        match = re.match(r'^data:[^;]*;base64,(.*)$', b64_str)
        if match:
            b64_clean = match.group(1)
        else:
            b64_clean = b64_str.strip()
        try:
            return base64.b64decode(b64_clean)
        except Exception as e:
            raise ValueError("无效的 Base64 字符串") from e

    @staticmethod
    def base64_to_image(
            b64_str: str,
            output_dir: str,
            filename: str
    ) -> str:
        """
        将 Base64 字符串保存为图片文件
        :param b64_str: Base64 字符串（可带 data:image/...;base64, 前缀）
        :param output_dir: 输出目录
        :param filename: 文件名，如 'photo.png'
        :return: 完整文件路径
        """
        image_data = MediaEncoderTool._extract_base64_data(b64_str)
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        return file_path

    @staticmethod
    def base64_to_audio(
            b64_str: str,
            output_dir: str,
            filename: str
    ) -> str:
        """
        将 Base64 字符串保存为音频文件（WAV / MP3 等）
        :param b64_str: Base64 字符串（可带 data:audio/...;base64, 前缀）
        :param output_dir: 输出目录
        :param filename: 文件名，如 'voice.mp3' 或 'record.wav'
        :return: 完整文件路径
        """
        audio_data = MediaEncoderTool._extract_base64_data(b64_str)
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        return file_path
