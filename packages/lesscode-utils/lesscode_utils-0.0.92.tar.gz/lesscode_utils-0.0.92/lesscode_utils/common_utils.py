import copy
import inspect
import os.path
import random
import string
import time
import traceback
import uuid
from copy import deepcopy
from functools import reduce
from importlib.util import spec_from_file_location, module_from_spec
from itertools import groupby
from typing import Callable, List, Dict, Union

from lesscode_utils.encryption_algorithm import MD5


def convert(value, func):
    return func(value)


def get_value_from_dict(data: dict, key: str = None):
    value = deepcopy(data)
    if key:
        key_list = key.split(".")
        for k in key_list:
            if not isinstance(value, dict):
                break
            else:
                value = value.get(k)
    return value


def list_dict_group(data: List[Dict], key):
    """
    列表字典去重
    :param data: 数据
    :param key: 去重的key
    :return:
    """
    new_data = {"list_data": list(), "dict_data": dict()}
    data.sort(key=lambda x: x.get(key, "") or "")
    group_data = groupby(data, key=lambda x: x.get(key, ""))
    for data_key, values in group_data:
        _values = list(values)
        new_data["list_data"].append({"key": data_key, "values": _values})
        new_data["dict_data"].update({data_key: _values})

    return new_data


def remove_list_dict_duplicate(list_dict_data):
    """
    去除列表字典里的重复数据
    :param list_dict_data: 列表字典
    :return:
    """
    return reduce(lambda x, y: x if y in x else x + [y], [[], ] + list_dict_data)


def retry(func, params: Union[dict, list, tuple, None] = None, check_func: callable = None, num: int = 1):
    """
    执行失败重试
    :param func: 要执行的函数
    :param params: 要执行的函数的参数值
    :param check_func: 校验函数
    :param num: 重试次数
    :return:
    """
    result = None
    for i in range(num):
        try:
            if params:
                if isinstance(params, dict):
                    result = func(**params)
                elif isinstance(params, list) or isinstance(params, tuple):
                    result = func(*params)
                else:
                    break
            else:
                result = func()
            if check_func:
                flag = check_func(result)
                if flag:
                    break
        except Exception as e:
            traceback.print_exc()
            if i == num - 1:
                raise e
    return result


def check_value(value, default):
    if not value:
        value = default
    return value


def fill(value, length, char: str, position="font"):
    value = str(value)
    value_len = len(value)
    if len(value) < length:
        if position == "font":
            value = char * (length - value_len) + value
        else:
            value = value + char * (length - value_len)
    return value


def check_or_add_growth_rate(data: List[dict], value_key: str, growth_rate_key: str = "growth_rate",
                             start_growth_rate: float = None, pre_value: Union[int, float] = None, flag: bool = True,
                             digits: int = None):
    """
    检查或添加增长率字段
    :param data: 数据
    :param value_key: 数据的key
    :param growth_rate_key: 增长率的key
    :param start_growth_rate: 起始增长率
    :param pre_value: 前一个数据
    :param flag: 是否乘100
    :param digits: 小数点位数
    :return:
    """
    for i, _ in enumerate(data):
        if not _.get(growth_rate_key) and value_key in _:
            if i == 0:
                if start_growth_rate:
                    if flag:
                        start_growth_rate = start_growth_rate * 100
                    if digits:
                        start_growth_rate = round(start_growth_rate, digits)
                    data[i][growth_rate_key] = start_growth_rate
                else:
                    if pre_value:
                        current = check_value(data[i].get(value_key, 0), 0) if data[i].get(value_key, 0) else 0
                        value = float(current - pre_value) / abs(pre_value) if pre_value else 0
                    else:
                        value = 0
                    if flag:
                        value = value * 100
                    if digits:
                        value = round(value, digits)
                    data[i][growth_rate_key] = value
            else:
                pre = check_value(data[i - 1].get(value_key, 0), 0) if data[i - 1].get(value_key, 0) else 0
                current = check_value(data[i].get(value_key, 0), 0) if data[i].get(value_key, 0) else 0
                value = float(current - pre) / abs(pre) if pre else 0
                if flag:
                    value = value * 100
                if digits:
                    value = round(value, digits)
                data[i][growth_rate_key] = value


def get_members_from_file(file_path: str, name="module"):
    if os.path.exists(file_path):
        spec = spec_from_file_location(name, file_path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        members = inspect.getmembers(module, lambda member: not inspect.ismodule(member))
        members_list = []
        for key, value in members:
            if not key.startswith('_'):
                info = {"name": key, "value": value}
                if inspect.isclass(value):
                    info["type"] = "class"
                    class_members = []
                    for k, v in vars(value).items():
                        if not k.startswith("_"):
                            class_member_info = {"name": k, "value": v, "type": v.__class__.__name__}
                            class_members.append(class_member_info)
                    info["class_members"] = class_members
                else:
                    info["type"] = value.__class__.__name__
                members_list.append(info)
        return members_list
    else:
        raise Exception(f"file_path={file_path} not exist")


def short_str(value: str, n: int = 1, flag=True, chars=string.ascii_letters + string.digits):
    key = f"{int(time.time() * 1000)}{uuid.uuid4().hex}"
    new_value = f"{key}{value}" if flag else value
    md_str = MD5.encrypt(new_value)
    result = []
    for i in range(0, len(md_str), 8):
        lh = 0x3FFFFFFF & int(md_str[i:i + 8], 16)
        out_chars = ""
        for j in range(0, n):
            index = lh & 0x0000003D
            out_chars += chars[index]
            lh >>= 5
        result.append(random.choice(out_chars))
    return "".join(result)


def get_short_id(chars=string.ascii_letters + string.digits):
    _id = uuid.uuid4().hex
    buffer = []
    for i in range(0, 8):
        start = i * 4
        end = i * 4 + 4
        val = int(_id[start:end], 32)
        buffer.append(chars[val % 62])
    return "".join(buffer)


def str2short_str(value: str, n: int = 5, chars=string.ascii_letters + string.digits):
    uuid_obj = uuid.uuid5(uuid.NAMESPACE_DNS, value)
    uuid_int = uuid_obj.int
    short_str = ""
    for _ in range(n):
        idx = uuid_int % len(chars)
        short_str += chars[idx]
        uuid_int //= len(chars)

    return short_str


def eliminate_empty(data: list):
    return [x for x in data if x not in [None, '', 'NULL']]


def find_child(data, key="id", parent_key="parent_id"):
    new_data = deepcopy(data)
    result = []
    obj = {}
    for x in new_data:
        obj[x.get(key)] = x
    for x in new_data:
        parent_key_value = x.get(parent_key)
        parent = obj.get(parent_key_value, {})
        if parent:
            if not parent.get("children"):
                parent["children"] = []
            if not x.get("children"):
                x["children"] = []
            parent["children"].append(x)
        else:
            if not x.get("children"):
                x["children"] = []
            result.append(x)
    return result


def dict2list(data: dict, data_key="count", key_name="key", value_name="value"):
    result = []
    for key, value in data.items():
        if data_key:
            value = value.get(data_key)
        result.append({key_name: key, value_name: value})
    return result


class ReadOnlyDict(dict):
    def __setitem__(self, key, value):
        raise NotImplementedError("Dictionary is read-only")


def sort_dfs(_tree, sort_key="serial_index", children_key="children", reverse=False):
    if _tree:
        if isinstance(_tree, list):
            _tree = sorted(_tree, key=lambda x: x.get(sort_key) or 0, reverse=reverse)
            for _ in _tree:
                sort_dfs(_, sort_key=sort_key, children_key=children_key, reverse=reverse)
        if isinstance(_tree, dict):
            if _tree.get(children_key):
                _tree[children_key] = sorted(_tree.get(children_key), key=lambda x: x.get(sort_key) or 0,
                                             reverse=reverse)
                for _ in _tree.get(children_key):
                    sort_dfs(_, sort_key=sort_key, children_key=children_key, reverse=reverse)


def sort_tree(data, sort_key="serial_index", children_key="children", reverse=False):
    sort_dfs(data, sort_key=sort_key, children_key=children_key, reverse=reverse)


def recursion_handle(data: Union[List[Dict], Dict], func: Callable, children_key="children"):
    """
    递归处理函数
    :param data:
    :param func:
    :param children_key:
    :return:
    """

    if isinstance(data, list):
        data = func(data)
        for i in data:
            recursion_handle(i, func, children_key=children_key)
    elif isinstance(data, dict):
        if data.get(children_key):
            data[children_key] = func(data.get(children_key, []) or [])
            for i in data.get(children_key):
                recursion_handle(i, func, children_key=children_key)


def tree2list(data_tree, key="children", parent_key="parent_key", data_key="key"):
    data_tree_tmp = copy.deepcopy(data_tree)
    data = []

    def temp(tree, _parent_key=""):
        if tree.get(key):
            for _child in tree.get(key):
                _child[parent_key] = tree.get(data_key)
                temp(_child, _parent_key)
            tree.pop(key)
        data.append(tree)

    if isinstance(data_tree_tmp, list):
        for x in data_tree_tmp:
            temp(x, parent_key)
    elif isinstance(data_tree_tmp, dict):
        temp(data_tree, parent_key)
    return data


def sort_dict_list_by_list(dict_list: List[dict], sort_value_list: List[str], name_key="name"):
    """
    根据sort_value_list的顺序重新排列dict_list中的字典顺序。

    :param name_key:
    :param dict_list: List[Dict] - 包含字典的列表，每个字典都有一个排序属性
    :param sort_value_list: List[str] - 包含字符串的列表，字符串对应dict_list中排序属性
    """
    # 创建一个字典，根据name属性快速查找对应的字典
    name_to_dict = {d[name_key]: d for d in dict_list}

    # 根据name_list的顺序重新排列字典
    ordered_list = [name_to_dict[name] for name in sort_value_list if name in name_to_dict]

    return ordered_list


def find_all_parents(tree: list, target_list: list, parent_key: str = "parent_id", key: str = "id",
                     children_key: str = "children", value_key: str = None):
    """
    查找树形结构中每个目标元素的所有父级（包括间接父级）

    参数:
    target_list: 需要查找父级的目标值列表

    返回:
    字典，key为目标值，value为该目标的所有父级列表（从直接父级到根父级）
    """
    # 创建节点映射表：value -> node_info (包含parent_id和children)
    node_map = {}

    def build_map(nodes):
        """递归构建节点映射表"""
        for node in nodes:
            node_map[node[key]] = node
            if value_key and value_key not in node:
                node[value_key] = node.get(value_key, '')
            if children_key in node and node[children_key]:
                build_map(node[children_key])

    # 构建节点映射表
    build_map(tree)

    result = {}

    def find_parents(value, parents_list):
        """递归查找某个节点的所有父级"""
        node_info = node_map.get(value)
        if not node_info:
            return parents_list

        parent_id = node_info[parent_key]
        if parent_id and parent_id in node_map:
            parent_info = node_map.get(parent_id, {}) or {}
            if value_key:
                if parent_info.get(value_key, {}):
                    parents_list.append(parent_info.get(value_key, {}))
            else:
                parents_list.append(parent_info)
            return find_parents(parent_id, parents_list)
        return parents_list

    # 为每个目标值查找所有父级
    for target in target_list:
        if target in node_map:
            # 查找该节点的所有父级（从直接父级开始到根节点）
            parents = find_parents(target, [])
            result[target] = parents
        else:
            result[target] = []  # 如果节点不存在，返回空列表

    return result


def find_all_children(tree: list, target_list: list, parent_key: str = "parent_id", key: str = "id",
                      children_key: str = "children", value_key: str = None):
    """
    查找树形结构中每个目标元素的所有子级（包括间接子级）

    参数:
    target_list: 需要查找子级的目标值列表

    返回:
    字典，key为目标值，value为该目标的所有子级列表（包括所有后代）
    """
    # 创建节点映射表：value -> node_info (包含parent_id和children)
    node_map = {}

    def build_map(nodes):
        """递归构建节点映射表"""
        for node in nodes:
            node_map[node[key]] = node
            if value_key and value_key not in node:
                node[value_key] = node.get(value_key, '')
            if children_key in node and node[children_key]:
                build_map(node[children_key])

    # 构建节点映射表
    build_map(tree)

    result = {}

    def find_children(parent_id, children_list):
        """递归查找某个节点的所有子级"""
        # 查找所有直接子节点
        for node_id, node_info in node_map.items():
            if node_info[parent_key] == parent_id:
                if value_key:
                    if node_info.get(value_key, ''):
                        children_list.append(node_info.get(value_key, ""))
                else:
                    children_list.append(node_info)
                # 递归查找孙子节点
                find_children(node_id, children_list)
        return children_list

    # 为每个目标值查找所有子级
    for target in target_list:
        if target in node_map:
            # 查找该节点的所有子级（包括所有后代）
            children = find_children(target, [])
            result[target] = children
        else:
            result[target] = []  # 如果节点不存在，返回空列表

    return result
