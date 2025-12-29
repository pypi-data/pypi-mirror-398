import importlib

from lesscode_utils.encryption_algorithm import AES


def condition_by_like(find_condition, column, value):
    if value:
        find_condition[column] = {"$regex": f".*{value}.*"}


def condition_by_in(find_condition, column, param_list, is_object=False, _include=True, is_need_decrypt=False,
                    aes_key="haohaoxuexi"):
    if param_list:
        param_list = [i for i in param_list if i not in [None, "", "all"]]
        if len(param_list) > 0:
            if is_object:
                try:
                    bson = importlib.import_module("bson")
                except ImportError:
                    raise Exception(f"pymongo is not exist,run:pip install pymongo==3.13.0")
                param_list = [bson.ObjectId(_id) for _id in param_list]
            if is_need_decrypt:
                try:
                    param_list = [int(AES.decrypt(key=aes_key, text=_id)) for _id in param_list]
                except:
                    pass
            if _include is True:
                find_condition[column] = {"$in": param_list}
            else:
                find_condition[column] = {"$nin": param_list}


def condition_by_between(column, data_list, and_condition_list, is_contain_end=True, is_contain_start=True):
    if data_list:
        if data_list[0]:
            if is_contain_start:
                and_condition_list.append({column: {"$gte": data_list[0]}})
            else:
                and_condition_list.append({column: {"$gt": data_list[0]}})
        if len(data_list) == 2 and data_list[1]:
            if is_contain_end:
                and_condition_list.append({column: {"$lte": data_list[1]}})
            else:
                and_condition_list.append({column: {"$lt": data_list[1]}})


def condition_by_between_(find_condition, column, data_list, is_contain_end=True, is_contain_start=True):
    if is_contain_start:
        start_op = "$gte"
    else:
        start_op = "$gt"
    if is_contain_end:
        end_op = "$lte"
    else:
        end_op = "$lt"
    if data_list:
        if len(data_list) == 1 and data_list[0]:
            find_condition[column] = {start_op: data_list[0]}
        if len(data_list) == 2:
            if data_list[0] and data_list[1]:
                find_condition[column] = {start_op: data_list[0], end_op: data_list[1]}
            elif not data_list[0] and data_list[1]:
                find_condition[column] = {end_op: data_list[1]}
            elif data_list[0] and not data_list[1]:
                find_condition[column] = {start_op: data_list[0]}


def condition_by_exists(find_condition, column, is_exists=True):
    find_condition[column] = {"$exists": is_exists}


def condition_by_relation(find_condition: dict, column: str, value, and_condition_list: list, relation: str = "$and"):
    if value:
        and_condition_list.append({column: value})
        if and_condition_list:
            find_condition[relation] = and_condition_list


def condition_by_eq(find_condition, column, param, _include=True):
    if param is not None and param != "":
        if _include is True:
            find_condition[column] = param
        else:
            find_condition[column] = {"$ne": param}


def mongodb_sql_paging(page_size, page_num):
    limit = int(page_size)
    skip = (int(page_num) - 1) * int(page_size)

    return limit, skip
