# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第1012-1022行（query_caller）、第1054-1283行（query_service）、
         第1285-1295行（warning_process）、第1079-1124行（PDT时间调整逻辑，现集成在query_service中）
功能说明：查询处理 - 包含查询调用、查询服务、警告处理、PDT累计指标时间调整
重构日期：2024-12-19
"""
import json
import re
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableGenerator,
    chain as chain_decorator,
)
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.values import RunnableValue
from framebase.text2sql import sql_json_2_md

from commons.core.infrastructure import (
    metric_service,
    metric_service_api_configs,
    Metric_Service_Error_Message,
    Metric_Low_Relevance_Message,
    Metric_No_Dimension_Message,
    Metric_No_Dimension_Details_Message,
    Metric_Null_Result_Message,
    date_mapping_reverse,
    model_binding,
    hold_stream,
    data_format,
    is_spec_pdt_app,
    is_multi_app_id,
)
from commons.core.analysis_utils import get_permission_message
from commons.core.query_utils import (
    format_dimension_info_string,
    get_prompt_name_by_result_length,
    collect_warning_messages,
    extract_metric_candidates,
)
from commons.core.stream_utils import metric_query_description_process
from chains.table2chart_chain import chain as table2chart_chain
from utils.dbs import set_thought
from utils.logger import logger
from utils.exceptions import MetricQueryError, NoPermissionError

# ==================== PDT时间查询模式检测 ====================
# 代码来源：text2metric_chain.py（原PDT时间调整逻辑）
def detect_pdt_time_query_patterns(question: str) -> tuple[bool, bool, bool]:
    """
    检测PDT时间查询模式
    
    参数:
        question: 用户问题字符串
    
    返回:
        (is_same_month_query, is_from_january_query, has_each_month_keyword) 元组
    """
    is_same_month_query = False
    if question:
        same_month_keywords = ['当月', '这个月', '本月', '当月累计', '这个月累计', '本月累计']
        is_same_month_query = any(keyword in question for keyword in same_month_keywords)
    
    is_from_january_query = False
    if question and re.search(r'1月?[-\u5230\u81f3](\d+)\u6708', question):
        is_from_january_query = True
    
    has_each_month_keyword = False
    if question:
        each_month_keywords = ['各月', '每个月', '每月', '分别', '各个月']
        has_each_month_keyword = any(keyword in question for keyword in each_month_keywords)
    
    return is_same_month_query, is_from_january_query, has_each_month_keyword

# ==================== 缓存检查 ====================
# 代码来源：text2metric_chain.py（原第111-158行）
def check_redis_metric_cache(x):
    """
    检查Redis指标缓存
    
    如果有缓存数据且命中，返回True；否则返回False
    如果存在缓存的思考过程，会进行流式输出
    """
    # 检查是否有缓存数据
    if x.get('cache_hit') and x.get('metric_query') and x.get('metric_intents'):
        logger.info("使用缓存数据执行metric_query_execute_chain")
        
        # 如果有缓存的思考过程，直接启动流式输出（同步等待）
        if x.get('cached_insight'):
            import time
            
            # 获取完整内容
            content = x['cached_insight'].get('content', '')
            if content:
                logger.info(f"开始流式输出思考过程，内容长度: {len(content)}")
                
                # 分成10次输出
                total_length = len(content)
                chunk_size = total_length // 10
                
                for i in range(10):
                    # 计算当前输出的结束位置
                    end_pos = min((i + 1) * chunk_size, total_length)

                    # 如果是最后一次，确保包含完整内容
                    if i == 9:
                        end_pos = total_length
            
                    current_content = content[:end_pos]
                    
                    # 判断是否是最后一次输出
                    is_end = (i == 9)
                    
                    logger.info(f"输出第{i+1}次，内容长度: {len(current_content)}")
                    set_thought(x['session_id'], 'insight', {
                        'chunk': current_content,
                        'end': is_end
                    })
                    
                    if not is_end:
                        time.sleep(0.1)
                
                logger.info("思考过程流式输出完成")
            else:
                logger.warning("cached_insight中没有content内容")
        
        return True
    else:
        logger.info("无缓存数据，继续执行metric_router_chain")
        return False

# ==================== 警告处理 ====================
# 代码来源：text2metric_chain.py（原第1285-1295行）
@chain_decorator
async def warning_process(x, config):
    """
    警告处理Chain
    
    处理查询过程中的警告信息，如低相关性指标提示
    """
    session_id = config['input']['session_id']
    id = config['metadata']['id']
    warning = [x]
    if config['metadata']['metric_pick']:
        mentioned_metric = config['metadata']['metric_pick'].get('mentioned_metric', [])
        if not mentioned_metric:
            warning.append(Metric_Low_Relevance_Message)
    set_thought(session_id, f'invalid_dimensions_{id}', warning)
    return x

# ==================== 查询调用 ====================
# 代码来源：text2metric_chain.py（原第1012-1022行）
def call_metric_query(metric_query, cookie=None):
    """
    调用指标查询API
    
    封装metric_service.metric_query调用，处理异常
    """
    try:
        result = metric_service.metric_query(metric_query, cookie)
        if str(result['code']) != '200':
            raise MetricQueryError(f"Metric query failed: {result}")
        return metric_query, result
    except NoPermissionError as e:
        e.query = metric_query
        raise e
    except Exception as e:
        raise MetricQueryError(f"Metric query failed: {e}", query=metric_query)

# ==================== 查询服务 ====================
# 代码来源：text2metric_chain.py（原第1054-1283行）
@chain_decorator
async def call_metric_query_service(x, config):
    """
    指标查询服务Chain
    
    并发执行多个查询，处理结果（格式化、图表生成），生成警告和候选问题
    """

    @chain_decorator
    async def set_clarify(x, config):
        session_id = config['input']['session_id']
        set_thought(session_id, f'clarify', {'message': '您还可以提问以下相关的指标：', 'choices': x.get('new_questions')})
        return x

    branches = {'passthrough': RunnablePassthrough()}
    
    if x['metric_query']:
        metric_querys = x['metric_query']
        # 同步查询时间信息到意图数据（用于前端展示）
        if x.get('metric_intents'):
            for i in range(len(x['metric_query'])):
                for group in x['metric_intents']:
                    for intent in group:
                        if intent['metricId'] in x['metric_query'][i]['metricIdList']:
                            if x['metric_query'][i].get('comparisons', {}):
                                intent['comparisons'] = x['metric_query'][i]['comparisons']
                            intent['startDate'] = x['metric_query'][i]['startDate']
                            intent['endDate'] = x['metric_query'][i]['endDate']
                            intent['windowDate'] = date_mapping_reverse[x['metric_query'][i]['windowDate']]  # 反向转换日期格式
            set_thought(x['session_id'], 'intent', {'formdata': x['metric_intents'], 'metadata': x['metric_query_metadata']})
           
        # PDT专属累计指标时间调整：特殊处理累计指标的时间范围
        app_id = x.get('app_id') or config.get('input', {}).get('app_id')
        if app_id and is_spec_pdt_app(app_id):
            question = x.get('question', '') or config.get('input', {}).get('question', '')
            # 检测PDT时间查询模式
            is_same_month_query, is_from_january_query, has_each_month_keyword = detect_pdt_time_query_patterns(question)
                
            metric_querys_for_storage = deepcopy(metric_querys)
            for query in metric_querys_for_storage:
                if not query.get('is_accumulative'):
                    continue
                start_date = query.get('startDate', '')
                end_date = query.get('endDate', '')
                time_interval = query.get('time_interval', 'DAY')
                if not (start_date and end_date and start_date == end_date):
                    continue
                if is_same_month_query:
                    continue
                if time_interval in ['MONTH', '月']:
                    query['startDate'] = end_date[:4] + '-01' if len(end_date) >= 7 else '2025-01'
                elif time_interval in ['DAY', '日']:
                    query['startDate'] = end_date[:4] + '-01-01' if len(end_date) >= 10 else '2025-01-01'
            if is_from_january_query and not has_each_month_keyword:
                for query in metric_querys:
                    if query.get('is_accumulative'):
                        end_date = query.get('endDate', '')
                        if end_date:
                            query['startDate'] = end_date
            if x.get('metric_intents'):
                for query in metric_querys_for_storage:
                    for group in x['metric_intents']:
                        for intent in group:
                            if intent['metricId'] in query.get('metricIdList', []):
                                intent['startDate'] = query['startDate']
                                intent['endDate'] = query['endDate']
                set_thought(x['session_id'], 'intent', {'formdata': x['metric_intents'], 'metadata': x['metric_query_metadata']})
        # PDT专属累计指标时间调整（以上）
    
        set_thought(x['session_id'], 'metric_queries', {'thought': metric_querys})
        logger.info('metric intents requests:\n' + json.dumps(metric_querys, ensure_ascii=False, indent=4))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_metric_query, metric_query, config.get('headers', {}).get('cookie')) for metric_query in metric_querys]

            # 收集结果
            results = [None] * len(metric_querys)
            for future in as_completed(futures):
                try:
                    query, result = future.result()
                    result['data_source_query_info'] = {
                        "question_id": "",
                        "question_content": "",
                        "sql": result.get('data', {}).get('sql', "")
                    }
                    results[int(query['request_index']) - 1] = (query, result)
                except Exception as exc:
                    logger.error(f"Generated an exception: {exc}")
                    results[int(exc.query['request_index']) - 1] = (exc.query, {'exception': exc})
            datasets = []
            for (query, result) in deepcopy(results):
                if 'exception' in result:
                    if isinstance(result['exception'], NoPermissionError):
                        app_id = str(x['app_id'])
                        error_type = result['exception'].status_code if result['exception'].status_code == 'DIM403' else 'SYS403'
                        message = get_permission_message(app_id, error_type)
                        set_thought(x['session_id'], f"metric_query_description_{query['request_index']}", {'chunk': f"{message}{result['exception'].no_permission_metric}。", "end": True})
                        continue
                    else:
                        set_thought(x['session_id'], f"metric_query_description_{query['request_index']}", {'chunk': f"{Metric_Service_Error_Message}", "end": True})
                        continue
                result['data']['request_index'] = query['request_index']
                datasets.append(result['data'])
                # chart generation
                chart = None
                if 'data' in result['data']:
                    row = [dict(zip(result['data']['headers'], data)) for data in result['data']['data'][:2]]
                    async for chunk in table2chart_chain.with_config(config=config).astream({"question": x['question'], "table": row, "text2metric": True}):
                        if 'response_variables' in chunk and 'chart' in chunk['response_variables']:
                            chart = chunk['response_variables']['chart']
                if chart:
                    set_thought(x['session_id'], f"metric_query_chart_{query['request_index']}", chart)
                else:
                    set_thought(x['session_id'], f"metric_query_chart_{query['request_index']}", {})
            set_thought(x['session_id'], "metric_query_result", datasets)

            for i, (query, result) in enumerate(results):
                if 'exception' in result:
                    continue
                unauthorized_metric = [m['name'] for m in result['data'].get('unauthorizedMetrics') or []]
                df = pd.DataFrame(result['data']['data'], columns=result['data']['headers'], dtype=str)
                for j, formater in enumerate(result['data'].get('fieldFormatConfigList', []) or []):
                    df[df.columns[j]] = data_format(formater, df[df.columns[j]])
                result['data']['data'] = df.values.tolist()

                request_index = i + 1 if not query.get('request_index') else query.get('request_index')
                set_thought(x['session_id'], f"sql_{request_index}", result['data'].get('sql', ''))
                set_thought(x['session_id'], f"metric_data_{request_index}", df.to_dict('records'))
                if x.get('disable_description'):
                    return RunnablePassthrough()
                
                # check metric result length
                prompt_name = get_prompt_name_by_result_length(
                    len(result['data']['data']),
                    int(metric_service_api_configs.get('metric_query_reject_answer_row_number'))
                )
                
                dimension_info = format_dimension_info_string(query)
                warnings = query.get('warnings') or {}
                if x.get('metric_dimension_warning_mode') == 'all':
                    warning_chain = RunnablePassthrough.assign(template_name=RunnableValue(value='metric_warning_template'),
                                                metric_result=lambda x, v=sql_json_2_md(result['data']): v,
                                                warnings=lambda x, v=warnings: v,
                                                metric_query=lambda x, v=query: v
                                            ) | model_binding | hold_stream | ekcStrOutputParser() | \
                            warning_process.with_config(config={'metadata': {'id': request_index, 'metric_pick': x.get('metric_pick')}})
                    branches[f'warning_{i}'] = warning_chain
                elif x.get('metric_dimension_warning_mode') in ['only_abnormal_metric_message', 'abnormal_metric_and_dimension_message', 'abnormal_metric_and_dimension_details']:
                    warning_message = collect_warning_messages(
                        x.get('metric_dimension_warning_mode'),
                        x.get('metric_pick', {}),
                        warnings,
                        Metric_Low_Relevance_Message,
                        Metric_No_Dimension_Message,
                        Metric_No_Dimension_Details_Message,
                    )
                    set_thought(x['session_id'], f'invalid_dimensions_{request_index}', warning_message)
                else:
                    pass
                branches[f'{i}'] = \
                    RunnablePassthrough.assign(template_name=RunnableValue(value=prompt_name),
                                               data_number=RunnableValue(value=len(result['data']['data'])),
                                               null_message=RunnableValue(value=Metric_Null_Result_Message),
                                                model_name=RunnableValue(value='output_llm'),
                                                metric_result=lambda x, v=sql_json_2_md(result['data']): v,
                                                dimension_info=lambda x, v=dimension_info: v
                    ) | \
                    RunnablePassthrough.assign(placeholder=model_binding | RunnableGenerator(metric_query_description_process).with_config(config={'metadata': {'id': request_index, 'unauthorized_metric': unauthorized_metric}}))
        
        app_id = x.get('app_id')
        is_multi_mode = x.get('metric_pick_mode') == 'multiple' or (app_id and is_multi_app_id(app_id))
        metric_candiates = extract_metric_candidates(
            x.get('metric_pick', {}),
            x.get('raw_metric_info', []),
            is_multi_mode,
        )
        if metric_candiates:
            if x.get('metric_candiates_enabled') == 'on':
                metric_candiates_max_number = f"最多生成{x['metric_candiates_max_number']}个候选问题。"
                branches['metric_candiates'] = RunnablePassthrough.assign(template_name=RunnableValue(value='metric_candiates_template'),
                                                question=lambda x, v=x['question']: v,
                                                metric_candiates=lambda x, v=metric_candiates: v,
                                                metric_candiates_max_number=lambda x, v=metric_candiates_max_number: v
                        ) | \
                        model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser() | set_clarify
        
        return RunnablePassthrough.assign(**branches)

