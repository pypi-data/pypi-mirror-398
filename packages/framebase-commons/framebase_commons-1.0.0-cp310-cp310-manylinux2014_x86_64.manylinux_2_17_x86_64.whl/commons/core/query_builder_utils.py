# cython: annotation_typing = False
"""
查询构建器工具函数 - Query Builder Utilities
代码来源：chains/text2metric_chain.py（从 service/query_builder.py 提取的工具函数）
功能说明：查询构建相关的通用工具函数，用于时间意图组织、查询对象构建、维度信息提取等
创建日期：2024-12-19
"""
from collections import defaultdict


def organize_time_intent_keys(time_intent: dict) -> None:
    """
    组织时间意图的键，将带前缀的键（如 'comparisons_xxx', 'time_filters_xxx'）组织成字典结构
    
    参数:
        time_intent: 时间意图字典，会被原地修改
    """
    time_intent['comparisons'] = {}
    time_intent['time_filters'] = {}
    # 将分散的comparisons_xxx和time_filters_xxx键组织成字典结构
    for k, v in time_intent.items():
        if k.startswith('comparisons_'):
            metric_id = k.split('_')[-1]  # 提取metric_id
            time_intent['comparisons'][metric_id] = v
        elif k.startswith('time_filters_'):
            metric_id = k.split('_')[-1]
            time_intent['time_filters'][metric_id] = v


def build_metric_query_dict(
    metric_id: str,
    metric_info: dict,
    time_intent: dict,
    dimension_intent: dict,
    additional_intent: dict,
    metric_type_mapping: dict,
) -> dict:
    """
    构建指标查询字典
    
    参数:
        metric_id: 指标ID
        metric_info: 指标信息字典
        time_intent: 时间意图字典
        dimension_intent: 维度意图字典
        additional_intent: 额外意图字典
        metric_type_mapping: 指标类型映射字典
    
    返回:
        指标查询字典
    """
    warnings = defaultdict(list)
    
    query = {
        "metricId": metric_id,
        "metricName": metric_info['name'],
        "metricType": metric_type_mapping[metric_info['type']],
        "is_accumulative": metric_info['is_accumulative'],
        'is_point_metric': metric_info['is_point_metric'],
        "time_interval": metric_info['time_interval'],
        "selected": metric_info['selected'],
        "unit": metric_info['unit'],
        "startDate": time_intent['startDate'][metric_id],
        "endDate": time_intent['endDate'][metric_id],
        "windowDate": time_intent['windowDate'][metric_id],
        "timeFilters": time_intent['time_filters'].get(metric_id, []),
        "comparisons": time_intent['comparisons'].get(metric_id, {}),
        "dimensionHolds": dimension_intent[metric_id].get('dimensionHolds', []),
        "dimensionFilters": dimension_intent[metric_id].get('dimensionFilters', {}),
        "warnings": warnings,
        "aggregation": additional_intent[metric_id].get('aggregation') or 'NONE',
        "sorting": additional_intent[metric_id].get('sorting'),
        "metricValueFilters": additional_intent[metric_id].get('metricValueFilters', {}),
        "limit": additional_intent[metric_id].get('limit', 100000) or 100000,
        "offset": additional_intent[metric_id].get('offset', 0) or 0,
        "type": "metric_query",
    }
    return query


def extract_dimension_info(metric_info: dict) -> tuple:
    """
    从指标信息中提取维度相关信息
    
    参数:
        metric_info: 指标信息字典
    
    返回:
        (dimension_names, dimension_kvs, dimension_defaults, mandatory_dimension) 元组
    """
    dimension_names = [m['name'] for m in metric_info['associated_dimension']]
    dimension_kvs = {m['name']: m['values'] for m in metric_info['associated_dimension']}
    dimension_defaults = {m['name']: m.get('defaultValue') for m in metric_info['associated_dimension'] if m.get('defaultValue')}
    mandatory_dimension = [m['name'] for m in metric_info['associated_dimension'] if m.get('dimMandatory')]
    return dimension_names, dimension_kvs, dimension_defaults, mandatory_dimension


def validate_and_optimize_time_filters(query: dict, metric_info: dict, strptime_func, metric_type_mapping: dict) -> None:
    """
    验证和优化时间过滤器，如果时间过滤器覆盖完整时间范围，则清空
    
    参数:
        query: 查询字典，会被原地修改
        metric_info: 指标信息字典
        strptime_func: 时间解析函数
        metric_type_mapping: 指标类型映射字典（未使用，保留以保持接口一致性）
    """
    if not query.get('timeFilters'):
        return
    
    time_filters_1 = strptime_func(query['timeFilters'][-1], metric_info['time_interval'], end=True)
    time_filters_0 = strptime_func(query['timeFilters'][0], metric_info['time_interval'])
    
    if query['time_interval'] == 'DAY' and (time_filters_1 - time_filters_0).days == len(query['timeFilters']) - 1:
        query['timeFilters'] = []
    elif query['time_interval'] == 'MONTH' and (time_filters_1.year - time_filters_0.year) * 12 + (time_filters_1.month - time_filters_0.month) == len(query['timeFilters']) - 1:
        query['timeFilters'] = []
    elif query['time_interval'] == 'YEAR' and time_filters_1.year - time_filters_0.year == len(query['timeFilters']) - 1:
        query['timeFilters'] = []


def collect_warnings(time_warning: dict, dimension_intent: dict, metric_id: str) -> dict:
    """
    收集时间警告和维度警告
    
    参数:
        time_warning: 时间警告字典
        dimension_intent: 维度意图字典
        metric_id: 指标ID
    
    返回:
        警告字典，包含 'time_warning' 和 'dimension_warning'
    """
    warnings = defaultdict(list)
    time_warning[metric_id] = list(set([m['msg'] for m in time_warning[metric_id]]))
    for warning in time_warning[metric_id]:
        warnings['time_warning'].append(warning)
    if dimension_intent[metric_id].get('invalidDimensions', []):
        warnings['dimension_warning'].append(dimension_intent[metric_id]['invalidDimensions'])
    return warnings


def group_queries_by_dimension(metric_query: list) -> list:
    """
    按维度分组查询，有comparisons的查询单独成组，其他查询按dimensionHolds、unit、is_accumulative分组
    
    参数:
        metric_query: 查询列表
    
    返回:
        分组后的查询列表，每个元素是一个查询组
    """
    from itertools import groupby
    
    groups = []
    need_groupby = []
    for query in metric_query:
        if query.get('comparisons'):
            groups.append([query])
        else:
            need_groupby.append(query)
    need_groupby = sorted(need_groupby, key=lambda x: x['dimensionHolds'] + [x['unit']] + [x['is_accumulative']])
    for _key, _group in groupby(need_groupby, key=lambda x: x['dimensionHolds'] + [x['unit']] + [x['is_accumulative']]):
        groups.append(list(_group))
    return groups

