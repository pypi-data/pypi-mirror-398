# cython: annotation_typing = False
"""
分析工具函数 - Analysis Utilities
代码来源：chains/text2metric_chain.py（从 service/analysis.py 提取的工具函数）
功能说明：分析相关的通用工具函数，用于错误处理、权限消息选择、数据处理等
创建日期：2024-12-19
"""
import os
from copy import deepcopy
import pandas as pd
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableGenerator,
)
from framebase.values import RunnableValue

from .infrastructure import (
    Metric_Permission_Denied_Message,
    HSJ_Metric_Permission_Denied_Message,
    Metric_Dimension_Permission_Denied_Message,
    HSJ_Metric_Dimension_Permission_Denied_Message,
    Metric_Analysis_Error_Message,
    data_format,
)
from utils.dbs import set_thought
from utils.logger import logger

# ==================== 常量定义 ====================
METRIC_TYPE = {'原子指标': 0, '派生指标': 1, '复合指标': 2}


def get_permission_message(app_id: str, error_type: str = 'SYS403') -> str:
    """
    根据 app_id 和错误类型返回正确的权限消息
    
    参数:
        app_id: 应用ID
        error_type: 错误类型，'SYS403' 表示系统权限错误，'DIM403' 表示维度权限错误
    
    返回:
        权限拒绝消息字符串
    """
    is_hsj_app = str(app_id) == str(os.environ.get('HSJ_Message_app_id'))
    
    if error_type == 'DIM403':
        return HSJ_Metric_Dimension_Permission_Denied_Message if is_hsj_app else Metric_Dimension_Permission_Denied_Message
    else:  # SYS403
        return HSJ_Metric_Permission_Denied_Message if is_hsj_app else Metric_Permission_Denied_Message


def create_error_branch(
    result: dict,
    analysis_type: str,
    stream_process: callable,
    gi: int,
    session_id: str,
    error_message: str
) -> RunnablePassthrough:
    """
    创建分析错误处理分支
    
    参数:
        result: API返回的结果字典
        analysis_type: 分析类型（如 'dimension', 'metric-link-analysis', 'lineage-analysis'）
        stream_process: 流式处理函数
        gi: 分组索引
        session_id: 会话ID
        error_message: 错误消息
    
    返回:
        RunnablePassthrough 链用于错误处理
    """
    return RunnablePassthrough.assign(
        set_thought=lambda x, v=result, w=analysis_type: set_thought(session_id, f'{w}_{gi}', v)
    ) | RunnablePassthrough.assign(
        placeholder=RunnableValue(value=error_message) | RunnableGenerator(stream_process).with_config(
            config={'metadata': {'index': gi}}
        )
    )


def handle_analysis_error_response(
    result: dict,
    analysis_type: str,
    stream_process: callable,
    gi: int,
    session_id: str,
    app_id: str,
    metric_query: dict = None
) -> RunnablePassthrough | None:
    """
    统一处理分析服务的错误响应
    
    参数:
        result: API返回的结果字典
        analysis_type: 分析类型（如 'dimension', 'metric-link-analysis', 'lineage-analysis'）
        stream_process: 流式处理函数
        gi: 分组索引
        session_id: 会话ID
        app_id: 应用ID
        metric_query: 指标查询字典（可选，用于日志）
    
    返回:
        如果存在错误，返回错误处理分支；否则返回 None
    """
    code = str(result.get('code', ''))
    
    # 处理 400 错误
    if code == '400':
        log_msg = f'{analysis_type} result 400'
        if metric_query:
            logger.warning(f'{log_msg}: {metric_query}\n\t\t\t{result}')
        else:
            logger.warning(f'{log_msg}: {result}')
        return create_error_branch(
            result, analysis_type, stream_process, gi, session_id, result.get('message', '请求参数错误')
        )
    
    # 处理 SYS403 错误（系统权限被拒绝）
    elif code == 'SYS403':
        log_msg = f'{analysis_type} result 403'
        if metric_query:
            logger.warning(f'{log_msg}: {metric_query}\n\t\t\t{result}')
        else:
            logger.warning(f'{log_msg}: {result}')
        perm_message = get_permission_message(app_id, 'SYS403')
        return create_error_branch(
            result, analysis_type, stream_process, gi, session_id, perm_message
        )
    
    # 处理 DIM403 错误（维度权限被拒绝）
    elif code == 'DIM403':
        log_msg = f'{analysis_type} result 403'
        if metric_query:
            logger.warning(f'{log_msg}: {metric_query}\n\t\t\t{result}')
        else:
            logger.warning(f'{log_msg}: {result}')
        dim_message = get_permission_message(app_id, 'DIM403')
        return create_error_branch(
            result, analysis_type, stream_process, gi, session_id, dim_message
        )
    
    # 处理其他非 200 错误
    elif code != '200':
        logger.error(f'metric analysis response error:{result}')
        if analysis_type == 'dimension':
            set_thought(session_id, f'dimension-description_{gi}', {
                'chunk': Metric_Analysis_Error_Message,
                'end': True
            })
        return None
    
    # 成功响应，返回 None
    return None


def create_no_data_branch(
    result: dict,
    analysis_type: str,
    stream_process: callable,
    gi: int,
    session_id: str
) -> RunnablePassthrough:
    """
    创建"暂无数据"处理分支
    
    参数:
        result: API返回的结果字典
        analysis_type: 分析类型（如 'dimension', 'metric-link-analysis', 'lineage-analysis'）
        stream_process: 流式处理函数
        gi: 分组索引
        session_id: 会话ID
    
    返回:
        RunnablePassthrough 链用于"暂无数据"处理
    """
    return RunnablePassthrough.assign(
        set_thought=lambda x, v=result, w=analysis_type: set_thought(session_id, f'{w}_{gi}', v)
    ) | RunnablePassthrough.assign(
        placeholder=RunnableValue(value='暂无数据。') | RunnableGenerator(stream_process).with_config(
            config={'metadata': {'index': gi}}
        )
    )


def format_invalid_dimension_info(invalid_dimensions: list) -> str:
    """
    格式化无效维度信息提示
    
    参数:
        invalid_dimensions: 无效维度列表
    
    返回:
        格式化后的提示信息字符串
    """
    if not invalid_dimensions:
        return ''
    return f"请你注意，指标查询时检测到用户可能输入了错误的维度信息。\n请你告诉用户，未检索到这些维度信息：{invalid_dimensions}。\n以下结果是忽略掉这些错误的维度信息后，查询到的结果。"


def format_clarify_information(invalid_dimensions: list, metric_dimension_info: str = '') -> str:
    """
    格式化澄清信息
    
    参数:
        invalid_dimensions: 无效维度列表
        metric_dimension_info: 指标和维度信息（可选）
    
    返回:
        格式化后的澄清信息字符串
    """
    clarify_information = f"指标查询时检测到了错误的维度信息，以下维度信息不存在于指标当中，请检查输入的信息是否正确：{invalid_dimensions}。"
    if metric_dimension_info:
        clarify_information += f"\n以下是指标和指标的维度信息：{metric_dimension_info}"
    return clarify_information


# ==================== 数据处理工具函数 ====================

def format_dimension_dataframe(data: list, headers: list, field_format_config_list: list) -> pd.DataFrame:
    """
    格式化维度分析数据的 DataFrame
    
    参数:
        data: 数据列表
        headers: 列标题列表
        field_format_config_list: 字段格式化配置列表
    
    返回:
        格式化后的 DataFrame
    """
    df = pd.DataFrame(data, columns=headers, dtype=str)
    for i, formater in enumerate(field_format_config_list):
        if i < len(df.columns):
            df[df.columns[i]] = data_format(formater, df[df.columns[i]])
    return df


def format_metric_link_nodes(nodes: list) -> dict:
    """
    格式化 metric-link-analysis 的节点数据
    
    参数:
        nodes: 节点数据列表
    
    返回:
        格式化后的节点字典，key 为 metricId
    """
    metric_id_dict = {}
    for _node in nodes:
        node = deepcopy(_node)
        node.update(dict(zip(
            ['metricValue', 'compareMetricValue'],
            data_format(node['valueFormatConfig'], [node['metricValue'], node['compareMetricValue']])
        )))
        if node.get('changeAmount'):
            node['changeAmount'] = data_format(node['valueFormatConfig'], [node['changeAmount']])[0]
        node.pop('valueFormatConfig', None)
        metric_id = node.pop('metricId')
        metric_id_dict[metric_id] = node
    return metric_id_dict


def filter_invalid_contribution_metrics(metric_id_dict: dict) -> dict:
    """
    过滤掉贡献度为 None 的指标
    
    参数:
        metric_id_dict: 指标ID字典
    
    返回:
        过滤后的指标ID字典
    """
    invalid_contribution = [
        key for key in metric_id_dict
        if metric_id_dict[key].get('contributionRate', 0) is None
    ]
    for key in invalid_contribution:
        metric_id_dict.pop(key)
    return metric_id_dict


def format_metric_links_string(links: list, metric_id_dict: dict) -> str:
    """
    格式化指标关联关系字符串
    
    参数:
        links: 关联关系列表
        metric_id_dict: 指标ID字典
    
    返回:
        格式化后的关联关系字符串
    """
    metric_links = ''
    for link in links:
        source_name = metric_id_dict[link['sourceNodeId']]['metricName']
        target_name = metric_id_dict[link['targetNodeId']]['metricName']
        contribution_rate = metric_id_dict[link['sourceNodeId']]['contributionRate']
        metric_links += f"指标【{source_name}】对指标【{target_name}】的贡献度是{contribution_rate}。\n"
    return metric_links


def merge_lineage_dataframes(result_data: dict, merge_key: str = 'ORG_ID') -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    合并 lineage-analysis 的 DataFrame
    
    参数:
        result_data: API返回的结果数据字典，应包含 newData, lackData, diffData 及其对应的 Original 数据
        merge_key: 合并键，默认为 'ORG_ID'
    
    返回:
        (new_data, lack_data, diff_data) 三个合并后的 DataFrame
    """
    selected_columns = ['ORG_ID', 'ORG_NM', "UP_LVL_ORG_NAME", "AREA", "UNIT"]
    
    # 创建基础 DataFrame
    new_data = pd.DataFrame(result_data['newData']['data'], columns=result_data['newData']['headers'], dtype=str)
    lack_data = pd.DataFrame(result_data['lackData']['data'], columns=result_data['lackData']['headers'], dtype=str)
    diff_data = pd.DataFrame(result_data['diffData']['data'], columns=result_data['diffData']['headers'], dtype=str)
    
    # 提取原始数据并选择指定列
    all_new_data = pd.DataFrame(
        result_data['newDataOriginal']['data'],
        columns=result_data['newDataOriginal']['headers'],
        dtype=str
    )[selected_columns]
    
    all_lack_data = pd.DataFrame(
        result_data['lackDataOriginal']['data'],
        columns=result_data['lackDataOriginal']['headers'],
        dtype=str
    )[selected_columns]
    
    all_diff_data = pd.DataFrame(
        result_data['diffDataOriginal']['data'],
        columns=result_data['diffDataOriginal']['headers'],
        dtype=str
    )[selected_columns]
    
    # 合并数据
    new_data = pd.merge(new_data, all_new_data, left_on=merge_key, right_on=merge_key, how='left')
    lack_data = pd.merge(lack_data, all_lack_data, left_on=merge_key, right_on=merge_key, how='left')
    diff_data = pd.merge(diff_data, all_diff_data, left_on=merge_key, right_on=merge_key, how='left')
    
    return new_data, lack_data, diff_data


def merge_multi_source_knowledge(recall_nodes: list) -> str:
    """
    合并多源知识
    
    参数:
        recall_nodes: 召回节点列表
    
    返回:
        合并后的知识字符串
    """
    multi_source_knowledge = ''
    for multi_source_query_result in recall_nodes:
        multi_source_knowledge += multi_source_query_result.page_content
    return multi_source_knowledge


def format_metric_info_string(metric_info: dict, exclude_keys: list = None) -> str:
    """
    格式化指标信息字符串
    
    参数:
        metric_info: 指标信息字典
        exclude_keys: 要排除的键列表，默认为 ['definition', 'associated_dimension']
    
    返回:
        格式化后的指标信息字符串
    """
    if exclude_keys is None:
        exclude_keys = ['definition', 'associated_dimension']
    
    return ",".join([
        f"{key}:'{value}'"
        for key, value in metric_info.items()
        if key not in exclude_keys
    ])


def ensure_single_selected_output(outputs: list) -> list:
    """
    确保至少有一个输出被选中，且只有一个输出被选中
    
    参数:
        outputs: 输出列表
    
    返回:
        更新后的输出列表
    """
    # 如果没有任何输出被选中，选中第一个
    if not any(output['selected'] for output in outputs):
        outputs[0]['selected'] = True
    
    # 如果有多个输出被选中，只保留第一个被选中的
    selected_count = sum(1 for output in outputs if output['selected'])
    if selected_count > 1:
        flag = 0
        for output in outputs:
            if output['selected']:
                if not flag:
                    flag = 1
                else:
                    output['selected'] = False
    
    return outputs


def build_dimension_filters_with_defaults(
    dimension_filters: dict,
    available_dimensions: list
) -> dict:
    """
    使用维度默认值构建维度过滤器
    
    参数:
        dimension_filters: 现有维度过滤器
        available_dimensions: 可用维度列表
    
    返回:
        更新后的维度过滤器
    """
    is_empty = not dimension_filters or (
        isinstance(dimension_filters, dict) and dimension_filters.get('must') == []
    )
    
    if is_empty and available_dimensions:
        dimension_defaults = {
            m['name']: m.get('defaultValue')
            for m in available_dimensions
            if m.get('defaultValue')
        }
        
        if dimension_defaults:
            dimension_filters = {'must': []}
            for dimension_name, default_value in dimension_defaults.items():
                dimension_filters['must'].append({
                    'dimensionName': dimension_name,
                    'operator': '=',
                    'dimensionValue': default_value
                })
    
    return dimension_filters


def create_simple_thought_branch(result: dict, analysis_type: str, gi: int, session_id: str) -> RunnablePassthrough:
    """
    创建简单的 set_thought 分支
    
    参数:
        result: API返回的结果字典
        analysis_type: 分析类型
        gi: 分组索引
        session_id: 会话ID
    
    返回:
        RunnablePassthrough 链
    """
    return RunnablePassthrough.assign(
        set_thought=lambda x, v=result, w=analysis_type: set_thought(session_id, f'{w}_{gi}', v)
    )


def extract_dimension_info(associated_dimension: list) -> tuple[list, dict, dict, list]:
    """
    从关联维度列表中提取维度相关信息
    
    参数:
        associated_dimension: 关联维度列表
    
    返回:
        (dimension_names, dimension_kvs, dimension_defaults, mandatory_dimension) 元组
        - dimension_names: 维度名称列表
        - dimension_kvs: 维度键值对字典 {name: values}
        - dimension_defaults: 维度默认值字典 {name: defaultValue}
        - mandatory_dimension: 必选维度列表
    """
    dimension_names = [m['name'] for m in associated_dimension]
    dimension_kvs = {m['name']: m['values'] for m in associated_dimension}
    dimension_defaults = {
        m['name']: m.get('defaultValue')
        for m in associated_dimension
        if m.get('defaultValue')
    }
    mandatory_dimension = [
        m['name'] for m in associated_dimension
        if m.get('dimMandatory')
    ]
    return dimension_names, dimension_kvs, dimension_defaults, mandatory_dimension

