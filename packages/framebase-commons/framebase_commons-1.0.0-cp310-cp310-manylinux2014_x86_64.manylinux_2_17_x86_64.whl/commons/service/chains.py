# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第1316-1321行（raise_error）、第1323-1326行（query_execute_chain）、
         第1396-1400行（analysis_execute_chain）、第2395-2403行（query_chain）、
         第2404-2411行（analysis_chain）、第2412行（scroll_chain）、
         第2413行（pick_chain）、第2414-2437行（router_chain）、第2440-2466行（sub_request）
功能说明：Chain组合 - 包含各种chain的组合逻辑
重构日期：2024-12-19
"""
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBranch,
    RunnableParallel,
    RunnablePick,
)

from commons.core.infrastructure import (
    date_mapping,
    replace_operator,
    charge,
    Metric_Not_Found_Message,
)
from commons.core.chains_utils import (
    format_query_modified_values,
    format_analysis_modified_values,
    create_subrequest_question,
    create_subrequest_chain,
    raise_error_DBInfoError,
    raise_error_ValueError,
)
from commons.service.query import call_metric_query_service
from commons.service.analysis import (
    call_metric_analysis_service,
    metric_analysis_additional_intent,
    refine_metric_analysis_intents,
)
from commons.service.metric import (
    metric_pick,
    metric_definition,
    scroll_metric_base,
    metric_tree_pick,
    metric_scroll_merge,
    metric_scroll_answer,
    process_metric_retrieve_result,
)
from commons.service.intent import (
    metric_router,
    metric_router_clarify_check,
    metric_router_clarify,
    passthrough_inputs,
    additional_intent,
)
from commons.service.dimension import dimension_intent
from commons.service.time import (
    get_metric_time_records,
    time_intent,
)
from commons.service.query_builder import (
    combine_rewrite,
    make_metric_query,
)
from chains.retriever_chain import metric_retrieve_chain
from chains.analytic_metric_chain import metric_time_recognizer, metric_dimension_recognizer
from utils.logger import logger

# ==================== 查询执行Chain ====================
# 代码来源：text2metric_chain.py（原第1323-1326行）
# 查询执行Chain：如果存在metric_query则执行查询，否则抛出错误
metric_query_execute_chain = RunnableBranch(
    (lambda x: x.get('metric_query'), call_metric_query_service | {"model_output": lambda x: "", 'response_variables': charge}),
    raise_error_DBInfoError
)

# ==================== 分析执行Chain ====================
# 代码来源：text2metric_chain.py（原第1396-1400行）
# 分析执行Chain：如果存在metric_query则执行分析，否则抛出错误
metric_analysis_execute_chain = RunnableBranch(
    (lambda x: x.get('metric_query'), call_metric_analysis_service | {"model_output": lambda x: "", 'response_variables': charge}),
    raise_error_DBInfoError
)

# ==================== 查询Chain ====================
# 代码来源：text2metric_chain.py（原第2395-2403行）
# 查询Chain：并行执行时间意图、维度意图、额外意图识别，然后构建查询并执行
metric_query_chain = RunnableParallel(
    time_intent=RunnableParallel(
        time_records=get_metric_time_records | RunnablePick('time_records'),
        metric_infos=RunnablePick('metric_infos'),
        question=RunnablePick('question'),
        time_recognizer=RunnablePick('time_recognizer')
    ) | time_intent,
    dimension_intent=dimension_intent,
    additional_intent=additional_intent,
    passthrough=RunnablePassthrough()
) | make_metric_query | metric_query_execute_chain

# ==================== 分析Chain ====================
# 代码来源：text2metric_chain.py（原第2404-2411行）
# 分析Chain：获取时间记录、分析意图识别、维度意图识别，细化分析意图后执行
metric_analysis_chain = RunnableParallel(
    time_records=get_metric_time_records | RunnablePick('time_records'),
    additional_intent=metric_analysis_additional_intent,
    dimension_intent=dimension_intent,
    time_recognizer=RunnablePick('time_recognizer'),
    passthrough=RunnablePassthrough()
) | refine_metric_analysis_intents | metric_analysis_execute_chain

# ==================== 滚动Chain ====================
# 代码来源：text2metric_chain.py（原第2412行）
# 滚动Chain：获取指标列表，选择指标和指标树，合并结果并生成答案
metric_scroll_chain = scroll_metric_base | RunnableParallel(
    metric_pick_result=metric_pick,
    metric_tree_pick_result=metric_tree_pick
) | metric_scroll_merge | metric_scroll_answer

# ==================== 选择Chain ====================
# 代码来源：text2metric_chain.py（原第2413行）
# 选择Chain：重写问题，检索指标，处理检索结果，选择相关指标
metric_pick_chain = combine_rewrite | RunnablePassthrough.assign(raw_metric_info=metric_retrieve_chain) | process_metric_retrieve_result | metric_pick

# ==================== 路由Chain ====================
# 代码来源：text2metric_chain.py（原第2414-2437行）
# 路由Chain：识别意图，根据意图分发到不同的处理Chain（scroll/query/analysis/definition）
metric_router_chain = metric_router | RunnableBranch(
    (metric_router_clarify_check, metric_router_clarify),  # 需要澄清则中断
    RunnablePassthrough.assign(response_type=lambda x: ['Metric'])
) | \
RunnableBranch(
    (lambda x: x.get('intent') == 'scroll', metric_scroll_chain),  # 滚动意图
    (lambda x: x.get('intent') != 'definition',  # 非定义意图需要指标选择和时间维度识别
        RunnableParallel(
            passthrough=metric_pick_chain,
            time_recognizer=metric_time_recognizer,
            metric_dimension_recognizer=metric_dimension_recognizer,
        ) | passthrough_inputs
    ),
    metric_pick_chain,  # 定义意图只需选择指标
) | \
RunnableBranch(  # 根据意图执行对应的处理Chain
    (lambda x: x.get('response_variables'), RunnablePassthrough()),  # 已有响应变量则透传
    (lambda x: x.get('intent') != 'definition' and not x.get('metric_infos', []), {"model_output": lambda x: Metric_Not_Found_Message, 'response_variables': charge}),  # 未找到指标
    (lambda x: x.get('intent') == 'definition', metric_definition),
    (lambda x: x.get('intent') == 'query', metric_query_chain),
    (lambda x: x.get('intent') in ['dimension_analysis', 'link_analysis', 'lineage_analysis', 'root cause analysis'], metric_analysis_chain),
    (lambda x: x.get('intent') == 'rank', metric_query_chain),
    raise_error_ValueError
)

# ==================== 子请求分发 ====================
# 代码来源：text2metric_chain.py（原第2440-2466行）
def sub_request_dispatcher(x):
    """
    子请求分发器
    
    处理sub_requests，根据类型（metric_query或analysis）分发到对应的执行Chain
    """
    metric_query = []
    
    for request in x['sub_requests']:
        if not isinstance(request, dict):
            request = request.dict()
        metric_query.append(request)
        if request['type'] == 'metric_query':  # 查询类型子请求
            modified_values = format_query_modified_values(request)
            question = create_subrequest_question(modified_values)
            chain = metric_query_execute_chain
            metric_query = request
            metric_query = replace_operator(metric_query)  # 转换操作符
            metric_query['windowDate'] = date_mapping[metric_query['windowDate']]  # 转换日期格式
            logger.info('sub request: text2metric_chain metric_query.')
            return create_subrequest_chain(question, [metric_query], chain)
        else:  # 分析类型子请求
            modified_values = format_analysis_modified_values(request)
            question = create_subrequest_question(modified_values)
            chain = metric_analysis_execute_chain
    return create_subrequest_chain(question, [metric_query], chain)

