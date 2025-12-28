# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第1805-1935行（dimension_intent, dimension_rerank）
功能说明：维度处理 - 包含维度意图识别、维度重排序
注意：维度验证和过滤函数（check_dimension_holds, check_dimension_filters等）已移至 core/dimension_utils.py
重构日期：2024-12-19
"""
import json
import pkg_resources
from copy import deepcopy
from itertools import product

from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    chain as chain_decorator,
)
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.values import RunnableValue
from framebase.embeddings import rerank_embeddings

from commons.core.infrastructure import (
    bm25_rerank,
    merge_list_by_order,
    model_binding,
    hold_stream,
)
from commons.core.dimension_utils import (
    remove_wildcard_dimension_value,
)
from utils.logger import logger

# ==================== 维度意图识别 ====================
# 代码来源：text2metric_chain.py（原第1805-1935行）
@chain_decorator
async def dimension_intent(x, config):
    """
    维度意图识别Chain
    
    使用BM25和reranker识别用户问题中的维度信息，调用LLM生成维度过滤器
    """

    @chain_decorator
    def attach_invalid_dimension(x, config):
        if config.get('metadata', {}).get('invalid_dimension'):
            x['invalidDimensions'] = config['metadata']['invalid_dimension']
        return x

    @chain_decorator
    def remove_wildcard_dimension(x):
        """移除通配符维度值（*），并清理空值"""
        if x.get('dimensionFilters'):
            remove_wildcard_dimension_value(x['dimensionFilters'])
            x['dimensionFilters'] = {k: v for k, v in x['dimensionFilters'].items() if v}  # 过滤空值
        return x

    with open(pkg_resources.resource_filename('configs', 'chain/metric_dimension_intent.json'), 'r', encoding='utf-8') as f:
        json_schema = json.load(f)
    branches = {}
    reranker = list(rerank_embeddings.values())[0]
    metric_names = [m['name'] for m in x['metric_infos']]
    _logger = RunnablePassthrough(lambda x: logger.info(f"dimension_intent: {x}"))
    for i, metric_info in enumerate(x['metric_infos']):
        _json_schema = deepcopy(json_schema)
        reranker_inputs = {'query': [], 'candidates': []}
        
        dimension_alias_map = {}
        alias_dimension_map = {}
        for dimension in x['dimensions']:
            value = dimension.get('value') or ''
            name = dimension['name']
            _bm25_results = {}
            for dimension_info in metric_info['associated_dimension']:
                if dimension_info['name'] not in _bm25_results:
                    _bm25_results[dimension_info['name']] = {
                        'name': dimension_info['name'],
                        'alias': dimension_info['alias'],
                        'values': merge_list_by_order(
                            bm25_rerank(value, dimension_info['values'], 3),
                            bm25_rerank(name, dimension_info['values'], 3)
                        )
                    }
                else:
                    _bm25_results[dimension_info['name']]['values'] = merge_list_by_order(
                        _bm25_results[dimension_info['name']]['values'],
                        merge_list_by_order(
                            bm25_rerank(value, dimension_info['values'], 3),
                            bm25_rerank(name, dimension_info['values'], 3)
                        )
                    )
            reranker_inputs['query'].append(f'{name}:{value}')
            for jk, jv in _bm25_results.items():
                _candidates = []
                alias_dimension_map[jv['name']] = jv.get('alias', [])
                if jv.get('alias'):
                    for k_alias in jv['alias']:
                        dimension_alias_map[k_alias] = jv['name']
                    for k_alias, kv in product(jv['alias'], jv['values']):
                        _candidates.append(json.dumps({k_alias: kv}, ensure_ascii=False))
                    if value:
                        for k_alias in jv['alias']:
                            _candidates.append(json.dumps({k_alias: ''}, ensure_ascii=False))
                dimension_alias_map[jv['name']] = jv['name']
                for k_alias, kv in product([jv['name']], jv['values']):
                    _candidates.append(json.dumps({k_alias: kv}, ensure_ascii=False))
                if value:
                    for k_alias in [jv['name']]:
                        _candidates.append(json.dumps({k_alias: ''}, ensure_ascii=False))
                reranker_inputs['candidates'].extend(_candidates)
        # if there is dimension detected by llm
        if len(reranker_inputs['query']) > 0:
            reranker_inputs['candidates'] = list(dict.fromkeys(reranker_inputs['candidates']))
            reranker_result = reranker.compute_score(
                reranker_inputs['query'],
                [reranker_inputs['candidates'] for m in range(len(reranker_inputs['query']))]
            )
            dimension_names_reranker_result = reranker.compute_score(
                reranker_inputs['query'],
                [[d['name'] for d in metric_info['associated_dimension']] for _ in range(len(reranker_inputs['query']))]
            )
            relevant_dimension_names = list(set([n['data'] for m in dimension_names_reranker_result for n in m if n['score'] > 0]))
            for d in metric_info['associated_dimension']:
                if d['name'] not in relevant_dimension_names and (any(t['name'] in d['name'] for t in x['dimensions']) or any(d['name'] in t['name'] for t in x['dimensions'])):
                    relevant_dimension_names.append(d['name'])
            _relevant_dimension = []
            invalid_dimensions = []
            for ri in range(len(reranker_result)):
                # empty
                if not reranker_result[ri]:
                    invalid_dimensions.append(reranker_inputs['query'][ri])
                    continue
                # rerank score lower than 0, means the dimension is not relevant to the metric
                _r = {}
                reranker_result[ri] = sorted(reranker_result[ri], key=lambda x: x['score'], reverse=True)
                logger.info(f'dimension reranker:{reranker_inputs["query"][ri]}:{reranker_result[ri][:3]}')
                if reranker_result[ri][0]['score'] < 0:
                    invalid_dimensions.append(reranker_inputs['query'][ri])
                else:
                    relevant_dimension_values = list(filter(lambda m: m['score'] > 0, reranker_result[ri]))
                    for relevant_dimension_value in relevant_dimension_values:
                        for k, v in json.loads(relevant_dimension_value['data']).items():
                            if dimension_alias_map[k] not in _r:
                                _r[dimension_alias_map[k]] = {
                                    'name': dimension_alias_map[k],
                                    'alias': alias_dimension_map[dimension_alias_map[k]],
                                    'values': [v]
                                }
                            elif v not in _r[dimension_alias_map[k]]['values']:
                                _r[dimension_alias_map[k]]['values'].append(v)
                    _relevant_dimension.extend(list(_r.values()))

            if _relevant_dimension or invalid_dimensions:
                relevant_dimension = {}
                for dimension_info in _relevant_dimension:
                    if relevant_dimension.get(dimension_info['name']):
                        relevant_dimension[dimension_info['name']]['values'] = merge_list_by_order(
                            relevant_dimension[dimension_info['name']]['values'],
                            dimension_info['values']
                        )
                    else:
                        relevant_dimension[dimension_info['name']] = dimension_info
                
                if invalid_dimensions:
                    similarity_result = reranker.compute_score([metric_info['name']], [invalid_dimensions])
                    invalid_dimensions = [invalid_dimensions[k] for k, t in enumerate(similarity_result[0]) if t['score'] < 0]
                if invalid_dimensions:
                    _attach_invalid_dimension = attach_invalid_dimension.with_config(config={'metadata': {'invalid_dimension': invalid_dimensions}})
                else:
                    _attach_invalid_dimension = RunnablePassthrough()
                
                for dimension_name in relevant_dimension_names:
                    if dimension_name not in relevant_dimension:
                        relevant_dimension[dimension_name] = {
                            'name': dimension_name,
                            'alias': alias_dimension_map[dimension_name],
                            'values': []
                        }
                if relevant_dimension:
                    _json_schema['properties']['related_dimension_values']['description'] = _json_schema['properties']['related_dimension_values']['description'].replace('{dimension_info}', str(relevant_dimension))
                    branches[metric_info['metricId']] = RunnablePassthrough.assign(
                        relevant_dimension=lambda x, v=relevant_dimension: v,
                        json_schema=lambda x, v=_json_schema: v,
                        metric_name=lambda x, v=metric_names: v,
                        template_name=RunnableValue(value='metric_dimension_intent_template'),
                    ) | model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser() | _logger | remove_wildcard_dimension | _attach_invalid_dimension
                else:
                    branches[metric_info['metricId']] = lambda x: {}
            else:
                branches[metric_info['metricId']] = lambda x: {}
        else:
            branches[metric_info['metricId']] = lambda x: {}
    return RunnableParallel(branches)

