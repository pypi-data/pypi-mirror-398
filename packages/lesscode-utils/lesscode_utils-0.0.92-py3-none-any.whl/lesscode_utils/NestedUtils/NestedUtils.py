import json
import re
from datetime import date, datetime

from lesscode_utils.NestedUtils.nested_ddl import NestedDict


def standard_nested(nested_string: str) -> dict:
    nested_string = re.sub(r"Nullable\(([\w\W]+?)\)", r"\1", nested_string)
    nested_string = re.sub(r"Array\(([\w]+)\)", r"\1", nested_string)
    nested_string = re.sub(r"FixedString\(([\w]+)\)", r"\1", nested_string)
    nested_string = re.sub(r"Enum8\([\d\D]+?\)", r"String", nested_string)
    nested_string = re.sub(r'(["\w]+) ([\w]+)', r'"\1":"\2"', nested_string)
    nested_string = nested_string.replace("(Date32)", '')
    nested_string = nested_string.replace('"Nested"', "")
    nested_string = nested_string.replace('(', '{')
    nested_string = nested_string.replace(')', '}')
    nested_string = json.loads(nested_string)
    return nested_string


def format_data(data, template):
    formatted_data = {}
    for index, (key, value) in enumerate(template.items()):
        if isinstance(value, dict):
            formatted_data[key] = []
            for sub_data in data[index]:
                formatted_data[key].append(format_data(sub_data, value))
        else:
            if isinstance(data[index], date) or isinstance(data[index], datetime):
                d = str(data[index])
            else:
                d = data[index]
            formatted_data[key] = d
    return formatted_data


def standard_nested_value(data_list: list, nested_key: str) -> list:
    table_name, field_name = nested_key.split(".")
    nested_string = NestedDict.get(table_name).get(field_name)
    template = standard_nested(nested_string)
    result_list = []
    for data in data_list:
        result_list.append(format_data(data, template))
    return result_list
