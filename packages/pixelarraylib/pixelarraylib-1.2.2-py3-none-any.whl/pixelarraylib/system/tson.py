#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TSON (Token-Optimized JSON) 转换工具

TSON是一种比JSON更紧凑的格式，用于AI输入输出，可以显著减少TOKEN消耗。
主要优化：
1. 去掉键名中的引号（如果键名是有效的标识符）
2. 去掉不必要的空格和换行
3. 使用更紧凑的数组和对象表示
4. 保持可读性和可解析性
"""

import json
from typing import Any, Union, Tuple


class Tson:
    def __init__(self):
        """
        description:
            初始化TSON转换工具类
        """
        pass

    def _is_valid_identifier(self, s: str) -> bool:
        """
        description:
            检查字符串是否是有效的标识符（不需要引号）
        parameters:
            s(str): 字符串
        return:
            bool: 是否是有效的标识符
        """
        if not s:
            return False

        # 标识符必须以字母或下划线开头，后续可以是字母、数字、下划线
        if not (s[0].isalpha() or s[0] == "_"):
            return False

        for char in s[1:]:
            if not (char.isalnum() or char == "_"):
                return False

        return True

    def _is_identifier_char(self, c: str) -> bool:
        """
        description:
            检查字符是否是标识符的一部分
        parameters:
            c(str): 字符
        return:
            bool: 是否是标识符的一部分
        """
        return c.isalnum() or c == "_"

    def _parse_number(self, s: str, pos: int) -> Tuple[Union[int, float], int]:
        """
        description:
            解析数字
        parameters:
            s(str): 字符串
            pos(int): 位置
        return:
            Tuple[Union[int, float], int]: 数字和下一个位置
        """
        start = pos
        if s[pos] == "-":
            pos += 1

        if pos >= len(s):
            raise ValueError("数字解析错误")

        # 解析整数部分
        while pos < len(s) and s[pos].isdigit():
            pos += 1

        # 解析小数部分
        if pos < len(s) and s[pos] == ".":
            pos += 1
            while pos < len(s) and s[pos].isdigit():
                pos += 1

        # 解析科学计数法
        if pos < len(s) and s[pos] in "eE":
            pos += 1
            if pos < len(s) and s[pos] in "+-":
                pos += 1
            while pos < len(s) and s[pos].isdigit():
                pos += 1

        num_str = s[start:pos]
        if "." in num_str or "e" in num_str.lower():
            return float(num_str), pos
        return int(num_str), pos

    def _parse_string(self, s: str, pos: int) -> Tuple[str, int]:
        """
        description:
            解析字符串（使用JSON的字符串解析逻辑）
        parameters:
            s(str): 字符串
            pos(int): 位置
        return:
            Tuple[str, int]: 字符串和下一个位置
        """
        # 找到字符串的结束位置
        end = pos + 1
        escaped = False

        while end < len(s):
            if escaped:
                escaped = False
                end += 1
                continue

            if s[end] == "\\":
                escaped = True
                end += 1
                continue

            if s[end] == '"':
                # 找到结束引号
                str_content = s[pos : end + 1]
                try:
                    # 使用JSON解析来正确处理转义字符
                    value = json.loads(str_content)
                    return value, end + 1
                except json.JSONDecodeError:
                    raise ValueError(f"字符串解析错误在位置 {pos}")

            end += 1

        raise ValueError(f"字符串未闭合在位置 {pos}")

    def _parse_array(self, s: str, pos: int) -> Tuple[list, int]:
        """
        description:
            解析数组
        parameters:
            s(str): 字符串
            pos(int): 位置
        return:
            Tuple[list, int]: 数组和下一个位置
        """
        pos += 1  # 跳过 '['
        result = []

        # 跳过空白
        while pos < len(s) and s[pos] in " \t\n\r":
            pos += 1

        # 空数组
        if pos < len(s) and s[pos] == "]":
            return result, pos + 1

        # 解析数组元素
        while pos < len(s):
            # 解析值
            value, pos = self._parse_value(s, pos)
            result.append(value)

            # 跳过空白
            while pos < len(s) and s[pos] in " \t\n\r":
                pos += 1

            # 检查是否有更多元素
            if pos >= len(s):
                raise ValueError("数组未闭合")

            if s[pos] == "]":
                return result, pos + 1
            elif s[pos] == ",":
                pos += 1
                # 跳过空白
                while pos < len(s) and s[pos] in " \t\n\r":
                    pos += 1
            else:
                raise ValueError(f"数组解析错误，意外的字符 '{s[pos]}' 在位置 {pos}")

        raise ValueError("数组未闭合")

    def _parse_object(self, s: str, pos: int) -> Tuple[dict, int]:
        """
        description:
            解析对象
        parameters:
            s(str): 字符串
            pos(int): 位置
        return:
            Tuple[dict, int]: 对象和下一个位置
        """
        pos += 1  # 跳过 '{'
        result = {}

        # 跳过空白
        while pos < len(s) and s[pos] in " \t\n\r":
            pos += 1

        # 空对象
        if pos < len(s) and s[pos] == "}":
            return result, pos + 1

        # 解析键值对
        while pos < len(s):
            # 跳过空白
            while pos < len(s) and s[pos] in " \t\n\r":
                pos += 1

            if pos >= len(s):
                raise ValueError("对象未闭合")

            # 解析键
            if s[pos] == '"':
                # 带引号的键
                key, pos = self._parse_string(s, pos)
            else:
                # 不带引号的标识符键
                start = pos
                while pos < len(s) and (
                    self._is_identifier_char(s[pos]) or s[pos] in "-_"
                ):
                    pos += 1
                key = s[start:pos]
                if not key:
                    raise ValueError(f"对象键解析错误在位置 {pos}")

            # 跳过空白
            while pos < len(s) and s[pos] in " \t\n\r":
                pos += 1

            # 检查冒号
            if pos >= len(s) or s[pos] != ":":
                raise ValueError(f"对象键值对缺少冒号在位置 {pos}")
            pos += 1

            # 跳过空白
            while pos < len(s) and s[pos] in " \t\n\r":
                pos += 1

            # 解析值
            value, pos = self._parse_value(s, pos)
            result[key] = value

            # 跳过空白
            while pos < len(s) and s[pos] in " \t\n\r":
                pos += 1

            # 检查是否有更多键值对
            if pos >= len(s):
                raise ValueError("对象未闭合")

            if s[pos] == "}":
                return result, pos + 1
            elif s[pos] == ",":
                pos += 1
            else:
                raise ValueError(f"对象解析错误，意外的字符 '{s[pos]}' 在位置 {pos}")

        raise ValueError("对象未闭合")

    def _parse_value(self, s: str, pos: int) -> Tuple[Any, int]:
        """
        description:
            解析TSON值，返回(值, 下一个位置)
        parameters:
            s(str): 字符串
            pos(int): 位置
        return:
            Tuple[Any, int]: 值和下一个位置
        """
        s = s.strip()
        if not s:
            raise ValueError("无法解析空字符串")

        # 跳过空白字符
        while pos < len(s) and s[pos] in " \t\n\r":
            pos += 1

        if pos >= len(s):
            raise ValueError("意外的字符串结束")

        char = s[pos]

        # 解析null
        if s[pos : pos + 4] == "null":
            return None, pos + 4

        # 解析true/false
        if s[pos : pos + 4] == "true":
            return True, pos + 4
        if s[pos : pos + 5] == "false":
            return False, pos + 5

        # 解析数字
        if char in "-0123456789":
            return self._parse_number(s, pos)

        # 解析字符串
        if char == '"':
            return self._parse_string(s, pos)

        # 解析数组
        if char == "[":
            return self._parse_array(s, pos)

        # 解析对象
        if char == "{":
            return self._parse_object(s, pos)

        raise ValueError(f"无法解析字符 '{char}' 在位置 {pos}")

    def _parse_tson(self, tson_str: str) -> Any:
        """
        description:
            解析TSON字符串
        parameters:
            tson_str(str): TSON字符串
        return:
            Any: 值
        """
        tson_str = tson_str.strip()

        if not tson_str:
            raise ValueError("TSON字符串为空")

        # 解析值
        value, _ = self._parse_value(tson_str, 0)
        return value

    def json_to_tson(self, data: Union[str, dict, list]) -> str:
        """
        description:
            将JSON字符串或Python对象转换为TSON格式
        parameters:
            data(Union[str, dict, list]): JSON字符串、字典或列表
        return:
            tson_str(str): TSON格式的字符串
        """
        # 如果输入是字符串，先解析为Python对象
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError("输入的字符串不是有效的JSON格式")

        def _convert_value(value: Any, indent: int = 0) -> str:
            """
            description:
                递归转换值
            parameters:
                value(Any): 值
                indent(int): 缩进
            return:
                str: 转换后的值
            """
            if value is None:
                return "null"
            elif isinstance(value, bool):
                return "true" if value else "false"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, str):
                # 转义特殊字符
                escaped = json.dumps(value)
                return escaped
            elif isinstance(value, list):
                if not value:
                    return "[]"
                items = []
                for item in value:
                    item_str = _convert_value(item, indent)
                    items.append(item_str)
                return "[" + ",".join(items) + "]"
            elif isinstance(value, dict):
                if not value:
                    return "{}"
                items = []
                for key, val in value.items():
                    # 检查键名是否是有效的标识符（不需要引号）
                    if self._is_valid_identifier(key):
                        key_str = key
                    else:
                        key_str = json.dumps(key)
                    val_str = _convert_value(val, indent)
                    items.append(f"{key_str}:{val_str}")
                return "{" + ",".join(items) + "}"
            else:
                # 对于其他类型，使用JSON序列化
                return json.dumps(value)

        return _convert_value(data)

    def tson_to_json(
        self, tson_str: str, pretty: bool = False
    ) -> Union[str, dict, list]:
        """
        description:
            将TSON格式字符串转换为JSON字符串或Python对象
        parameters:
            tson_str(str): TSON格式的字符串
            pretty(bool): 如果为True，返回格式化的JSON字符串；如果为False，返回Python对象
        return:
            result(Union[str, dict, list]): JSON字符串或Python对象（dict/list）
        """
        # 先尝试直接解析为JSON（兼容标准JSON）
        try:
            result = json.loads(tson_str)
            if pretty:
                return json.dumps(result, ensure_ascii=False, indent=2)
            return result
        except json.JSONDecodeError:
            pass

        # 如果不是标准JSON，进行TSON解析
        try:
            result = self._parse_tson(tson_str)
            if pretty:
                return json.dumps(result, ensure_ascii=False, indent=2)
            return result
        except Exception as e:
            raise ValueError(f"TSON解析失败: {str(e)}")

    def convert_file(
        self, input_file: str, output_file: str = None, to_tson: bool = True
    ):
        """
        description:
            转换文件格式
        parameters:
            input_file(str): 输入文件路径
            output_file(str): 输出文件路径，如果为None则自动生成
            to_tson(bool): 如果为True，将JSON转换为TSON；如果为False，将TSON转换为JSON
        return:
            output_file(str): 输出文件路径
        """
        # 读取输入文件
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 转换
        if to_tson:
            # JSON -> TSON
            try:
                data = json.loads(content)
                tson_content = self.json_to_tson(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"输入文件不是有效的JSON格式: {str(e)}")

            # 确定输出文件
            if output_file is None:
                if input_file.endswith(".json"):
                    output_file = input_file[:-5] + ".tson"
                else:
                    output_file = input_file + ".tson"
        else:
            # TSON -> JSON
            try:
                data = self.tson_to_json(content, pretty=True)
                tson_content = (
                    data
                    if isinstance(data, str)
                    else json.dumps(data, ensure_ascii=False, indent=2)
                )
            except Exception as e:
                raise ValueError(f"输入文件不是有效的TSON格式: {str(e)}")

            # 确定输出文件
            if output_file is None:
                if input_file.endswith(".tson"):
                    output_file = input_file[:-5] + ".json"
                else:
                    output_file = input_file + ".json"

        # 写入输出文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(tson_content)

        return output_file


# 为了向后兼容，提供便捷函数接口
_default_tson = Tson()


def json_to_tson(data: Union[str, dict, list]) -> str:
    """
    description:
        将JSON字符串或Python对象转换为TSON格式（便捷函数）
    parameters:
        data(Union[str, dict, list]): JSON字符串、字典或列表
    return:
        str: TSON格式的字符串
    """
    return _default_tson.json_to_tson(data)


def tson_to_json(tson_str: str, pretty: bool = False) -> Union[str, dict, list]:
    """
    description:
        将TSON格式字符串转换为JSON字符串或Python对象（便捷函数）
    parameters:
        tson_str(str): TSON格式的字符串
        pretty(bool): 如果为True，返回格式化的JSON字符串；如果为False，返回Python对象
    return:
        result(Union[str, dict, list]): JSON字符串或Python对象（dict/list）
    """
    return _default_tson.tson_to_json(tson_str, pretty)


def convert_file(input_file: str, output_file: str = None, to_tson: bool = True):
    """
    description:
        转换文件格式（便捷函数）
    parameters:
        input_file(str): 输入文件路径
        output_file(str): 输出文件路径，如果为None则自动生成
        to_tson(bool): 如果为True，将JSON转换为TSON；如果为False，将TSON转换为JSON
    return:
        output_file(str): 输出文件路径
    """
    return _default_tson.convert_file(input_file, output_file, to_tson)
