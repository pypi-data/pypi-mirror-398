NestedDict = {
    "bids_deal_display_tags": {},
    "bids_deal_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "bids_deal_item_tags": {},
    "bids_deal_related_party_tags": {
        "purchaser_tags": "(id Int64, name String)",
        "supplier_tags": "(id Int64, name String)",
        "agency_tags": "(id Int64, name String)"
    },
    "bids_notice_date_tags": {},
    "bids_notice_display_tags": {},
    "bids_notice_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "bids_notice_item_tags": {},
    "bids_notice_related_party_tags": {
        "purchaser_tags": "(id Int64, name String)",
        "agency_tags": "(id Int64, name String)"
    },
    "college_desc_tags": {},
    "college_level_tags": {
        "level_tag": "(name String, level String, year UInt16, id Int32, sub_type String)"
    },
    "college_location_tags": {},
    "college_reg_park_tags": {
        "reg_park": "(tag_code UInt16, tag_name String)"
    },
    "company_abbreviation_tags": {},
    "company_address_tags": {
        "off_building": "(tag_name String, tag_code String)",
        "off_park": "(tag_name String, tag_code String)",
        "reg_building": "(tag_name String, tag_code String)",
        "reg_park": "(tag_name String, tag_code UInt16, way String)",
        "reg_township": "(tag_name String, tag_code String)"
    },
    "company_basic_tags": {},
    "company_belong_project_tags": {},
    "company_brief_tags": {},
    "company_chain_leader_tags": {
        "chain_leader_tag": "(industry_name String, industry_code String, label Array(String))"
    },
    "company_contact_tags": {
        "contact": "(contact_name String, contact_info String, type String, source String, date Nullable(Date32), link String)"
    },
    "company_desc_tags": {},
    "company_diy_tags": {},
    "company_evaluation_tags": {},
    "company_financing_tags": {
        "financing_tag": "(date Nullable(Date32), round String, amount Float32, investor Array(String), unit String)"
    },
    "company_growth_score_tags": {
        "company_growth_score": "(total_score Float32)"
    },
    "company_honor_tags": {
        "association_tag": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "award_tag": "(award_tag_code Int32, award_type String, award_rank String, level String, date Nullable(Date32), publisher String, tag_name String, year UInt16)",
        "certification": "(certification_name String, certification_code String, certification_tag_code Int32, certification_year UInt16, level String, status String, start Nullable(Date32), end Nullable(Date32), date Nullable(Date32), publisher String)",
        "city_tag": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "district_tag": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "national_tag": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "nonpublic_tags": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "park_tag": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "permission": "(permission_name String, permission_code String, permission_tag_code Int32, permission_year UInt16, level String, status String, validity_start_date String, validity_end_date String, date Nullable(Date32), publisher String, permission_production String)",
        "province_tag": "(tag_name String, tag_code Int32, tag_year String, level String, date Nullable(Date32), publisher String)",
        "rank_tag": "(rank_name String, rank_tag_code Int32, rank_year UInt16, rank_level String, rank Int32, date Nullable(Date32), publisher String)"
    },
    "company_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, children Nested(tag_code String, tag_name String, level Int8, way String))",
        "industry_tag_detail": "(tag_code String, way String, keyword String, tag_name String, children Nested(tag_code String, tag_name String, level Int8, way String))",
        "corpus": "(name String)",
        "industry_tag_old": "(tag_code String, tag_name String, way String, children Nested(tag_code String, tag_name String, level Int8, way String))"
    },
    "company_keywords_tags": {},
    "company_leader_industry_tags": {
        "leader_industry": "(tag_code String, tag_name String, count Int32, score Int32)"
    },
    "company_market_latest_tags": {
        "market_tag": "(stock_short String, stock_code String, status String, market_date Nullable(Date32), block String, block_detail String, block_std String, block_code Int32)"
    },
    "company_operating_risk_tags": {
        "operating_risk": "(risk_type String, risk_date Nullable(Date32))"
    },
    "company_potential_zjtx_tags": {
        "potential_zjtx": "(company_credit Int32, company_scale Int32, finance_predict Int32, innovation Int32, operation Int32, total_point Float32, company_scale_desc String, company_credit_desc String)"
    },
    "company_production_cleaning_tags": {},
    "company_reg_cap_change_tags": {
        "reg_cap_change": "(change_type String, change_date Nullable(Date32), change_be Float32, change_af Float32, unit String)"
    },
    "company_risk_tags": {
        "risk": "(type Enum8('NULL' = 0, '\u884c\u653f\u5904\u7f5a' = 1, '\u7ecf\u8425\u5f02\u5e38' = 2, '\u4e25\u91cd\u8fdd\u6cd5' = 3, '\u62bd\u67e5\u4e0d\u5408\u683c' = 4, '\u6ce8\u8d44\u51cf\u5c11' = 5, '\u52a8\u4ea7\u62b5\u62bc' = 6, '\u80a1\u6743\u51fa\u8d28' = 7, '\u4f01\u4e1a\u51b3\u8bae\u89e3\u6563/\u88ab\u540a\u9500\u8425\u4e1a\u6267\u7167' = 8, '\u6e05\u7b97\u7ec4\u4fe1\u606f' = 9, '\u77e5\u8bc6\u4ea7\u6743\u51fa\u8d28' = 10, '\u7b80\u6613\u6ce8\u9500\u516c\u544a' = 11, '\u5bf9\u5916\u62c5\u4fdd' = 12, '\u80a1\u6743\u8d28\u62bc' = 13), date Nullable(Date32), content String, is_history Int8)"
    },
    "company_score_tags": {},
    "company_ssf_count_tags": {},
    "company_support_project_tags": {
        "support_project_tag": "(project_name String, funding_form String, project_id String, level String, date Nullable(Date32))"
    },
    "company_tech_keywords_tags": {},
    "company_zombie_company_tags": {},
    "industry_carrier_desc_tags": {},
    "industry_carrier_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "industry_carrier_level_tags": {
        "level_tag": "(name String, level String, year UInt16, id Int32, sub_type String, type String, type_std String, publisher String)"
    },
    "industry_carrier_support_unit_tags": {
        "company": "(id Int64, support_unit String)",
        "college": "(id FixedString(24), support_unit String)",
        "person": "(id Int64, support_unit String)",
        "region": "(id Int64, support_unit String)",
        "gov": "(id Int64, support_unit String)",
        "other": "(id Int64, support_unit String)",
        "park": "(id Int32, support_unit String)"
    },
    "investment_company_tags": {
        "invest_company": "(company_id String, name String, type String)"
    },
    "investment_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "investment_investor_tags": {
        "investors": "(short_name String, ent_name String, company_id String, investor_id String)"
    },
    "investor_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "investor_invest_company_tags": {},
    "investor_reg_park_tags": {
        "reg_park": "(tag_code String, tag_name String)"
    },
    "label_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "label_publisher_type_tags": {
        "publisher_type": "(type String, sub_type String, way Int32)"
    },
    "league_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "league_location_tags": {},
    "league_reg_park_tags": {
        "reg_park": "(tag_code UInt16, tag_name String)"
    },
    "news_bank_tags": {
        "mentioned_bank": "(bank_name String, bank_type String)"
    },
    "news_basic_tags": {},
    "news_company_tags": {
        "company_id": "(code Int64, name String)"
    },
    "news_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "news_location_tags": {},
    "news_type_tags": {
        "mentioned_bank": "(bank_name String, bank_type String)"
    },
    "park_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "park_location_tags": {
        "location": "(province String, city String, district String)"
    },
    "patent_basic_tags": {},
    "patent_industry_segment_tags": {
        "industry_segment": "(industry_name String, industry_code String, segment Nested(segment String, attribute String))"
    },
    "patent_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "patent_is_high_values_tags": {},
    "patent_location_tags": {},
    "patent_prize_tags": {},
    "patent_proposer_tags": {
        "company": "(id Int64, proposer String)",
        "college": "(id FixedString(24), proposer String)",
        "person": "(id Int64, proposer String)",
        "region": "(id Int64, proposer String)",
        "gov": "(id Int64, proposer String)",
        "other": "(id Int64, proposer String)",
        "park": "(id UInt16, proposer String)"
    },
    "patent_reference_tags": {},
    "patent_reg_park_tags": {
        "reg_park": "(tag_name String, tag_code UInt16)"
    },
    "patent_score_tags": {},
    "patent_status_tags": {},
    "patent_tactic_industry_tags": {},
    "patent_tech_keyword_tags": {},
    "policy_certification_tags": {},
    "policy_content_abstract_tags": {},
    "policy_continuity_tags": {},
    "policy_declare_tags": {},
    "policy_display_tags": {},
    "policy_feature_label_tags": {},
    "policy_industry_segment_tags": {
        "industry_segment": "(industry_code String, industry_name String, segment Nested(segment String, attribute String))"
    },
    "policy_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "policy_ministry_std_tags": {},
    "policy_quote_tags": {},
    "policy_support_tags": {},
    "project_desc_tags": {},
    "project_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "project_level_tags": {
        "level_tag": "(tag_name String, tag_code Int32, year UInt16, level String, date Nullable(Date32), publisher String)"
    },
    "project_support_unit_tags": {
        "company": "(id Int64, support_unit String)",
        "college": "(id FixedString(24), support_unit String)",
        "person": "(id Int64, support_unit String)",
        "region": "(id Int64, support_unit String)",
        "gov": "(id Int64, support_unit String)",
        "other": "(id Int64, support_unit String)",
        "park": "(id UInt16, support_unit String)"
    },
    "region_code_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String)"
    },
    "research_institution_desc_tags": {},
    "research_institution_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "research_institution_level_tags": {
        "level_tag": "(name String, level String, year UInt16, id Int32, sub_type String, type String, type_std String, publisher String)"
    },
    "research_institution_location_tags": {},
    "research_institution_support_unit_tags": {
        "company": "(id Int64, support_unit String, reg_xy Point)",
        "college": "(id FixedString(24), support_unit String)",
        "person": "(id Int64, support_unit String)",
        "region": "(id Int64, support_unit String)",
        "gov": "(id Int64, support_unit String)",
        "other": "(id Int64, support_unit String)",
        "park": "(id UInt16, support_unit String)"
    },
    "security_report_basic_tags": {},
    "security_report_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "security_report_pages_tags": {},
    "security_report_value_score_tags": {},
    "standards_correlation_standards_tags": {
        "correlation_standards": "(tag_code String, tag_name String)"
    },
    "standards_drafting_unit_tags": {
        "company": "(id Int64, drafting_unit String)",
        "college": "(id FixedString(24), drafting_unit String)",
        "person": "(id Int64, drafting_unit String)",
        "region": "(id Int64, drafting_unit String)",
        "gov": "(id Int64, drafting_unit String)",
        "other": "(id Int64, drafting_unit String)",
        "park": "(id UInt16, drafting_unit String)"
    },
    "standards_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "supply_demand_relation_industry_tags": {
        "industry_tag": "(tag_code String, tag_name String, way String, method String, children Nested(tag_code String, tag_name String, way String, method String, level Int32))"
    },
    "supply_demand_relation_part_info_tags": {
        "customer_tags": "(id Int64, name String)",
        "supplier_tags": "(id Int64, name String)"
    }
}
