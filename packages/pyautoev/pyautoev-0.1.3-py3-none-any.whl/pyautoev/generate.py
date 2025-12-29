# -*- coding: utf-8 -*-
import json

import yaml


def generate_sequence(r, n):
    """
    Generate a sequence of strings with incrementing numeric suffix.

    :param r: Base string ending with a number (e.g., 'XXX001')
    :param n: Number of elements in the sequence
    :return: List of generated sequence strings

    Example:
        >>> generate_sequence('XXX001', 2)
        ['XXX001', 'XXX002']
    """
    if n == 1:
        return [r]

    prefix = r[:-2]
    last_two_digits = int(r[-2:])
    sequence = [f"{prefix}{str(i).zfill(2)}" for i in range(last_two_digits, last_two_digits + n)]
    return sequence


def sql_column_get(column):
    """
    Extract column name from a SQL expression like 'table.column'.

    :param column: Column string, optionally prefixed by table name
    :return: Column name without table prefix if present

    Example:
        >>> sql_column_get('user.id')
        'id'
    """
    column_list = column.split('.')
    return column_list[1] if len(column_list) > 1 else column_list[0]


def format_msg(input_str):
    """
    Format message based on leading symbol '<' or '>'.

    If input starts with '<' or '>', returns a list of numbers in a range:
    - '<': Returns range from (number - 30) to number (exclusive)
    - '>': Returns range from number to (number + 30) (exclusive)

    Otherwise, returns a list containing the original string.

    :param input_str: Input string that may start with '<' or '>'
    :return: List of formatted messages or numbers

    Example:
        >>> format_msg('<100')
        [70, 71, ..., 99]
    """
    if not input_str or input_str[0] not in ('<', '>'):
        return [input_str]

    symbol = input_str[0]
    try:
        number = int(input_str[1:])
    except ValueError:
        return [input_str]

    range_map = {
        '<': range(number - 30, number),
        '>': range(number, number + 30)
    }

    return list(range_map.get(symbol, []))


#  Auto function
def order_datatime(apply_time, product_period, overdue):
    approval_time = apply_time + 1800
    arrival_time = apply_time + 86400
    repay_time = apply_time + product_period * 86400
    complate_time = repay_time + overdue * 86400
    return approval_time, arrival_time, repay_time, complate_time

def convert_unicode_to_chinese(data):
    if isinstance(data, dict):
        return {key: convert_unicode_to_chinese(value) for key, value in data.items()}
    elif isinstance(data, str):
        try:
            # 尝试解析字符串中的 JSON 内容（如果有的话）
            parsed = json.loads(data)
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            # 如果不是有效的 JSON 字符串，则直接转换 Unicode
            return data.encode().decode('unicode_escape')
    else:
        return data

def format_datetime_to_timestamp(date_str):
    if date_str is None or date_str == "" or date_str == 0:
        return 0
    from datetime import datetime
    # 定义日期格式
    date_format = "%Y-%m-%d %H:%M:%S"
    # 将字符串转换为 datetime 对象
    date_object = datetime.strptime(date_str, date_format)
    # 将 datetime 对象转换为时间戳
    timestamp = int(date_object.timestamp())
    # 打印时间戳
    return timestamp


def read_yaml(file_path):
    """
    :param file_path: str - YAML 文件的路径
    :return: dict/list - 解析后的 YAML 内容
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return None

def format_json_str(data):
    if data:
        json_str = json.dumps(data, ensure_ascii=False)
        escaped_json_str = json_str.replace('"', '\\"')
    else:
        escaped_json_str = data
    return escaped_json_str