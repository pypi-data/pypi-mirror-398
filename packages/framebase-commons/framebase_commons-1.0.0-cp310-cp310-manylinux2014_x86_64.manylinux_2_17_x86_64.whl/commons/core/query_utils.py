# cython: annotation_typing = False
"""
查询工具函数 - Query Utilities
代码来源：chains/text2metric_chain.py（从 service/query.py 提取的工具函数）
功能说明：查询处理相关的通用工具函数，用于维度信息提取、警告消息收集、PDT时间检测等
创建日期：2024-12-19
"""
import re


def recursive_extract_dimension_info(dimension_filters: dict, dimension_info: list) -> None:
    """
    递归提取维度过滤信息为字符串列表
    
    参数:
        dimension_filters: 维度过滤字典
        dimension_info: 维度信息列表，会被原地修改
    """
    for key, filter_pairs in dimension_filters.items():
        for filter_pair in filter_pairs:
            if any(filter_pair.get(c) for c in ['must', 'should', 'must_not']):
                recursive_extract_dimension_info(filter_pair, dimension_info)
            if 'dimensionValue' in filter_pair:
                dimension_info.append(f"{filter_pair['dimensionName']} {filter_pair['operator']} {filter_pair['dimensionValue']}")
            elif 'dimensionName' in filter_pair:
                dimension_info.append(f"{filter_pair['dimensionName']} {filter_pair['operator']}")


def format_dimension_info_string(query: dict) -> str:
    """
    格式化查询中的维度过滤信息为字符串
    
    参数:
        query: 查询字典，可能包含 'dimensionFilters' 或 'rankingDimensionFilters'
    
    返回:
        格式化后的维度信息字符串
    """
    dimension_info = []
    if 'dimensionFilters' in query:  # 普通查询使用dimensionFilters
        recursive_extract_dimension_info(query['dimensionFilters'], dimension_info)
    elif 'rankingDimensionFilters' in query:  # 排序查询使用rankingDimensionFilters
        recursive_extract_dimension_info(query['rankingDimensionFilters'], dimension_info)
    dimension_info_str = '\n'.join(dimension_info)
    if dimension_info_str:
        dimension_info_str += '在回答问题时，向用户介绍当前的查询结果是基于以上的维度过滤条件得到的。'
    return dimension_info_str


def get_prompt_name_by_result_length(result_data_length: int, reject_threshold: int) -> str:
    """
    根据结果数据长度获取提示模板名称
    
    参数:
        result_data_length: 结果数据行数
        reject_threshold: 拒绝阈值
    
    返回:
        提示模板名称
    """
    if result_data_length == 0:
        return "metric_query_reject_answer_template"
    elif result_data_length < reject_threshold:
        return 'metric_query_answer_template'
    else:
        return 'metric_query_reject_answer_template'


def collect_warning_messages(
    warning_mode: str,
    metric_pick: dict,
    warnings: dict,
    Metric_Low_Relevance_Message: str,
    Metric_No_Dimension_Message: str,
    Metric_No_Dimension_Details_Message: str,
) -> list:
    """
    根据警告模式收集警告消息
    
    参数:
        warning_mode: 警告模式 ('only_abnormal_metric_message', 'abnormal_metric_and_dimension_message', 'abnormal_metric_and_dimension_details')
        metric_pick: 指标选择字典
        warnings: 警告字典，包含 'time_warning' 和 'dimension_warning'
        Metric_Low_Relevance_Message: 低相关性消息
        Metric_No_Dimension_Message: 无维度消息
        Metric_No_Dimension_Details_Message: 无维度详情消息模板
    
    返回:
        警告消息列表
    """
    warning_message = []
    
    if warning_mode == 'only_abnormal_metric_message':
        if metric_pick and not metric_pick.get('mentioned_metric', []):
            warning_message.append(Metric_Low_Relevance_Message)
        if warnings.get('time_warning', []):
            warning_message.extend(warnings.get('time_warning', []))
    
    elif warning_mode == 'abnormal_metric_and_dimension_message':
        if metric_pick and not metric_pick.get('mentioned_metric', []):
            warning_message.append(Metric_Low_Relevance_Message)
        if warnings.get('time_warning', []):
            warning_message.extend(warnings.get('time_warning', []))
        if warnings.get('dimension_warning', []):
            warning_message.append(Metric_No_Dimension_Message)
    
    elif warning_mode == 'abnormal_metric_and_dimension_details':
        if metric_pick and not metric_pick.get('mentioned_metric', []):
            warning_message.append(Metric_Low_Relevance_Message)
        if warnings.get('time_warning', []):
            warning_message.extend(warnings.get('time_warning', []))
        if warnings.get('dimension_warning', []):
            warning_message.append(Metric_No_Dimension_Details_Message.format(details=warnings.get('dimension_warning', [])))
    
    return warning_message


def extract_metric_candidates(
    metric_pick: dict,
    raw_metric_info: list,
    is_multi_mode: bool,
) -> list:
    """
    提取指标候选列表
    
    参数:
        metric_pick: 指标选择字典
        raw_metric_info: 原始指标信息列表
        is_multi_mode: 是否多指标模式
    
    返回:
        指标候选名称列表
    """
    metric_candidates = []
    
    if not is_multi_mode:
        mentioned_metric = metric_pick.get('mentioned_metric', [])
        if len(mentioned_metric) > 1:
            metric_candidates.extend(
                raw_metric_info[int(i)].metadata['page_content'] 
                for i in mentioned_metric[1:]
            )
    
    related_metric = metric_pick.get('related_metric', [])
    for i, j in enumerate(related_metric):
        if not metric_pick.get('mentioned_metric') and i == 0:
            continue
        else:
            metric_candidates.append(raw_metric_info[int(j)].metadata['page_content'])
    
    return metric_candidates

