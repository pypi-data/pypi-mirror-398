# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第1617-1623行（combine_rewrite）、第2063-2379行（make_metric_query）
功能说明：查询构建器 - 包含查询构建主逻辑、时间处理、比较构建、分组处理
重构日期：2024-12-19
"""
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from langchain_core.runnables import (
    RunnablePassthrough,
    chain as chain_decorator,
)
from framebase.values import RunnableValue

from commons.core.infrastructure import (
    replace_operator,
    is_multi_app_id,
)
from commons.core.dimension_utils import (
    check_dimension_holds,
    check_dimension_filters,
)
from commons.core.time_utils import (
    strptime,
    convert_date_format,
    time2str,
    check_aggregation,
    check_date,
    check_sorting,
    check_limit,
    reset_date_by_time_filters,
)
from commons.core.query_builder_utils import (
    organize_time_intent_keys,
    build_metric_query_dict,
    extract_dimension_info,
    validate_and_optimize_time_filters,
    collect_warnings,
    group_queries_by_dimension,
)
from app.admin_operation import get_global_config_info
from utils.logger import logger

# 代码来源：text2metric_chain.py（原第1423行）
metric_type = {'原子指标': 0, '派生指标': 1, '复合指标': 2}

# ==================== 组合重写 ====================
# 代码来源：text2metric_chain.py（原第1617-1623行）
@chain_decorator
def combine_rewrite(x):
    """
    组合重写，提取指标并重写问题
    
    从router_json中提取指标名称，与问题组合为queries列表
    """
    logger.info(f"metric extract from question:{x.get('router_json', {}).get('metric')}")
    if x.get('router_json', {}).get('metric'):
        return RunnablePassthrough.assign(queries=RunnableValue(values=[*x.get('router_json', {}).get('metric', []), x.get('question')]))
    else:
        return RunnablePassthrough()

# ==================== 构建指标查询 ====================
# 代码来源：text2metric_chain.py（原第2063-2379行）
async def make_metric_query(x):
    """
    构建指标查询的主要函数
    
    处理时间比较、时间过滤器、维度信息，构建完整的metric_query列表
    """
    passthrough = x['passthrough']
    metric_query = []
    metric_query_metadata = []

    organize_time_intent_keys(x['time_intent'])  # 整理时间意图的键值结构
    
    time_warning = defaultdict(list)
    # 处理时间比较：如果存在比较需求，需要重置time_filters
    for metric_id in x['time_intent']['comparisons']:
        metric_info = list(filter(lambda m: m['metricId'] == metric_id, passthrough['metric_infos']))[0]
        fixed_date_comparisons = []
        period_comparisons = []
        for item in x['time_intent']['comparisons'][metric_id].get('timeComparisons', []):
            result = {}
            if item.get('t1') and item.get('t2'):
                result['comparisonType'] = 'fixedDate'
                if not result.get('sourceDataDate'):
                    result['sourceDataDate'] = []
                result['sourceDataDate'].append(item['t1'])
                if not result.get('targetDataDate'):
                    result['targetDataDate'] = []
                result['targetDataDate'].append(item['t2'])
                fixed_date_comparisons.append(result)
            elif item.get('periodUnit') and item.get('periodQuantity'):
                result['comparisonType'] = 'period'
                result['comparisonInterval'] = item['periodQuantity']
                result['comparisonTimeUnit'] = item['periodUnit']
                if item.get('t'):
                    result['time_filters'] = [item.get('t')]
                    result['t'] = item.get('t')
                else:
                    result['time_filters'] = []
                period_comparisons.append(result)
        if len(period_comparisons) > 1:
            x['time_intent']['comparisons'][metric_id] = {}
            comparisons_time_filters = []
            for item in period_comparisons:
                if item.get('t'):
                    date = strptime(item['t'], metric_info['time_interval'])
                    if item['comparisonInterval'] == 'YEAR':
                        date = date - relativedelta(years=item['comparisonTimeUnit'])
                    elif item['comparisonInterval'] == 'MONTH':
                        date = date - relativedelta(months=item['comparisonTimeUnit'])
                    elif item['comparisonInterval'] == 'DAY':
                        date = date - relativedelta(days=item['comparisonTimeUnit'])
                    comparisons_time_filters.append(time2str(date, metric_info['time_interval']))
            if comparisons_time_filters:
                x['time_intent']['time_filters'][metric_id] = comparisons_time_filters
        elif len(fixed_date_comparisons) > 1:
            x['time_intent']['comparisons'][metric_id] = fixed_date_comparisons[0]
            x['time_intent']['time_filters'][metric_id] = [*fixed_date_comparisons[0]['sourceDataDate'], *fixed_date_comparisons[0]['targetDataDate']]
            for item in fixed_date_comparisons[1:]:
                for date in item['sourceDataDate']:
                    x['time_intent']['time_filters'][metric_id].append(date)
                    x['time_intent']['comparisons'][metric_id]['sourceDataDate'].append(date)
                for date in item['targetDataDate']:
                    x['time_intent']['time_filters'][metric_id].append(date)
                    x['time_intent']['comparisons'][metric_id]['targetDataDate'].append(date)
            x['time_intent']['comparisons'][metric_id]['sourceDataDate'] = sorted(list(set(x['time_intent']['comparisons'][metric_id]['sourceDataDate'])))
            x['time_intent']['comparisons'][metric_id]['targetDataDate'] = sorted(list(set(x['time_intent']['comparisons'][metric_id]['targetDataDate'])))
        elif len(fixed_date_comparisons):
            x['time_intent']['time_filters'][metric_id] = []
            x['time_intent']['time_filters'][metric_id].append(time2str(strptime(fixed_date_comparisons[0]['sourceDataDate'][0], metric_info['time_interval']), metric_info['time_interval']))
            x['time_intent']['time_filters'][metric_id].append(time2str(strptime(fixed_date_comparisons[0]['targetDataDate'][0], metric_info['time_interval']), metric_info['time_interval']))
            x['time_intent']['comparisons'][metric_id] = fixed_date_comparisons[0]
        elif len(period_comparisons):
            if period_comparisons[0].get('t'):
                x['time_intent']['time_filters'][metric_id] = []
            x['time_intent']['comparisons'][metric_id] = period_comparisons[0]
        else:
            x['time_intent']['comparisons'][metric_id] = {}
        
        if x['time_intent']['time_records'][metric_id]:
            latest_record = x['time_intent']['time_records'][metric_id][-1]
        else:
            latest_record = time2str(datetime.now(), metric_info['time_interval'])

        if x['time_intent']['comparisons'][metric_id].get('comparisonType') == 'fixedDate':
            for i, date in enumerate(x['time_intent']['comparisons'][metric_id]['sourceDataDate']):
                if date not in x['time_intent']['time_records'][metric_id] and x['time_intent']['time_records'][metric_id] and \
                    (get_global_config_info('metric_time_records_mapping_mode') == 'adaptive' or not get_global_config_info('metric_time_records_mapping_mode')):
                    if strptime(date, metric_info['time_interval']) > strptime(latest_record, metric_info['time_interval']) and not metric_info['is_accumulative']:
                        x['time_intent']['time_filters'][metric_id].append(latest_record)
                        x['time_intent']['comparisons'][metric_id]['sourceDataDate'][i] = latest_record
                        time_warning[metric_id].append({'miss': date, 'replace': latest_record, 'msg': f'{metric_info["name"]}缺少{date}的数据，已替换数据库中最新的日期：{latest_record}'})
                    elif strptime(date, metric_info['time_interval']) < strptime(x['time_intent']['time_records'][metric_id][0], metric_info['time_interval']):
                        x['time_intent']['time_filters'][metric_id].append(x['time_intent']['time_records'][metric_id][0])
                        time_warning[metric_id].append({'miss': date, 'replace': x["time_intent"]["time_records"][metric_id][0], 'msg': f'{metric_info["name"]}缺少{date}的数据，已替换数据库中最早的日期：{x["time_intent"]["time_records"][metric_id][0]}'})
                    else:
                        x['time_intent']['time_filters'][metric_id].append(date)
                        x['time_intent']['comparisons'][metric_id]['sourceDataDate'][i] = date
                else:
                    x['time_intent']['time_filters'][metric_id].append(date)
            for i, date in enumerate(x['time_intent']['comparisons'][metric_id]['targetDataDate']):
                if date not in x['time_intent']['time_records'][metric_id] and x['time_intent']['time_records'][metric_id] and \
                    (get_global_config_info('metric_time_records_mapping_mode') == 'adaptive' or not get_global_config_info('metric_time_records_mapping_mode')):
                    if strptime(date, metric_info['time_interval']) > strptime(latest_record, metric_info['time_interval']) and not metric_info['is_accumulative']:
                        x['time_intent']['time_filters'][metric_id].append(latest_record)
                        x['time_intent']['comparisons'][metric_id]['targetDataDate'][i] = latest_record
                        time_warning[metric_id].append({'miss': date, 'replace': latest_record, 'msg': f'{metric_info["name"]}缺少{date}的数据，已替换数据库中最新的日期：{latest_record}'})
                    elif strptime(date, metric_info['time_interval']) < strptime(x['time_intent']['time_records'][metric_id][0], metric_info['time_interval']):
                        x['time_intent']['time_filters'][metric_id].append(x['time_intent']['time_records'][metric_id][0])
                        x['time_intent']['comparisons'][metric_id]['targetDataDate'][i] = x['time_intent']['time_records'][metric_id][0]
                        time_warning[metric_id].append({'miss': date, 'replace': x["time_intent"]["time_records"][metric_id][0], 'msg': f'{metric_info["name"]}缺少{date}的数据，已替换数据库中最早的日期：{x["time_intent"]["time_records"][metric_id][0]}'})
                    else:
                        x['time_intent']['time_filters'][metric_id].append(date)
                        x['time_intent']['comparisons'][metric_id]['targetDataDate'][i] = date
                else:
                    x['time_intent']['time_filters'][metric_id].append(date)
            x['time_intent']['comparisons'][metric_id]['targetDataDate'] = sorted(list(set(x['time_intent']['comparisons'][metric_id]['targetDataDate'])))
            x['time_intent']['comparisons'][metric_id]['sourceDataDate'] = sorted(list(set(x['time_intent']['comparisons'][metric_id]['sourceDataDate'])))
            if len(x['time_intent']['comparisons'][metric_id]['targetDataDate']) > 1 and len(x['time_intent']['comparisons'][metric_id]['sourceDataDate']) > 1:
                x['time_intent']['time_filters'][metric_id].extend(x['time_intent']['comparisons'][metric_id]['targetDataDate'])
                x['time_intent']['time_filters'][metric_id].extend(x['time_intent']['comparisons'][metric_id]['sourceDataDate'])
                x['time_intent']['comparisons'][metric_id] = {}
            if x['time_intent']['comparisons'][metric_id] and len(x['time_intent']['comparisons'][metric_id]['targetDataDate']) == 1 and len(x['time_intent']['comparisons'][metric_id]['sourceDataDate']) == 1:
                if x['time_intent']['comparisons'][metric_id]['targetDataDate'][0] == x['time_intent']['comparisons'][metric_id]['sourceDataDate'][0]:
                    x['time_intent']['comparisons'][metric_id] = {}

        if x['time_intent']['comparisons'][metric_id].get('comparisonType') == 'period':
            for date in x['time_intent']['comparisons'][metric_id]['time_filters']:
                if date not in x['time_intent']['time_filters'][metric_id] and x['time_intent']['time_records'][metric_id] and \
                    (get_global_config_info('metric_time_records_mapping_mode') == 'adaptive' or not get_global_config_info('metric_time_records_mapping_mode')):
                    if strptime(date, metric_info['time_interval']) > strptime(latest_record, metric_info['time_interval']) and not metric_info['is_accumulative']:
                        x['time_intent']['time_filters'][metric_id].append(latest_record)
                        time_warning[metric_id].append({'miss': date, 'replace': latest_record, 'msg': f'{metric_info["name"]}缺少{date}的数据，已替换数据库中最新的日期：{latest_record}'})
                    elif strptime(date, metric_info['time_interval']) < strptime(x['time_intent']['time_records'][metric_id][0], metric_info['time_interval']):
                        x['time_intent']['time_filters'][metric_id].append(x['time_intent']['time_records'][metric_id][0])
                        time_warning[metric_id].append({'miss': date, 'replace': x["time_intent"]["time_records"][metric_id][0], 'msg': f'{metric_info["name"]}缺少{date}的数据，已替换数据库中最早的日期：{x["time_intent"]["time_records"][metric_id][0]}'})
                    else:
                        x['time_intent']['time_filters'][metric_id].append(date)
                else:
                    x['time_intent']['time_filters'][metric_id].append(date)
            x['time_intent']['comparisons'][metric_id].pop('time_filters')
        if x['time_intent']['time_filters'].get(metric_id):
            x['time_intent']['time_filters'][metric_id] = sorted(list(set(x['time_intent']['time_filters'][metric_id])))

    if get_global_config_info('metric_time_records_mapping_mode') == 'adaptive' or not get_global_config_info('metric_time_records_mapping_mode'):
        for metric_id in x['time_intent']['time_filters']:
            metric_info = list(filter(lambda m: m['metricId'] == metric_id, passthrough['metric_infos']))[0]
            if x['time_intent']['time_records'][metric_id]:
                if not x['time_intent']['time_filters'][metric_id]:
                    x['time_intent']['time_filters'][metric_id].append(x['time_intent']['time_records'][metric_id][-1])
                    if convert_date_format(x['time_intent']['startDate'][metric_id], x['time_intent']['windowDate'][metric_id]) == convert_date_format(x['time_intent']['endDate'][metric_id], x['time_intent']['windowDate'][metric_id]):
                        miss = convert_date_format(x['time_intent']['startDate'][metric_id], x['time_intent']['windowDate'][metric_id])
                        replace = x['time_intent']['time_records'][metric_id][-1]
                        time_warning[metric_id].append({'miss': miss, 'replace': replace, 'msg': f'{metric_info["name"]}缺少{miss}的数据，已替换数据库中最新的日期：{replace}'})
                    else:
                        miss = f"{convert_date_format(x['time_intent']['startDate'][metric_id], x['time_intent']['windowDate'][metric_id])},{convert_date_format(x['time_intent']['endDate'][metric_id], x['time_intent']['windowDate'][metric_id])}"
                        replace = x['time_intent']['time_records'][metric_id][-1]
                        time_warning[metric_id].append({'miss': miss, 'replace': replace, 'msg': f'{metric_info["name"]}缺少{miss}的数据，已替换数据库中最新的日期：{replace}'})
                for date in x['time_intent']['time_filters'][metric_id]:
                    if date not in x['time_intent']['time_records'][metric_id]:
                        x['time_intent']['time_filters'][metric_id].remove(date)
                        if strptime(date, metric_info['time_interval']) > strptime(x['time_intent']['time_records'][metric_id][-1], metric_info['time_interval']) and not metric_info['is_accumulative']:
                            x['time_intent']['time_filters'][metric_id].append(x['time_intent']['time_records'][metric_id][-1])
                            miss = convert_date_format(date, x['time_intent']['windowDate'][metric_id])
                            replace = x['time_intent']['time_records'][metric_id][-1]
                            time_warning[metric_id].append({'miss': miss, 'replace': replace, 'msg': f'{metric_info["name"]}缺少{miss}的数据，已替换数据库中最新的日期：{replace}'})
                        elif strptime(date, metric_info['time_interval']) < strptime(x['time_intent']['time_records'][metric_id][0], metric_info['time_interval']):
                            x['time_intent']['time_filters'][metric_id].append(x['time_intent']['time_records'][metric_id][0])
                            miss = convert_date_format(date, x['time_intent']['windowDate'][metric_id])
                            replace = x['time_intent']['time_records'][metric_id][0]
                            time_warning[metric_id].append({'miss': miss, 'replace': replace, 'msg': f'{metric_info["name"]}缺少{miss}的数据，已替换数据库中最早的日期：{replace}'})
            else:
                time_warning[metric_id].append({'miss': '', 'msg': f'{metric_info["name"]}缺少数据。'})
    elif get_global_config_info('metric_time_records_mapping_mode') == 'fixed':
        pass
    for i, metric_id in enumerate(x['dimension_intent']):
        time_warning[metric_id].extend(x['time_intent']['time_warning'])
        metric_info = list(filter(lambda m: m['metricId'] == metric_id, passthrough['metric_infos']))[0]
        if x['time_intent']['time_filters'].get(metric_id):
            time_filters_1 = strptime(x['time_intent']['time_filters'][metric_id][-1], metric_info['time_interval'], end=True)
            time_filters_0 = strptime(x['time_intent']['time_filters'][metric_id][0], metric_info['time_interval'])
            date_1 = strptime(x['time_intent']['endDate'][metric_id], x['time_intent']['windowDate'][metric_id], end=True)
            date_0 = strptime(x['time_intent']['startDate'][metric_id], x['time_intent']['windowDate'][metric_id])
            if 0 < (date_1 - time_filters_1).days < 1 and 0 < (date_0 - time_filters_0).days < 1:
                if metric_info['time_interval'] == 'DAY' and (time_filters_1 - time_filters_0).days == len(x['time_intent']['time_filters'][metric_id]) - 1:
                    x['time_intent']['time_filters'][metric_id] = []
                elif metric_info['time_interval'] == 'MONTH' and (time_filters_1.year - time_filters_0.year) * 12 + (time_filters_1.month - time_filters_0.month) == len(x['time_intent']['time_filters'][metric_id]) - 1:
                    x['time_intent']['time_filters'][metric_id] = []
                elif metric_info['time_interval'] == 'YEAR' and time_filters_1.year - time_filters_0.year == len(x['time_intent']['time_filters'][metric_id]) - 1:
                    x['time_intent']['time_filters'][metric_id] = []
        warnings = collect_warnings(time_warning, x['dimension_intent'], metric_id)
       
        query = build_metric_query_dict(
            metric_id,
            metric_info,
            x['time_intent'],
            x['dimension_intent'],
            x['additional_intent'],
            metric_type,
        )
        query['warnings'] = warnings
        
        dimension_names, dimension_kvs, dimension_defaults, mandatory_dimension = extract_dimension_info(metric_info)
        query = check_aggregation(query)
        query = check_dimension_holds(query, dimension_names, mandatory_dimension)
        query = check_date(query)
        query = check_dimension_filters(query, dimension_kvs, dimension_defaults)
        query = check_sorting(query)
        query = check_limit(query)
        query = reset_date_by_time_filters(query, x['time_intent']['time_records'][metric_id])
        validate_and_optimize_time_filters(query, metric_info, strptime, metric_type)
        if passthrough['intent'] == 'rank':
            query['rankingDimensionFilters'] = query.pop('dimensionFilters')
            query.pop('limit')
            query.pop('offset')
            query.pop('comparisons')
        metric_query.append(query)

    groups = group_queries_by_dimension(metric_query)
    
    metric_query = []
    app_id = passthrough.get('app_id')
    is_multi_mode = passthrough.get('metric_pick_mode') == 'multiple' or (app_id and is_multi_app_id(app_id))
    if any(m['selected'] for group in groups for m in group) and is_multi_mode:
        _groups = []
        orphan_query = []
        for i, group in enumerate(groups):
            if selected := [m for m in group if m['selected']]:
                metric_query_base = deepcopy(selected[0])
                metric_query_base['metricIdList'] = [m['metricId'] for m in group if m['selected']]
                metric_query_base['metricNameList'] = [m['metricName'] for m in group if m['selected']]
                metric_query_base.pop('metricId')
                metric_query_base.pop('metricName')
                metric_query_metadata.append({"type": "checkbox"})
                metric_query.append(metric_query_base)
                _groups.append(group)
            else:
                orphan_query += group

    else:
        _groups = [[item for group in groups for item in group]]
        if any(m['selected'] for m in _groups[0]):
            selected_metric = list(filter(lambda x: x['selected'], _groups[0]))[0]
            for m in _groups[0]:
                m['selected'] = False
            selected_metric['selected'] = True
            metric_query_base = deepcopy(selected_metric)
        else:
            _groups[0][0]['selected'] = True
            metric_query_base = deepcopy(_groups[0][0])
        metric_query_base['metricIdList'] = [metric_query_base['metricId']]
        metric_query_base['metricNameList'] = [metric_query_base['metricName']]
        metric_query_base.pop('metricId')
        metric_query_base.pop('metricName')
        metric_query_metadata.append({"type": "radio"})
        metric_query.append(metric_query_base)

    metric_intents = deepcopy(_groups)
    for i, group in enumerate(metric_intents):
        for intent in group:
            intent['request_index'] = i + 1
            metric = list(filter(lambda x: x['metricId'] == intent['metricId'], passthrough['metric_infos']))[0]
            valid_associated_dimension = list(filter(lambda x: x['name'] and any(x['values']), metric['associated_dimension']))
            intent['dimensionHoldsOptions'] = [dimension['name'] for dimension in valid_associated_dimension]
            intent['dimensionfilterOptions'] = {
                'dimensionNameOptions': intent['dimensionHoldsOptions'],
                'dimensionValueOptions': {name: (list(filter(lambda m: m['name'] == name, metric['associated_dimension'])) or [{'values': None}])[0]['values'] for name in intent['dimensionHoldsOptions']}
            }
    for i, query in enumerate(metric_query):
        metric_query[i] = replace_operator(query)
        metric_query[i]['request_index'] = i + 1

    passthrough['metric_query'] = metric_query
    passthrough['metric_query_metadata'] = metric_query_metadata
    passthrough['metric_intents'] = metric_intents
    return passthrough

