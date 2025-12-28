# cython: annotation_typing = False
"""
维度工具函数 - Dimension Utilities
代码来源：chains/text2metric_chain.py（部分从 service/dimension.py 提取的工具函数）
功能说明：维度处理相关的通用工具函数，用于维度过滤器处理、维度名称提取等
创建日期：2024-12-19
"""
from collections import defaultdict

from utils.logger import logger


def recursive_traverse_dimension_filters(item):
    """
    递归遍历维度过滤器，处理重复的维度名称并设置默认操作符
    
    参数:
        item: 维度过滤器项（dict 或 list）
    
    返回:
        如果找到重复的维度名称，返回 buffer 字典；否则返回 None
    """
    if isinstance(item, dict):
        should = []
        for key, value in item.items():
            result = recursive_traverse_dimension_filters(value)
            if result:
                item[key] = []
                for k, v in result.items():
                    if len(v) > 1:
                        should.extend(v)
                    else:
                        item[key].extend(v)
        if should:
            if 'should' not in item:
                item['should'] = []
            item['should'].extend(should)

    elif isinstance(item, list):
        buffer = defaultdict(list)
        for element in item:
            if isinstance(element, dict):
                if element.get('dimensionName'):
                    buffer[element['dimensionName']].append(element)  # 收集相同维度名的过滤器
                if not element.get('operator'):
                    element['operator'] = '='  # 设置默认操作符
            recursive_traverse_dimension_filters(element)
        if buffer:  # 如果发现重复的维度名，返回buffer用于后续处理
            return buffer
    return None


def delete_invalid_dimension_filters(item, dimension_kvs):
    """
    删除无效的维度过滤器
    
    参数:
        item: 维度过滤器项（dict 或 list）
        dimension_kvs: 维度键值对字典，格式为 {dimension_name: [values]}
    """
    if isinstance(item, dict):
        if item.get('dimensionName') and item.get('dimensionValue') and (
            item.get('dimensionName') not in dimension_kvs or 
            item.get('dimensionValue') not in dimension_kvs[item.get('dimensionName')]
        ):
            item.clear()
        elif item.get('dimensionName') and not item.get('dimensionValue') and item.get('operator') not in ['is null', 'is not null']:
            item.clear()
        elif 'operator' in item and 'dimensionName' not in item:
            item.clear()
        else:
            for value in item.values():
                delete_invalid_dimension_filters(value, dimension_kvs)
    elif isinstance(item, list):
        for element in item:
            delete_invalid_dimension_filters(element, dimension_kvs)


def delete_empty_dimension_filters(item):
    """
    递归删除空的维度过滤器项
    
    参数:
        item: 维度过滤器项（dict 或 list）
    
    返回:
        清理后的维度过滤器项
    """
    if isinstance(item, dict):
        for k, v in item.items():
            item[k] = delete_empty_dimension_filters(v)
        item = {k: v for k, v in item.items() if v}
    elif isinstance(item, list):
        for i, element in enumerate(item):
            item[i] = delete_empty_dimension_filters(element)
        item = [m for m in item if m]
    return item


def extract_dimension_names_from_filters(item, result):
    """
    从维度过滤器中提取所有维度名称
    
    参数:
        item: 维度过滤器项（dict 或 list）
        result: 结果列表，用于收集维度名称
    """
    if isinstance(item, dict):
        for k, v in item.items():
            extract_dimension_names_from_filters(v, result)
        if item.get('dimensionName'):
            result.append(item['dimensionName'])
    elif isinstance(item, list):
        for i, element in enumerate(item):
            extract_dimension_names_from_filters(element, result)


def remove_wildcard_dimension_value(item):
    """
    递归移除维度过滤器中的通配符维度值（'*'）
    
    参数:
        item: 维度过滤器项（dict 或 list）
    """
    if isinstance(item, dict):
        if item.get('dimensionValue') == '*':
            item.clear()
        else:
            for value in item.values():
                remove_wildcard_dimension_value(value)
    elif isinstance(item, list):
        for element in item:
            remove_wildcard_dimension_value(element)


# ==================== 维度验证函数 ====================
# 代码来源：text2metric_chain.py（原第181-197行）
# 迁移路径：text2metric_chain.py → service/dimension.py → core/dimension_utils.py
def check_dimension_holds(x, dimension_names, mandatory_dimension):
    """
    检查并修正维度持有情况
    
    根据指标类型（百分比、点指标）和必选维度，修正dimensionHolds列表
    
    参数:
        x: 包含dimensionHolds的字典
        dimension_names: 可用维度名称列表
        mandatory_dimension: 必选维度列表
    
    返回:
        更新后的字典
    """
    if 'dimensionHolds' in x:
        if not isinstance(x['dimensionHolds'], list):
            x['dimensionHolds'] = []
    else:
        x['dimensionHolds'] = []
    x['dimensionHolds'] = [m for m in x['dimensionHolds'] if m in dimension_names]
    if x.get('unit') == '%' and x.get('metricType') != 2:
        x['dimensionHolds'] = dimension_names
    if x.get('is_point_metric'):
        x['dimensionHolds'] = dimension_names
    if mandatory_dimension:
        logger.debug(f"mandatory_dimension: {mandatory_dimension}")
        for dimension in mandatory_dimension:
            if dimension not in x['dimensionHolds']:
                x['dimensionHolds'].append(dimension)
    return x


# 代码来源：text2metric_chain.py（原第199-302行）
# 迁移路径：text2metric_chain.py → service/dimension.py → core/dimension_utils.py
def check_dimension_filters(x, dimension_kvs, dimension_defaults=None):
    """
    检查并修正维度过滤器
    
    清理无效和空的维度过滤器，合并must/should/must_not结构，应用维度默认值
    
    参数:
        x: 包含dimensionFilters的字典
        dimension_kvs: 维度键值对字典，格式为 {dimension_name: [values]}
        dimension_defaults: 维度默认值字典（可选）
    
    返回:
        更新后的字典
    """
    if dimension_defaults is None:
        dimension_defaults = {}
    
    dimension_names = []
    if 'dimensionFilters' in x:
        recursive_traverse_dimension_filters(x['dimensionFilters'])
        delete_invalid_dimension_filters(x['dimensionFilters'], dimension_kvs)
        x['dimensionFilters'] = delete_empty_dimension_filters(x['dimensionFilters'])
        extract_dimension_names_from_filters(x['dimensionFilters'], dimension_names)
        x['dimensionHolds'] = list(set(x['dimensionHolds'] + dimension_names))
        if 'must' in x['dimensionFilters']:
            if 'should' in x['dimensionFilters']:
                x['dimensionFilters']['must'].append({'should': x['dimensionFilters'].pop('should')})
            if 'must_not' in x['dimensionFilters']:
                x['dimensionFilters']['must'].append({'must_not': x['dimensionFilters'].pop('must_not')})
    
    if dimension_defaults:
        if 'dimensionFilters' not in x or not x['dimensionFilters']:
            x['dimensionFilters'] = {'must': []}
        if 'must' not in x['dimensionFilters']:
            x['dimensionFilters']['must'] = []
        dimension_holds = x.get('dimensionHolds', [])
        if not dimension_holds:
            for dimension_name, default_value in dimension_defaults.items():
                x['dimensionFilters']['must'].append({
                    'dimensionName': dimension_name,
                    'operator': '=',
                    'dimensionValue': default_value
                })
                if dimension_name not in dimension_holds:
                    dimension_holds.append(dimension_name)
        else:
            for dimension_name, default_value in dimension_defaults.items():
                if dimension_name not in dimension_holds:
                    dimension_holds.append(dimension_name)
                    x['dimensionFilters']['must'].append({
                        'dimensionName': dimension_name,
                        'operator': '=',
                        'dimensionValue': default_value
                    })
        
        x['dimensionHolds'] = dimension_holds
    return x

