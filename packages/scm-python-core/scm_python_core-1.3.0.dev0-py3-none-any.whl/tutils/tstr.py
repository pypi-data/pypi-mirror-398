import tlog.tlogging as tl
import os, datetime, re
import fnmatch
import hashlib
import shutil
import yaml
import tempfile
import tutils.tssh as tssh
import xml.etree.ElementTree as ET
import chardet
import codecs
from pathlib import Path
from typing import Union
from typing import Literal

import Levenshtein

log = tl.log if hasattr(tl, "log") else None

DIFF_TYPE_SIMILARITY = "similarity"
DIFF_TYPE_CONTAIN = "contain"
DIFF_TYPES = (DIFF_TYPE_SIMILARITY, DIFF_TYPE_CONTAIN)
DiffTypeLiteral = Literal["similarity", "contain"]

REG_TO_CAMEL = re.compile(r"_(\w)")

SIMILARITY_HISTORY_DATA: dict = {}


def clear_similarity_history_data():
    SIMILARITY_HISTORY_DATA.clear()


def print_similarity_history_data():
    print("---print_similarity_history_data---")
    for str2, similarity_result in SIMILARITY_HISTORY_DATA.items():
        dist, similarity_value = similarity_result
        print(f"{str2} 距离: {dist}, 相似度: {similarity_value:.2f}")


def split_by_low_upper_break(statement: str):
    if len(statement) < 2:
        return [statement]
    result: list[str] = []
    last_index = 0
    for index in range(len(statement)):
        if index == 0:
            continue
        last_str = statement[index - 1]
        current_str = statement[index]
        if last_str.islower() and current_str.isupper():
            result.append(statement[last_index:index])
            last_index = index
    if last_index < len(statement):
        result.append(statement[last_index : len(statement)])
    return result


def find_nth_occurrence(src: str, sub: str, n=1):
    start = -1
    for _ in range(n):
        start = src.find(sub, start + 1)
        if start == -1:
            return -1  # 如果子字符串没有出现n次，返回-1
    return start


def split_by_space(s: str):
    stack: list[str] = []
    result: list[str] = []
    i = 0
    length = len(s)
    start = 0
    while i < length:
        if s[i] in "'\"":
            quote = s[i]
            if len(stack) > 0 and stack[len(stack) - 1] == quote:
                stack.pop()
            else:
                stack.append(quote)
        elif s[i] in " \t\n\r":
            if len(stack) == 0:
                # print("------ split_by_space::", start, f"[{s[i]}]")
                if start != i:
                    result.append(s[start:i])
                start = i + 1
        i += 1
    if start < length:
        result.append(s[start:length])
    return result


def similarity(str1: str, str2: str):
    if not isinstance(str2, str):
        print("---similarity", str2)
    dist = Levenshtein.distance(str1, str2)
    similarity_value = 1 - dist / max(len(str1), len(str2))
    SIMILARITY_HISTORY_DATA[str2] = dist, similarity_value
    return dist, similarity_value


def passed_similarity_handler(
    input_value: str,
    key: str,
    passed_similarity: float,
    passed_dist: int,
    enable_similarity_str_len: int,
):
    if len(key) >= enable_similarity_str_len:
        dist, similarity_value = similarity(input_value, key)
        if similarity_value >= passed_similarity and dist < passed_dist:
            return True
    return False


def exist_in_object(
    input_value: str,
    exist_object: Union[dict, list],
    diff_type: DiffTypeLiteral = DIFF_TYPE_SIMILARITY,
):
    if DIFF_TYPE_CONTAIN == diff_type:
        return exist_in_object_with_contain(input_value, exist_object)
    if DIFF_TYPE_SIMILARITY == diff_type:
        return exist_in_object_with_similarity(input_value, exist_object)
    if input_value in exist_object:
        return (
            exist_object[input_value] if isinstance(exist_object, dict) else input_value
        )
    return None


def exist_in_object_with_contain(
    input_value: str,
    exist_object: Union[dict, list],
):
    # known issues: ssz, 2025.9.25 split会自动过滤掉所有empty item
    input_item_list = input_value.split()
    if isinstance(exist_object, dict):
        for key, value in exist_object.items():
            found = True
            for item in input_item_list:
                if item not in key:
                    found = False
                    break
            if found:
                return key, value
    if isinstance(exist_object, list):
        for key in exist_object:
            found = True
            for item in input_item_list:
                if item not in key:
                    found = False
                    break
            if found:
                return key
    return None


def exist_in_object_with_similarity(
    input_value: str,
    exist_object: Union[dict, list],
    passed_similarity=0.9,
    passed_dist=100,
    enable_similarity_str_len=10,
):
    clear_similarity_history_data()
    if len(input_value) < enable_similarity_str_len:
        return None
    if isinstance(exist_object, dict):
        if input_value in exist_object:
            return input_value, exist_object[input_value]
        for key, value in exist_object.items():
            if passed_similarity_handler(
                input_value,
                key,
                passed_similarity,
                passed_dist,
                enable_similarity_str_len,
            ):
                return key, value
    if isinstance(exist_object, list):
        if input_value in exist_object:
            return input_value
        for item in exist_object:
            if passed_similarity_handler(
                input_value,
                item,
                passed_similarity,
                passed_dist,
                enable_similarity_str_len,
            ):
                return item
    return None


def to_camel_or_lower(name: str, capitalize=False, skip_underscores=True):
    """
    转换name为驼峰命名或小写开头
    capitalize: True 驼峰, False 小写开头
    skip_underscores: 不转换下划线
    """
    # bug: 'a'.capitalize() == 'a', so use upper() to workaround
    str_value = (
        REG_TO_CAMEL.sub(lambda repl: repl.group(1).upper(), name)
        if skip_underscores
        else name
    )
    first_char = f"{str_value[0].upper()}" if capitalize else f"{str_value[0].lower()}"
    return f"{first_char}{str_value[1:]}"


def bash_to_go_template(bash_template: str, **kw_args_dict: dict):
    if kw_args_dict:
        for key, value in kw_args_dict.items():
            bash_template = bash_template.replace(f"${{{key}}}", value)
    return re.sub(
        r"\$\{([^}]+)\}",
        r"{{.\1}}",
        bash_template,
    )
