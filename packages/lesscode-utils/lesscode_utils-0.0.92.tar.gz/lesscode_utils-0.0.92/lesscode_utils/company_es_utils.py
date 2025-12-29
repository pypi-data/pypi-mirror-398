def parse_company_industry_tag(tags):
    tag_list = []
    industry_tag = tags.get("industry_tag", [])
    if industry_tag:
        for _ in industry_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_permission_level_tag(tags):
    permission = tags.get("permission", [])
    tag_list = []
    if permission:
        for _ in permission:
            if _:
                level = _.get("level")
                if level:
                    tag_list.append(level)
    return tag_list


def parse_company_permission_name_tag(tags):
    permission = tags.get("permission", [])
    tag_list = []
    if permission:
        for _ in permission:
            if _:
                permission_name = _.get("permission_name")
                if permission_name:
                    tag_list.append(permission_name)
    return tag_list


def parse_company_certification_tag(tags):
    certification = tags.get("certification", [])
    tag_list = []
    if certification:
        for _ in certification:
            if _:
                certification_name = _.get("certification_name")
                if certification_name:
                    tag_list.append(certification_name)
    return tag_list


def parse_company_award_tag(tags):
    award_tag = tags.get("award_tag", [])
    tag_list = []
    if award_tag:
        for _ in award_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_rank_tag(tags):
    rank_tag = tags.get("rank_tag", [])
    tag_list = []
    if rank_tag:
        for _ in rank_tag:
            if _:
                rank_name = _.get("rank_name")
                if rank_name:
                    tag_list.append(rank_name)
    return tag_list


def parse_company_diy_tag(tags):
    diy_tag = tags.get("diy_tag", [])
    tag_list = []
    if diy_tag:
        for _ in diy_tag:
            if _:
                tag_list.append(_)
    return tag_list


def parse_company_national_tag(tags):
    national_tag = tags.get("national_tag", [])
    tag_list = []
    if national_tag:
        for _ in national_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_province_tag(tags):
    province_tag = tags.get("province_tag", [])
    tag_list = []
    if province_tag:
        for _ in province_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_city_tag(tags):
    city_tag = tags.get("city_tag", [])
    tag_list = []
    if city_tag:
        for _ in city_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_district_tag(tags):
    district_tag = tags.get("district_tag", [])
    tag_list = []
    if district_tag:
        for _ in district_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_park_tag(tags):
    park_tag = tags.get("park_tag", [])
    tag_list = []
    if park_tag:
        for _ in park_tag:
            if _:
                tag_name = _.get("tag_name")
                if tag_name:
                    tag_list.append(tag_name)
    return tag_list


def parse_company_nei_code2_tag(tags):
    nei_code2 = tags.get("nei_code2", {})
    tag_list = []
    if nei_code2:
        tag_name = nei_code2.get("tag_name")
        if tag_name:
            tag_list.append(tag_name)
    return tag_list


def parse_company_nei_code3_tag(tags):
    nei_code3 = tags.get("nei_code3", {})
    tag_list = []
    if nei_code3:
        tag_name = nei_code3.get("tag_name")
        if tag_name:
            tag_list.append(tag_name)
    return tag_list


def parse_company_nei_code4_tag(tags):
    nei_code4 = tags.get("nei_code4", {})
    tag_list = []
    if nei_code4:
        tag_name = nei_code4.get("tag_name")
        if tag_name:
            tag_list.append(tag_name)
    return tag_list


def parse_company_production_cleaning(tags):
    production_cleaning = tags.get("production_cleaning", [])
    tag_list = []
    if production_cleaning:
        for _ in production_cleaning:
            if _:
                tag_list.append(_)
    return tag_list


def parse_company_desc_tag(tags):
    desc_tag = tags.get("desc_tag", [])
    tag_list = []
    if desc_tag:
        for _ in desc_tag:
            if _:
                tag_list.append(_)
    return tag_list


def parse_company_financing_round_tag(tags):
    financing_tag = tags.get("financing_tag", [])
    tag_list = []
    if financing_tag:
        financing_round = financing_tag.get("round")
        if financing_round:
            tag_list.append(financing_round)
    return tag_list


def parse_company_market_block_tag(tags):
    market_tag = tags.get("market_tag", [])
    tag_list = []
    if market_tag:
        block = market_tag.get("block")
        if block:
            tag_list.append(block)
    return tag_list


def parse_company_market_status_tag(tags):
    market_tag = tags.get("market_tag", [])
    tag_list = []
    if market_tag:
        status = market_tag.get("status")
        if status:
            tag_list.append(status)
    return tag_list


def parse_company_association_tag(tags):
    association_tag = tags.get("association_tag", [])
    tag_list = []
    if association_tag:
        tag_name = association_tag.get("tag_name")
        if tag_name:
            tag_list.append(tag_name)
    return tag_list


def parse_company_tag(tags: dict, return_type: bool = False, tag_type_list: list = None):
    _tags = []
    tag_dict = {
        "产业标签": parse_company_industry_tag,
        "备案许可级别": parse_company_permission_level_tag,
        "备案许可名称": parse_company_permission_name_tag,
        "资质认证名称": parse_company_certification_tag,
        "奖项名称": parse_company_award_tag,
        "榜单名称": parse_company_rank_tag,
        "diy标签": parse_company_diy_tag,
        "国家级标签": parse_company_national_tag,
        "省级标签": parse_company_province_tag,
        "市级标签": parse_company_city_tag,
        "区级标签": parse_company_district_tag,
        "园区标签": parse_company_park_tag,
        "国民行业分类二位码名字": parse_company_nei_code2_tag,
        "国民行业分类三位码名字": parse_company_nei_code3_tag,
        "国民行业分类四位码名字": parse_company_nei_code4_tag,
        "产品标签": parse_company_production_cleaning,
        "描述性标签": parse_company_desc_tag,
        "融资轮次": parse_company_financing_round_tag,
        "上市板块": parse_company_market_block_tag,
        "上市状态": parse_company_market_status_tag,
        "联盟协会标签": parse_company_association_tag
    }
    if tag_type_list:
        for tag_type in tag_dict:
            if tag_type in tag_type_list and tag_type in tag_dict:
                if not return_type:
                    _tags.extend(tag_dict.get(tag_type)(tags))
                else:
                    tag_info = {
                        "tag_type": tag_type,
                        "tags": tag_dict.get(tag_type)(tags)
                    }
                    _tags.append(tag_info)
    else:
        for tag_type in tag_dict:
            if tag_type in tag_dict:
                if not return_type:
                    _tags.extend(tag_dict.get(tag_type)(tags))
                else:
                    tag_info = {
                        "tag_type": tag_type,
                        "tags": tag_dict.get(tag_type)(tags)
                    }
                    _tags.append(tag_info)
    return _tags
