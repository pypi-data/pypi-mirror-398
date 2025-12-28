# cython: annotation_typing = False
"""
时间工具函数 - Time Utilities
代码来源：chains/text2metric_chain.py
原始行数：第323-366行（time_utils）、第1024-1048行（time_utils）、
         第1425-1444行（time_utils）、第1625-1638行（time_utils）、
         第368-419行（time_validator）
功能说明：时间处理相关的通用工具函数，用于时间转换、时间验证、时间比较等
创建日期：2024-12-19
"""
from calendar import monthrange
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from itertools import groupby
import jieba

# ==================== 时间级别常量 ====================
# 代码来源：text2metric_chain.py（原第1625-1635行）
# 时间级别映射：用于比较不同时间粒度的大小关系
# 值越大，时间粒度越大（YEAR > QUARTER > MONTH > DAY）
time_level = {'DAY': 1, "MONTH": 2, "QUARTER": 3, "YEAR": 4}


# ==================== 时间格式转换 ====================
# 代码来源：text2metric_chain.py（原第337-366行）
def convert_date_format(date_str: str, window_date: str, end: bool = False) -> str:
    """
    转换日期格式到指定的窗口日期类型
    
    该函数用于统一日期格式，根据窗口日期类型（window_date）将日期字符串转换为对应格式：
    - DAY/日: 转换为 'YYYY-MM-DD' 格式
    - MONTH/月: 转换为 'YYYY-MM' 格式
    - YEAR/年: 转换为 'YYYY' 格式
    - QUARTER/季度: 转换为 'YYYY-MM' 格式（季度首月）
    
    如果输入日期不完整，会根据窗口类型和是否为结束日期进行补全：
    - 对于开始日期（end=False）：补全为最小日期（如 '2024' -> '2024-01-01'）
    - 对于结束日期（end=True）：补全为最大日期（如 '2024' -> '2024-12-31'）
    
    参数:
        date_str: 日期字符串，可能格式为 'YYYY-MM-DD', 'YYYY-MM', 或 'YYYY'
        window_date: 窗口日期类型，支持 'DAY'/'日', 'MONTH'/'月', 'YEAR'/'年', 'QUARTER'/'季度'
        end: 是否为结束日期，影响补全策略
    
    返回:
        转换后的日期字符串，格式符合window_date要求
    
    示例:
        >>> convert_date_format('2024-12-19', 'DAY')
        '2024-12-19'
        >>> convert_date_format('2024-12-19', 'MONTH')
        '2024-12'
        >>> convert_date_format('2024', 'MONTH', end=False)
        '2024-01'
        >>> convert_date_format('2024', 'MONTH', end=True)
        '2024-12'
    """
    if window_date == 'DAY' or window_date == '日':
        if len(date_str) >= 10:
            date_str = date_str[:10]
        elif len(date_str) == 7:
            date_str += '-01'
        elif len(date_str) == 4:
            if end:
                date_str += '-12-31'
            else:
                date_str += '-01-01'
    elif window_date == 'MONTH' or window_date == '月':
        if len(date_str) >= 7:
            date_str = date_str[:7]
        elif len(date_str) == 4:
            if end:
                date_str += f'-12'
            else:
                date_str += '-01'
    elif window_date == 'YEAR' or window_date == '年':
        date_str = date_str[:4]
    elif window_date == 'QUARTER' or window_date == '季度':
        if len(date_str) >= 7:
            date_str = date_str[:7]
        elif len(date_str) == 4:
            if end:
                date_str += f'-12'
            else:
                date_str += '-01'
    return date_str


# 代码来源：text2metric_chain.py（原第1024-1048行）
def strptime(date_str: str, time_interval: str, end: bool = False) -> datetime:
    """
    解析日期字符串为datetime对象
    
    该函数是标准库datetime.strptime的扩展版本，支持指标查询中的时间间隔类型。
    对于不同时间间隔，返回的datetime对象会精确定位到区间的开始或结束时间：
    
    - DAY: 开始时间 00:00:00，结束时间 23:59:59
    - MONTH: 开始时间为月初 1日 00:00:00，结束时间为月末最后一天 23:59:59
    - YEAR: 开始时间为年初 1月1日 00:00:00，结束时间为年末 12月31日 23:59:59
    - QUARTER: 季度开始时间为季度首月1日，结束时间为季度末月最后一天 23:59:59
    
    参数:
        date_str: 日期字符串，格式可以是 'YYYY-MM-DD', 'YYYY-MM', 或 'YYYY'
        time_interval: 时间间隔类型，支持 'DAY'/'日', 'MONTH'/'月', 'YEAR'/'年', 'QUARTER'/'季度'
        end: 是否为结束日期，True返回区间结束时间，False返回区间开始时间
    
    返回:
        datetime对象，时间已精确定位到对应时间区间的开始或结束
    
    示例:
        >>> strptime('2024-12-19', 'DAY', end=False)
        datetime.datetime(2024, 12, 19, 0, 0, 0)
        >>> strptime('2024-12', 'MONTH', end=True)
        datetime.datetime(2024, 12, 31, 23, 59, 59)
        >>> strptime('2024', 'YEAR', end=False)
        datetime.datetime(2024, 1, 1, 0, 0, 0)
    """
    date_str = convert_date_format(date_str, time_interval, end)
    if time_interval == 'DAY' or time_interval == '日':
        return datetime.strptime(date_str, '%Y-%m-%d')
    elif time_interval == 'MONTH' or time_interval == '月':
        year, month = map(int, date_str.split('-'))
        if end:
            day = monthrange(year, month)[1]
            return datetime(year, month, day, 23, 59, 59)
        else:
            return datetime(year, month, 1, 0, 0, 0)
    elif time_interval == 'YEAR' or time_interval == '年':
        if end:
            return datetime.strptime(date_str, '%Y').replace(month=12, day=31, hour=23, minute=59, second=59)
        else:
            return datetime.strptime(date_str, '%Y').replace(month=1, day=1, hour=0, minute=0, second=0)
    elif time_interval == 'QUARTER' or time_interval == '季度':
        year, month = map(int, date_str.split('-'))
        last_month = month + 2 if month % 3 != 0 else month
        last_month = last_month if last_month <= 12 else 12
        if end:
            last_day = monthrange(year, last_month)[1]
            return datetime(year, last_month, last_day, 23, 59, 59)
        else:
            return datetime(year, month, 1, 0, 0, 0)


# 代码来源：text2metric_chain.py（原第1625-1635行）
def time2str(time_record: datetime, time_interval: str) -> str:
    """
    将datetime对象转换为指定时间间隔格式的字符串
    
    该函数与strptime互为逆操作，根据时间间隔类型将datetime对象转换为对应格式的字符串：
    - DAY: 'YYYY-MM-DD'
    - MONTH: 'YYYY-MM'
    - YEAR: 'YYYY'
    - QUARTER: 'YYYY-MM'（季度首月）
    
    参数:
        time_record: datetime对象
        time_interval: 时间间隔类型，支持 'DAY'/'日', 'MONTH'/'月', 'YEAR'/'年', 'QUARTER'/'季度'
    
    返回:
        日期字符串，格式符合time_interval要求
    
    示例:
        >>> time2str(datetime(2024, 12, 19), 'DAY')
        '2024-12-19'
        >>> time2str(datetime(2024, 12, 19), 'MONTH')
        '2024-12'
        >>> time2str(datetime(2024, 12, 19), 'YEAR')
        '2024'
    """
    if time_interval == 'DAY' or time_interval == '日':
        return time_record.strftime('%Y-%m-%d')
    elif time_interval == 'MONTH' or time_interval == '月':
        return time_record.strftime('%Y-%m')
    elif time_interval == 'YEAR' or time_interval == '年':
        return time_record.strftime('%Y')
    elif time_interval == 'QUARTER' or time_interval == '季度':
        return time_record.strftime('%Y-%m')


# 代码来源：text2metric_chain.py（原第260-271行，在analysis_service函数中）
# 迁移路径：text2metric_chain.py → service/analysis.py → core/time_utils.py
def subtract_minimum_unit(date_str: str) -> str:
    """
    从日期字符串中减去一年，保持原始格式
    
    参数:
        date_str: 日期字符串，格式为 'YYYY-MM-DD', 'YYYY-MM' 或 'YYYY'
    
    返回:
        减去一年后的日期字符串，格式与输入相同
    """
    date = parse(date_str)
    new_date = date - relativedelta(years=1)
    if len(date_str) == 10:
        return new_date.strftime('%Y-%m-%d')
    elif len(date_str) == 7:
        return new_date.strftime('%Y-%m')
    elif len(date_str) == 4:
        return new_date.strftime('%Y')
    return date_str


# ==================== 时间比较 ====================
# 代码来源：text2metric_chain.py（原第1425-1444行）
def is_date_after_today(date_str: str) -> bool:
    """
    判断日期是否在今天之后
    
    参数:
        date_str: 日期字符串
    
    返回:
        如果日期在今天之后返回True，否则返回False
    """
    given_date = parse(date_str).date()
    today = datetime.today().date()
    return given_date > today


def is_date_before_today(date_str: str) -> bool:
    """
    判断日期是否在今天之前
    
    参数:
        date_str: 日期字符串
    
    返回:
        如果日期在今天之前返回True，否则返回False
    """
    given_date = parse(date_str).date()
    today = datetime.today().date()
    return given_date < today


def is_today(date_str: str) -> bool:
    """
    判断日期是否是今天
    
    参数:
        date_str: 日期字符串
    
    返回:
        如果日期是今天返回True，否则返回False
    """
    given_date = parse(date_str).date()
    today = datetime.today().date()
    return given_date.day == today.day and given_date.month == today.month and given_date.year == today.year


# 代码来源：text2metric_chain.py（原第1637-1638行）
def check_comparisons_in_question(question: str) -> bool:
    """
    检查问题中是否包含比较相关的词汇
    
    参数:
        question: 用户问题字符串
    
    返回:
        如果包含比较词返回True，否则返回False
    """
    return any(word in jieba.lcut(question) for word in ['比', '较', '同比', '环比', '相比', '相较', '对比', '比起'])


# ==================== 时间验证 ====================
# 代码来源：text2metric_chain.py（原第368-375行）
def check_aggregation(x: dict) -> dict:
    """
    检查并修正聚合方式
    
    参数:
        x: 查询字典，会被原地修改
    
    返回:
        更新后的查询字典
    """
    if x['is_accumulative']:
        x['aggregation'] = 'NONE'
    if x.get('unit') == '%' and x.get('metricType') != 2:
        x['aggregation'] = 'NONE'
    if x.get('is_point_metric') or x['windowDate'] == 'YEAR':
        x['aggregation'] = 'NONE'
    return x


# 代码来源：text2metric_chain.py（原第377-380行）
def check_sorting(x: dict) -> dict:
    """
    检查并修正排序方式
    
    参数:
        x: 查询字典，会被原地修改
    
    返回:
        更新后的查询字典
    """
    if x.get('sorting') and x.get('aggregation') and x.get('aggregation') != 'NONE':
        x['sorting'] = []
    return x


# 代码来源：text2metric_chain.py（原第382-385行）
def check_limit(x: dict) -> dict:
    """
    检查并设置默认限制数量
    
    参数:
        x: 查询字典，会被原地修改
    
    返回:
        更新后的查询字典
    """
    if not x.get('limit'):
        x['limit'] = 100000
    return x


# 代码来源：text2metric_chain.py（原第387-419行）
def check_date(x: dict) -> dict:
    """
    检查并修正查询字典中的日期有效性
    
    该函数是查询构建过程中日期验证的核心函数，执行以下操作：
    1. 处理累加指标的时间窗口调整：如果windowDate与time_interval不一致，需要调整timeFilters
    2. 处理百分比指标和点指标：强制使用time_interval作为windowDate
    3. 清理临时字段：删除date_pre_thinking
    4. 日期补全：如果startDate或endDate为空，互相补全
    5. 格式统一：将所有日期转换为windowDate格式
    6. 日期交换：如果startDate > endDate，自动交换
    
    业务规则：
    - 累加指标：如果windowDate粒度小于time_interval，需要在每个windowDate区间内选择最后一个time_interval时间点
    - 百分比指标（非类型2）和点指标：必须使用time_interval作为windowDate，不允许聚合
    - 时间比较的日期也需要统一格式转换
    
    参数:
        x: 查询字典，包含以下字段：
            - windowDate: 窗口日期类型
            - time_interval: 指标的时间间隔类型
            - is_accumulative: 是否为累加指标
            - unit: 指标单位
            - metricType: 指标类型
            - is_point_metric: 是否为点指标
            - startDate: 开始日期
            - endDate: 结束日期
            - timeFilters: 时间过滤器列表
            - comparisons: 时间比较配置（可选）
    
    返回:
        更新后的查询字典，所有日期字段已统一格式并验证
    
    注意:
        该函数会原地修改输入字典x，不会创建新字典
    """
    time_length = {'YEAR': 4, 'MONTH': 7, 'DAY': 10, 'QUARTER': 7}
    if x['windowDate'] != x['time_interval'] and x['is_accumulative']:
        _timeFilters = []
        for key, group in groupby(x['timeFilters'], key=lambda m: m[:time_length[x['windowDate']]]):
            _timeFilters.append(list(group)[-1])
        x['timeFilters'] = _timeFilters
        x['windowDate'] = x['time_interval']
    if x['unit'] == '%' and x['metricType'] != 2 or x.get('is_point_metric'):
        x['windowDate'] = x['time_interval']
    if 'date_pre_thinking' in x:
        x.pop('date_pre_thinking')
    if not x['endDate']:
        x['endDate'] = x['startDate']
    if not x['startDate']:
        x['startDate'] = x['endDate']
    if x['startDate']:
        x['startDate'] = convert_date_format(x['startDate'], x['windowDate'])
    if x['endDate']:
        x['endDate'] = convert_date_format(x['endDate'], x['windowDate'], end=True)
    if x['timeFilters']:
        for i, time_record in enumerate(x['timeFilters']):
            x['timeFilters'][i] = convert_date_format(time_record, x['time_interval'])
    if x['comparisons']:
        if x['comparisons']['comparisonType'] == 'fixedDate':
            for i, date in enumerate(x['comparisons']['sourceDataDate']):
                x['comparisons']['sourceDataDate'][i] = convert_date_format(date, x['windowDate'])
            for i, date in enumerate(x['comparisons']['targetDataDate']):
                x['comparisons']['targetDataDate'][i] = convert_date_format(date, x['windowDate'])
    if x.get('startDate') and x.get('endDate'):
        if strptime(x['startDate'], x['windowDate']) > strptime(x['endDate'], x['windowDate']):
            x['startDate'], x['endDate'] = x['endDate'], x['startDate']
    return x


# 代码来源：text2metric_chain.py（原第323-335行）
def reset_date_by_time_filters(x: dict, time_records: list) -> dict:
    """
    根据时间过滤器重置开始和结束日期
    
    该函数用于处理用户明确指定了timeFilters（离散时间点列表）的情况。
    函数会：
    1. 将timeFilters排序
    2. 使用timeFilters的第一个和最后一个时间点作为startDate和endDate
    3. 如果原始startDate或endDate不在time_records中，生成警告信息
    4. 去重警告信息
    
    使用场景：
    - 用户查询"2024年1月、3月、5月的销售额"时，timeFilters=['2024-01', '2024-03', '2024-05']
    - 此时startDate和endDate应该自动设置为'2024-01'和'2024-05'
    
    参数:
        x: 查询字典，包含以下字段：
            - timeFilters: 时间过滤器列表（可选）
            - windowDate: 窗口日期类型
            - startDate: 原始开始日期
            - endDate: 原始结束日期
            - metricName: 指标名称（用于生成警告信息）
            - warnings: 警告字典，包含time_warning列表
        time_records: 指标可用的时间记录列表，用于验证日期是否有效
    
    返回:
        更新后的查询字典，startDate和endDate已根据timeFilters重置，warnings已更新
    
    注意:
        - 如果timeFilters为空，函数不会修改startDate和endDate
        - 警告信息会追加到x['warnings']['time_warning']列表中
    """
    _start_date = x.get('startDate')
    _end_date = x.get('endDate')
    if x.get('timeFilters'):
        x['timeFilters'] = sorted(x['timeFilters'])
        x['startDate'] = convert_date_format(x['timeFilters'][0], x['windowDate'])
        x['endDate'] = convert_date_format(x['timeFilters'][-1], x['windowDate'], end=True)
        if _start_date != x['startDate'] and _start_date not in time_records:
            x['warnings']['time_warning'].append(f'{x["metricName"]}缺少{_start_date}的数据，已替换为：{x["startDate"]}')
        if _end_date != x['endDate'] and _end_date not in time_records:
            x['warnings']['time_warning'].append(f'{x["metricName"]}缺少{_end_date}的数据，已替换为：{x["endDate"]}')
        x['warnings']['time_warning'] = list(set(x['warnings']['time_warning']))
    return x


# 代码来源：text2metric_chain.py（原第159-188行）
# 迁移路径：text2metric_chain.py → service/time.py（time_intent内部函数）→ core/time_utils.py
def limit_time_filters(time_expression_result: dict, time_records: list, time_interval: str) -> list:
    """
    限制时间过滤器在可用时间记录范围内
    
    该函数用于处理LLM返回的时间表达式，将结果限制在实际可用的时间记录中。
    处理两种时间表达式类型：
    1. 时间范围（from-to）：在time_records中找到所有在范围内的时间点
    2. 单个时间点（time_value）：检查是否在time_records中
    
    如果没有任何有效结果，但有单个time_value，则使用time_records的最后一个时间点作为fallback。
    
    参数:
        time_expression_result: LLM返回的时间表达式结果字典，包含 'time_expression' 字段
        time_records: 可用的时间记录列表
        time_interval: 时间间隔类型，用于解析时间
    
    返回:
        过滤后的时间点列表，已排序并去重
    """
    from utils.logger import logger
    
    logger.info(f"limit_time_filters: {time_expression_result}")
    if not time_records:
        return []
    results = []
    for time_item in time_expression_result.get('time_expression', []):
        if time_item.get('from') and time_item.get('to'):
            date_range = strptime(time_item['from'], time_interval), strptime(time_item['to'], time_interval, end=True)
            for time_record in time_records:
                time_record = strptime(time_record, time_interval)
                if date_range[0] <= time_record <= date_range[1]:
                    results.append(time2str(time_record, time_interval))
        if time_item.get('time_value'):
            if time_item['time_value'] in time_records:
                results.append(time_item['time_value'])
    if not results and len(time_expression_result.get('time_expression', [])) == 1 and time_expression_result.get('time_expression')[0].get('time_value'):
        results.append(time_records[-1])
            
    results = sorted(list(set(results)))
    return results

