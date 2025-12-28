# cython: annotation_typing = False
"""
流式处理工具函数 - Stream Utilities
代码来源：chains/text2metric_chain.py
原始行数：第422-432行（base_stream）、第1297-1314行（query_stream）、
         第1328-1343行（dimension_stream）、第1345-1360行（multi_source_stream）、
         第1362-1377行（lineage_stream）、第1379-1394行（link_stream）、
         第2030-2043行（scroll_stream）
功能说明：流式处理工具函数 - 包含各种流式输出处理函数
迁移路径：text2metric_chain.py → service/stream.py → core/stream_utils.py
重构日期：2024-12-19
"""
import asyncio
from langchain.schema.messages import BaseMessage

from framebase import thought_wait_time
from utils.dbs import set_thought
from utils.logger import logger

# ==================== 基础流式处理 ====================
# 代码来源：text2metric_chain.py（原第422-432行）
async def stream_process(chunks, config):
    """基础流式处理，保存思考过程（insight）"""
    session_id = config['input']['session_id']

    async for chunk in chunks:
        if chunk.get('insight'):  # 如果chunk包含insight，实时保存
            set_thought(session_id, 'insight', {'chunk': chunk.get('insight')})
        yield chunk
    # 流式处理结束，标记end=True并等待一段时间确保写入完成
    set_thought(session_id, 'insight', {'chunk': chunk.get('insight'), 'end': True})
    await asyncio.sleep(thought_wait_time)
    logger.info('metric_router: ' + str(chunk))
    yield chunk

# ==================== 查询流式处理 ====================
# 代码来源：text2metric_chain.py（原第1297-1314行）
async def metric_query_description_process(chunks, config):
    """查询描述流式处理，保存查询描述和未授权指标信息"""
    session_id = config['input']['session_id']
    id = config['metadata']['id']
    content = ''
    unauthorized_metric = config['metadata']['unauthorized_metric']
    if unauthorized_metric:
        content += f"以下指标无权限访问：{unauthorized_metric}。\n"
    async for chunk in chunks:
        if isinstance(chunk, BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk) == str:
                content += chunk
            
        set_thought(session_id, f"metric_query_description_{id}", {'chunk': content})
        yield chunk
    set_thought(session_id, f"metric_query_description_{id}", {'chunk': content, 'end': True})

# ==================== 维度流式处理 ====================
# 代码来源：text2metric_chain.py（原第1328-1343行）
async def dimension_stream_process(chunks, config):
    """维度分析流式处理，保存维度分析描述"""
    session_id = config['input']['session_id']
    index = config['metadata']['index']
    content = ''
    async for chunk in chunks:
        if isinstance(chunk, BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk) == str:
                content += chunk
        set_thought(session_id, f'dimension-description_{index}', {'chunk': content})
        yield chunk
    set_thought(session_id, f'dimension-description_{index}', {'chunk': content, 'end': True})
    await asyncio.sleep(thought_wait_time)
    yield chunk

# ==================== 多源分析流式处理 ====================
# 代码来源：text2metric_chain.py（原第1345-1360行）
async def multi_source_stream_process(chunks, config):
    """多源分析流式处理，保存多源分析描述"""
    session_id = config['input']['session_id']
    index = config['metadata']['index']
    content = ''
    async for chunk in chunks:
        if isinstance(chunk, BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk) == str:
                content += chunk
        set_thought(session_id, f'multiple-sources-analysis-description_{index}', {'chunk': content})
        yield chunk
    set_thought(session_id, f'multiple-sources-analysis-description_{index}', {'chunk': content, 'end': True})
    await asyncio.sleep(thought_wait_time)
    yield chunk

# ==================== 血缘分析流式处理 ====================
# 代码来源：text2metric_chain.py（原第1362-1377行）
async def lineage_stream_process(chunks, config):
    """血缘分析流式处理，保存血缘分析描述"""
    session_id = config['input']['session_id']
    index = config['metadata']['index']
    content = ''
    async for chunk in chunks:
        if isinstance(chunk, BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk) == str:
                content += chunk
        set_thought(session_id, f'lineage-analysis-description_{index}', {'chunk': content})
        yield chunk
    set_thought(session_id, f'lineage-analysis-description_{index}', {'chunk': content, 'end': True})
    await asyncio.sleep(thought_wait_time)
    yield chunk

# ==================== 关联分析流式处理 ====================
# 代码来源：text2metric_chain.py（原第1379-1394行）
async def link_stream_process(chunks, config):
    """关联分析流式处理，保存关联分析描述"""
    session_id = config['input']['session_id']
    index = config['metadata']['index']
    content = ''
    async for chunk in chunks:
        if isinstance(chunk, BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk) == str:
                content += chunk
        set_thought(session_id, f'metric-link-analysis-description_{index}', {'chunk': content})
        yield chunk
    set_thought(session_id, f'metric-link-analysis-description_{index}', {'chunk': content, 'end': True})
    await asyncio.sleep(thought_wait_time)
    yield chunk

