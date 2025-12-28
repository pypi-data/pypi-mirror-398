# cython: annotation_typing = False
"""
Chain工具函数 - Chains Utilities
代码来源：chains/text2metric_chain.py（从 service/chains.py 提取的工具函数）
功能说明：Chain组合相关的通用工具函数，用于子请求处理、问题生成等
创建日期：2024-12-19
"""
from langchain_core.runnables import RunnablePassthrough
from framebase.values import RunnableValue
from community.models.stroutput_parser import ekcStrOutputParser

from .infrastructure import model_binding
from utils.logger import logger
from utils.exceptions import DBInfoError


def format_query_modified_values(request: dict) -> str:
    """
    格式化查询子请求的修改值信息
    
    参数:
        request: 子请求字典，包含 startDate, endDate, dimensionFilters, dimensionHolds
    
    返回:
        格式化后的修改值字符串
    """
    # 将查询参数格式化为自然语言描述，用于生成问题
    return f"startDate变为{request['startDate']}, endDate变为{request['endDate']}, dimensionFilters变成{request['dimensionFilters']}, dimensionHolds变为{request['dimensionHolds']}"


def format_analysis_modified_values(request: dict) -> str:
    """
    格式化分析子请求的修改值信息
    
    参数:
        request: 子请求字典，包含 sourceDate, targetDate, dimensionHolds, dimensionFilters
    
    返回:
        格式化后的修改值字符串
    """
    return f"sourceDate{request['sourceDate']}, targetDate{request['targetDate']}, dimensionHolds变为{request.get('dimensionHolds', [])}, dimensionFilters变为{request.get('dimensionFilters', {})}"


def create_subrequest_question(modified_values: str) -> RunnablePassthrough:
    """
    创建子请求问题生成链
    
    参数:
        modified_values: 格式化后的修改值字符串
    
    返回:
        RunnablePassthrough 链，用于生成问题
    """
    return RunnablePassthrough.assign(
        template_name=RunnableValue(value='metric_subrequest_question_refine_template'),
        modified_values=RunnableValue(value=modified_values)
    ) | model_binding | ekcStrOutputParser()


def create_subrequest_chain(question: RunnablePassthrough, metric_query: list, chain) -> RunnablePassthrough:
    """
    创建子请求执行链
    
    参数:
        question: 问题生成链
        metric_query: 指标查询列表
        chain: 要执行的chain（metric_query_execute_chain 或 metric_analysis_execute_chain）
    
    返回:
        RunnablePassthrough 链，用于执行子请求
    """
    # 组装子请求所需参数并执行对应的chain
    return RunnablePassthrough.assign(
        response_type=RunnableValue(values=['Metric']),
        question=question,
        metric_query=lambda x, v=metric_query: v
    ) | chain


# ==================== 错误处理函数 ====================
def raise_error_DBInfoError(x=None):
    """
    抛出指标未找到错误
    
    用于 RunnableBranch 的错误分支，当指标查询不存在时抛出 DBInfoError
    """
    raise DBInfoError('text2metric but no metric')


def raise_error_ValueError(x):
    """
    抛出意图错误
    
    用于 RunnableBranch 的错误分支，当意图识别错误时抛出 ValueError
    """
    logger.error('wrong intent:' + str(x))
    raise ValueError('wrong intent:' + str(x))

