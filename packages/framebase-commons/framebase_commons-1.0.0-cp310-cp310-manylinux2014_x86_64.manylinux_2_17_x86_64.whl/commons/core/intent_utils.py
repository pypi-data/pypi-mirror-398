# cython: annotation_typing = False
"""
意图工具函数 - Intent Utilities
代码来源：chains/text2metric_chain.py（从 service/intent.py 提取的工具函数）
功能说明：意图处理相关的通用工具函数，用于JSON schema加载、clarify处理等
创建日期：2024-12-19
"""
import json
import pkg_resources


def load_chain_json_schema(filename: str) -> dict:
    """
    加载chain配置目录下的JSON schema文件
    
    参数:
        filename: JSON schema文件名（如 'metric_router.json'）
    
    返回:
        加载的JSON schema字典
    """
    with open(pkg_resources.resource_filename('configs', f'chain/{filename}'), 'r', encoding='utf-8') as f:
        return json.load(f)


def should_remove_clarify_choices(x: dict) -> bool:
    """
    判断是否应该移除schema中的clarify_choices
    
    参数:
        x: 包含clarify和history的字典
    
    返回:
        如果应该移除clarify_choices返回True，否则返回False
    """
    if x.get('clarify') == 'off':  # 明确关闭澄清功能
        return True
    elif x.get('history', []):
        # 上一轮已进行过澄清，不再需要clarify_choices
        if any(json.loads(t)['type'] == 'clarify' for t in x['history'][-1]['thoughts']):
            return True
    return False


def remove_clarify_choices_from_schema(schema: dict) -> dict:
    """
    从JSON schema中移除clarify_choices属性
    
    参数:
        schema: JSON schema字典
    
    返回:
        移除clarify_choices后的schema字典（原地修改）
    """
    if 'clarify_choices' in schema.get('properties', {}):
        schema['properties'].pop('clarify_choices')
    return schema


def extract_clarify_choices(x: dict) -> list | None:
    """
    从多个可能的位置提取clarify_choices
    
    参数:
        x: 包含clarify_choices的字典，可能在不同的键下
    
    返回:
        clarify_choices列表，如果不存在则返回None
    """
    return (
        x.get('clarify_choices') or 
        x.get('router_json', {}).get('clarify_choices') or 
        x.get('metric_pick', {}).get('clarify_choices')
    )

