from lesscode_utils.encryption_algorithm.aes import AES


def format_company_id_en(value, route_key, key="haohaoxuexi"):
    if route_key in ["core.patent", "core.patent_lite"]:
        for data in value.get("tags", {}).get("proposer_type", []):
            if data.get("code"):
                data["code"] = AES.encrypt(key=key, text=data["code"])
    elif route_key in ["core.research_institution"]:
        for data in value.get("tags", {}).get("support_unit", []):
            if data.get("id"):
                data["id"] = AES.encrypt(key=key, text=data["id"])
    elif route_key in ["core.investment"]:
        for data in value.get("tags", {}).get("invest_company", []):
            if data.get("company_id"):
                data["company_id"] = AES.encrypt(key=key, text=data["company_id"])




def format_es_param_result(r, param_list, is_need_decrypt, is_need_es_score, route_key, key="haohaoxuexi"):
    result_dict = {}
    format_company_id_en(r["_source"], route_key)
    if param_list and r["_source"]:
        for param_key in param_list:
            value = r["_source"]
            key_arr = param_key.split(".")
            for _key in key_arr:
                if isinstance(value, list):
                    if value:
                        result = []
                        for v in value:
                            if isinstance(v.get(_key, None), list):
                                result = result + v[_key]
                            else:
                                result.append(v.get(_key, None))
                        value = result
                elif isinstance(value, dict):
                    value = value.get(_key, None)
                else:
                    pass
            if key_arr:
                _key = key_arr[-1]
                if result_dict.get(_key) is None:
                    if value is not None:
                        result_dict[_key] = value
    else:
        result_dict = r["_source"]
    if is_need_decrypt:
        r["_id"] = AES.encrypt(key=key, text=r["_id"])
    result_dict["_id"] = r["_id"]
    if is_need_es_score:
        result_dict["_score"] = r["_score"]
    return result_dict


def es_condition_by_match_phrase(bool_list, column, param, slop=0):
    if param:
        if isinstance(param, list):
            param = [_ for _ in param if _]
            if param:
                bool_list.append({
                    "match_phrase": {
                        column: {
                            "query": param[0],
                            "slop": slop
                        }
                    }
                })
        if isinstance(param, str):
            if param:
                bool_list.append({
                    "match_phrase": {
                        column: {
                            "query": param,
                            "slop": slop
                        }
                    }
                })


def es_condition_by_match(bool_list, column, param):
    if param:
        if isinstance(param, list):
            param = [_ for _ in param if _]
            if param:
                bool_list.append({
                    "match": {
                        column: {
                            "query": param[0],
                        }
                    }
                })
        if isinstance(param, str):
            if param:
                bool_list.append({
                    "match": {
                        column: {
                            "query": param,
                        }
                    }
                })


def es_condition_by_not_null(boo_must_list, column, param):
    if param is not None:
        if param:
            boo_must_list.append({
                "exists": {
                    "field": column
                }
            })
        else:
            boo_must_list.append({"bool": {"must_not": [{
                "exists": {
                    "field": column
                }
            }]}})


def es_condition_by_range(bool_must_list, column, range_list, is_contain_end=False, is_contain_start=True):
    if range_list:
        range_dict = {}
        if range_list[0]:
            if is_contain_start:
                range_dict["gte"] = range_list[0]
            else:
                range_dict["gt"] = range_list[0]
        if len(range_list) == 2 and range_list[1]:
            end = range_list[1]
            if is_contain_end:
                range_dict["lte"] = end
            else:
                range_dict["lt"] = end

        if range_dict:
            bool_must_list.append({
                "range": {
                    column: range_dict
                }})


def es_condition_by_terms(bool_must_list, column, param_list, is_need_decrypt=False, key="haohaoxuexi"):
    if param_list:
        param_list = [i for i in param_list if i not in [None, "", "all"]]
        if is_need_decrypt:
            for index, _id in enumerate(param_list):
                # noinspection PyBroadException
                try:
                    _id = AES.decrypt(key=key, text=_id)
                    param_list[index] = int(_id)
                except Exception:
                    pass
        if param_list:
            bool_must_list.append({
                "terms": {
                    column: param_list
                }})


def es_condition_by_wildcard(bool_list, column, param):
    if param:
        bool_list.append({"wildcard": {column: f"*{param}*"}})


def es_condition_by_exist(bool_must_list, param, is_exists="是"):
    if param:
        if is_exists == "是" or is_exists == "true" or is_exists is True:
            bool_must_list.append({
                "exists": {
                    "field": param
                }})
        else:
            bool_must_list.append({
                "bool": {
                    "must_not": [
                        {
                            "exists": {
                                "field": param
                            }
                        }
                    ]
                }
            })


def es_condition_by_exist_or_not(bool_must_list, param_dict):
    if param_dict:
        for key in param_dict:
            if param_dict[key] in ["是", "true", True]:
                bool_must_list.append({
                    "exists": {
                        "field": key
                    }})
            else:
                bool_must_list.append({
                    "bool": {
                        "must_not": [
                            {
                                "exists": {
                                    "field": key
                                }
                            }
                        ]
                    }
                })


def es_condition_by_not_in(bool_must_list: list = None, column="", param_list=None):
    if param_list:
        bool_must_list.append({
            "bool": {
                "must_not": {
                    "terms": {
                        column: param_list
                    }}
            }
        })


def es_condition_by_geo_shape(bool_must_list: list = None, column="", polygon=None, geo_type="MultiPolygon",
                              relation="intersects"):
    if polygon:
        bool_must_list.append({
            "geo_shape": {
                column: {
                    "shape": {
                        "type": geo_type,
                        "coordinates": polygon
                    },
                    "relation": relation
                }
            }
        })


def format_bool_must_and_should(bool_must_list, bool_should_more_list):
    if bool_should_more_list:
        for bool_should in bool_should_more_list:
            bool_must_list.append({
                "bool": {
                    "should": bool_should
                }
            })


def format_bool_must_and_must_not(bool_must_list, bool_must_not_more_list):
    if bool_must_not_more_list:
        for bool_must_not in bool_must_not_more_list:
            bool_must_list.append({
                "bool": {
                    "must_not": bool_must_not
                }
            })


def parse_es_sort_list(column=None, order=None):
    if column and order:
        if order == "asc":
            sort_list = [
                {
                    column: {
                        "order": order,
                        "missing": "_last"
                    }
                }
            ]
        else:
            sort_list = [
                {
                    column: {
                        "order": order,
                        "missing": "_last"
                    }
                }
            ]
    else:
        sort_list = []

    return sort_list


def es_condition_by_geo_distance(bool_must_list: list = None, column="", geo_distance=None):
    if geo_distance:
        bool_must_list.append({
            "geo_distance": {
                "distance": "{}{}".format(geo_distance.get("radius", 0), geo_distance.get("unit", "km")),
                column: {
                    "lat": geo_distance.get("lat", 0),
                    "lon": geo_distance.get("lon", 0),
                }
            }
        })


def es_mapping2dict(mapping):
    mapping_dict = dict()

    if isinstance(mapping, dict):
        if "properties" in mapping:
            for k, v in mapping.get("properties").items():
                if isinstance(v, dict):
                    if "properties" not in v:
                        if "fields" not in v and "type" in v:
                            field_type = v.get("type")
                            mapping_dict[k] = field_type
                        elif "fields" in v and "type" in v:
                            field_type = v.get("type")
                            mapping_dict[k] = field_type
                            if isinstance(v.get("fields"), dict):
                                for fk, fv in v.get("fields").items():
                                    if "type" in fv:
                                        mapping_dict[f"{k}.{fk}"] = fv.get("type")

                    else:
                        mapping_dict[k] = es_mapping2dict(v)

    return mapping_dict
