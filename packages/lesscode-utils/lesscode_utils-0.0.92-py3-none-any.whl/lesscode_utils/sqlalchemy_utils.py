import importlib


def condition_by_between(filters: list, model, column, start_value, end_value):
    _filter = None
    if start_value is not None and end_value is not None:
        _filter = getattr(model, column).between(start_value, end_value)
        filters.append(_filter)
    return _filter


def condition_by_in(filters: list, model, column, value):
    _filter = None
    if value and isinstance(value, list):
        value = [_ for _ in value if _ not in [None, '', 'all']]
        if value:
            _filter = getattr(model, column).in_(value)
            filters.append(_filter)
    return _filter


def condition_by_like(filters: list, model, column, value, position: str = "LR"):
    _filter = None
    if value is not None and value != "":
        if position == "LR":
            value = f"%{value}%"
        elif position == "L":
            value = f"%{value}"
        elif position == "R":
            value = f"{value}%"
        else:
            value = f"%{value}%"
        _filter = getattr(model, column).like(value)
        filters.append(_filter)
    return _filter


def condition_by_regex(filters: list, model, column, value):
    _filter = None
    if value:
        _filter = getattr(model, column).like(value)
        filters.append(_filter)
    return _filter


def condition_by_not_in(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column).notin_(value)
        filters.append(_filter)
    return _filter


def condition_by_not_like(filters: list, model, column, value):
    _filter = None
    if value:
        _filter = getattr(model, column).notlike(value)
        filters.append(_filter)
    return _filter


def condition_by_is_null(filters: list, model, column):
    _filter = getattr(model, column).is_(None)
    filters.append(_filter)
    return _filter


def condition_by_not_null(filters: list, model, column):
    _filter = getattr(model, column).isnot(None)
    filters.append(_filter)
    return _filter


def condition_by_not_in_list(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = ~getattr(model, column).in_(value)
        filters.append(_filter)
    return _filter


def condition_by_eq(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column) == value
        filters.append(_filter)
    return _filter


def condition_by_not_eq(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column) != value
        filters.append(_filter)
    return _filter


def condition_by_gt(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column) > value
        filters.append(_filter)
    return _filter


def condition_by_gte(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column) >= value
        filters.append(_filter)
    return _filter


def condition_by_lt(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column) < value
        filters.append(_filter)
    return _filter


def condition_by_lte(filters: list, model, column, value):
    _filter = None
    if value is not None:
        _filter = getattr(model, column) <= value
        filters.append(_filter)
    return _filter


def condition_by_range(filters: list, model, column, value: list = None, is_contain_end=True, is_contain_start=True):
    try:
        sqlalchemy = importlib.import_module("sqlalchemy")
    except ImportError:
        raise Exception(f"sqlalchemy is not exist,run:pip install sqlalchemy==1.4.36")
    _filter = None
    if value and isinstance(value, list):
        if len(value) == 2:
            _filter1 = None
            _filter2 = None
            if is_contain_start:
                _filter1 = condition_by_gte([], model, column, value[0])
            else:
                _filter1 = condition_by_gt([], model, column, value[0])
            if is_contain_end:
                _filter2 = condition_by_lte([], model, column, value[1])
            else:
                _filter2 = condition_by_lt([], model, column, value[1])
            if _filter1 is not None and _filter2 is not None:
                _filter = sqlalchemy.and_(_filter1, _filter2)
            elif _filter1 is not None and _filter2 is None:
                _filter = _filter1
            elif _filter1 is None and _filter2 is not None:
                _filter = _filter2
        elif len(value) == 1:
            if is_contain_start:
                _filter = condition_by_gte([], model, column, value[0])
            else:
                _filter = condition_by_gt([], model, column, value[0])
    if _filter is not None:
        filters.append(_filter)
    return _filter


def condition_by_relation(filters: list, model, _column, _relation, _value, _end_value=None, _position="LR",
                          is_contain_end=True, is_contain_start=True):
    if _relation == "in":
        condition_by_in(filters, model, _column, _value)
    elif _relation == "like":
        condition_by_like(filters, model, _column, _value, _position)
    elif _relation == "regex" or _relation == "re":
        condition_by_regex(filters, model, _column, _value)
    elif _relation == "between":
        condition_by_between(filters, model, _column, _value, _end_value)
    elif _relation == "not in" or _relation == "ni":
        condition_by_not_in(filters, model, _column, _value)
    elif _relation == "not like" or _relation == "nl":
        condition_by_not_like(filters, model, _column, _value)
    elif _relation == "is null" or _relation == "is empty" or _relation == "inl":
        condition_by_is_null(filters, model, _column)
    elif _relation == "not null" or _relation == "nn":
        condition_by_not_null(filters, model, _column)
    elif _relation == "not in list" or _relation == "nil":
        condition_by_not_in_list(filters, model, _column, _value)
    elif _relation == "eq" or _relation == "=":
        condition_by_eq(filters, model, _column, _value)
    elif _relation == "not eq" or _relation == "!=":
        condition_by_not_eq(filters, model, _column, _value)
    elif _relation == "gt" or _relation == ">":
        condition_by_gt(filters, model, _column, _value)
    elif _relation == "gte" or _relation == ">=":
        condition_by_gte(filters, model, _column, _value)
    elif _relation == "lt" or _relation == "<":
        condition_by_lt(filters, model, _column, _value)
    elif _relation == "lte" or _relation == ">=":
        condition_by_lte(filters, model, _column, _value)
    elif _relation == "range":
        condition_by_range(filters, model, _column, _value, is_contain_start=is_contain_start,
                           is_contain_end=is_contain_end)


def query_with_order_by(query, order_by_list: list = None):
    """
    :param query:
    :param order_by_list: [{"column":User.id,"order":"desc"}]
    :return:
    """
    if order_by_list is not None:
        for order in order_by_list:
            column = order.get("column")
            if column:
                if order.get("order") == "desc":
                    query = query.order_by(column.desc())
                else:
                    query = query.order_by(column.asc())
    return query


def single_model_format_order(model, sort_list):
    """
    :param model:
    :param sort_list: [{"column":"id","order":"desc"}]
    :return:
    """
    new_sort_list = []
    if sort_list is not None:
        for order in sort_list:
            column = order.get("column")
            if column:
                if hasattr(model, column):
                    column = getattr(model, column)
                    if order.get("order") == "desc":
                        column = column.desc()
                    else:
                        column = column.asc()
                    new_sort_list.append(column)
    return new_sort_list


def alchemy_default_to_dict(params, data, repetition=False):
    data_list = []
    key_list = []
    if repetition:
        for arg in params:
            if arg.key:
                key_list.append(arg.key)
            else:
                key_list.append(arg.name)
    else:
        for arg in params:
            arg = str(arg)
            if "(" in arg and ")" in arg:
                key_list.append(arg.split(".")[-1][:-1])
            else:
                key_list.append(arg.split(".")[-1])
    if isinstance(data, list):
        for d in data:
            dict_data = dict(zip(key_list, d))
            data_list.append(dict_data)
        return data_list
    else:
        if data:
            return dict(zip(key_list, data))
        else:
            return {}


def sqlalchemy_paging(query, limit_number, offset_number):
    data_list = query.limit(limit_number).offset(offset_number).all()
    data_count = query.count()
    return {"count": data_count, "dataSource": data_list}


def covert_relationship_property(attr, attr_value):
    if attr.__class__.__name__ == 'ColumnProperty':
        return attr_value
    elif attr.__class__.__name__ in ['RelationshipProperty', 'Relationship']:
        attrs = []
        for ar, ar_value in attr.mapper.attrs.items():
            if ar_value.__class__.__name__ == 'ColumnProperty' and ar not in attrs:
                attrs.append(ar)
        if attr_value.__class__.__name__ == 'InstrumentedList' or isinstance(attr_value, list):
            new_data = []
            for item in attr_value:
                info = dict()
                for ar in attrs:
                    if hasattr(item, ar):
                        new_attr_value = getattr(item, ar)
                        if new_attr_value.__class__.__name__ not in ['RelationshipProperty', 'InstrumentedList']:
                            info[ar] = new_attr_value
                        else:
                            info = covert_relationship_property(ar, new_attr_value)
                if info:
                    new_data.append(info)
            return new_data
        else:
            new_data = dict()
            for column, value in attr.entity.attrs.items():
                if value.__class__.__name__ not in ['RelationshipProperty', 'InstrumentedList']:
                    if hasattr(attr_value, column):
                        val = getattr(attr_value, column)
                        if val.__class__.__name__ not in ['RelationshipProperty', 'InstrumentedList']:
                            new_data[column] = val
            return new_data
    else:
        return attr_value


def query_set_to_dict(obj):
    if obj:
        if hasattr(obj, "__mapper__"):
            obj_dict = {}
            mapper = obj.__mapper__
            if hasattr(mapper, "attrs"):
                attrs = mapper.attrs
                for column, attr in attrs.items():
                    if hasattr(obj, column):
                        attr_value = getattr(obj, column)
                        value = covert_relationship_property(attr, attr_value)
                        if not value.__class__.__name__ == 'RelationshipProperty':
                            obj_dict[column] = value

            return obj_dict
        elif hasattr(obj, "keys"):
            return {key: getattr(obj, key) for key in obj.keys()}
        elif hasattr(obj, "_asdict"):
            return obj._asdict()
        else:
            return dict(obj)
    else:
        return obj


def query_set_to_list(query_set):
    ret_list = []
    for obj in query_set:
        ret_dict = query_set_to_dict(obj)
        ret_list.append(ret_dict)
    return ret_list


def result_to_json(data):
    if isinstance(data, list):
        return query_set_to_list(data)
    else:
        return query_set_to_dict(data)


def result_page(query, page_num=1, page_size=10):
    offset_number = (page_num - 1) * page_size if page_num >= 1 else 0
    data_list = result_to_json(query.limit(page_size).offset(offset_number).all())
    data_count = query.count()
    return {"count": data_count, "dataSource": data_list}
