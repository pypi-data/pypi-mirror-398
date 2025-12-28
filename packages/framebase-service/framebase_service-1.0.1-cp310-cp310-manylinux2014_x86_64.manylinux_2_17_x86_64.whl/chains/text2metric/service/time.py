# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第304-321行（time_records）、第1640-1802行（time_intent）、
         第2078-2208行（time_comparison_processor）
功能说明：时间处理业务逻辑 - 包含时间记录获取、时间意图识别、时间比较处理
注意：时间工具函数（strptime, time2str, check_date等）和时间验证函数已移至 core/time_utils.py
重构日期：2024-12-19
"""
import json
import pkg_resources
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
    chain as chain_decorator,
)
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.values import RunnableValue

from chains.text2metric.core.infrastructure import (
    metric_service,
    model_binding,
    hold_stream,
)
from chains.text2metric.core.time_utils import (
    time_level,
    strptime,
    time2str,
    is_today,
    check_comparisons_in_question,
    limit_time_filters,
)
from chains.analytic_metric_chain import time_convert
from utils.logger import logger
from utils.exceptions import APICallError, APICallTimeOutError, MetricDateQueryError

# ==================== 时间记录获取 ====================
# 代码来源：text2metric_chain.py（原第304-321行）
@chain_decorator
def get_metric_time_records(x, config):
    """
    获取指标的时间记录列表
    
    该Chain用于查询每个指标在数据库中实际可用的时间点列表。
    时间记录是后续时间意图识别和时间验证的基础，用于：
    - 验证用户指定的时间是否在指标数据范围内
    - 提供时间选择的候选列表给LLM
    - 当用户时间超出范围时，自动替换为最近可用时间
    
    输入:
        x: 包含metric_infos或metric_query的字典
        config: 配置字典，包含headers.cookie用于API认证
    
    输出:
        x['time_records']: 字典，key为metric_id，value为该指标的时间记录列表（已排序）
        例如: {'metric_123': ['2024-01', '2024-02', '2024-03'], ...}
    
    异常处理:
        - APICallError: API调用失败时抛出MetricDateQueryError
        - APICallTimeOutError: API调用超时时抛出MetricDateQueryError
    
    使用场景:
        - 在time_intent之前调用，为时间意图识别提供数据基础
        - 在查询构建时调用，用于验证时间有效性
    """
    x['time_records'] = {}
    # 从metric_infos或metric_query中提取metric_ids
    if 'metric_infos' in x:
        metric_ids = [m['metricId'] for m in x['metric_infos']]
    else:
        metric_ids = [n for m in x['metric_query'] for n in m['metricIdList']]
    
    # 为每个指标查询时间记录
    try:
        for metric_id in metric_ids:
            _time_records = metric_service.metric_time_query(metric_id, config.get('headers', {}).get('cookie'))
            x['time_records'][metric_id] = sorted(_time_records)
    except APICallError as e:
        logger.error(f'get_metric_time_records error: {e}')
        raise MetricDateQueryError(f"Metric dates query failed: {metric_id}")
    except APICallTimeOutError as e:
        logger.error(f'get_metric_time_records timeout error: {e}')
        raise MetricDateQueryError(f"Metric dates query failed: {metric_id}")
    return x

# ==================== 时间工具函数 ====================
# 所有时间工具函数已移至 core/time_utils.py，包括：
# - strptime, time2str, convert_date_format（时间格式转换）
# - check_date, check_aggregation, check_sorting, check_limit（时间验证）
# - reset_date_by_time_filters, limit_time_filters（时间过滤器处理）

# ==================== 时间意图识别 ====================
# 代码来源：text2metric_chain.py（原第1640-1802行）
@chain_decorator
async def time_intent(x, config):
    """
    时间意图识别Chain
    
    该Chain是时间处理的核心业务逻辑，负责：
    1. 解析用户问题中的时间信息（从time_recognizer获取）
    2. 为每个指标计算合适的时间窗口（windowDate）
    3. 根据时间窗口和时间记录，过滤出可用的时间点（time_filters）
    4. 识别时间比较需求（同比、环比等）
    5. 使用LLM进一步细化时间选择（如果需要）
    
    处理流程：
    1. 基础时间处理：
       - 从time_recognizer提取startDate、endDate、time_unit
       - 对于每个指标，计算windowDate（考虑指标time_interval和用户time_unit）
       - 根据startDate和endDate，从time_records中过滤出可用时间点
    
    2. LLM辅助时间选择（如果time_records存在）：
       - 加载时间选择模板（metric_time_tool.json）
       - 根据指标类型（累加/非累加）和窗口类型，生成动态提示
       - 调用LLM让用户选择具体的离散时间点或时间区间
       - 使用limit_time_filters函数限制选择结果在time_records范围内
    
    3. 时间比较识别（如果问题中包含比较词）：
       - 加载时间比较模板（metric_comparisons_intent.json）
       - 识别比较类型：固定日期对比（t1 vs t2）或周期对比（同比/环比）
       - 调用LLM识别具体的比较时间点
    
    输入:
        x: 包含以下字段：
            - time_records: 每个指标的时间记录（从get_metric_time_records获取）
            - time_recognizer: 时间识别结果，包含startDate、endDate、time_unit、pre_thinking
            - metric_infos: 指标信息列表
            - question: 用户问题
    
    输出:
        RunnableParallel，包含以下字段：
            - startDate: 每个指标的起始日期字典 {metric_id: '2024-01-01'}
            - endDate: 每个指标的结束日期字典 {metric_id: '2024-12-31'}
            - windowDate: 每个指标的窗口日期类型字典 {metric_id: 'MONTH'}
            - time_records: 原始时间记录字典
            - time_warning: 时间警告列表
            - time_filters_{metric_id}: 每个指标的时间过滤器Chain（如果time_records存在）
            - comparisons_{metric_id}: 每个指标的时间比较Chain（如果问题包含比较词）
    
    业务规则：
        - windowDate选择规则：
          * 如果time_unit为'None'，使用指标的time_interval
          * 如果time_level[time_interval] > time_level[time_unit]，使用time_interval（指标粒度更细）
          * 否则使用time_unit（用户要求的粒度可用）
        
        - 累加指标的特殊处理：
          * 如果windowDate粒度大于time_interval，只需要每个windowDate的最新time_interval时间点
          * 例如：月累指标，用户要求按年查询，只需每年最后一个月的日期
        
        - 非累加指标的特殊处理：
          * 如果windowDate粒度大于time_interval，需要所有time_interval时间点
          * 例如：日指标，用户要求按月查询，需要该月所有日期
    """

    time_records = x['time_records']
    startDate = x['time_recognizer'].get('startDate')
    endDate = x['time_recognizer'].get('endDate')
    time_unit = x['time_recognizer'].get('time_unit')
    time_insight = x['time_recognizer'].get('pre_thinking') or ''

    time_filters = {}
    _time_filters = {}
    output_startDate = {}
    output_endDate = {}
    comparisons = {}
    windowDate = {}
    time_warning = []
    
    # set time_filters and windowDate
    for metric_info in x['metric_infos']:
        if not time_records[metric_info['metricId']]:
            _latest_date = datetime.now()
            if metric_info['time_interval'] == 'DAY':
                latest_date = _latest_date.strftime('%Y-%m-%d')
            elif metric_info['time_interval'] == 'MONTH':
                latest_date = _latest_date.strftime('%Y-%m')
            elif metric_info['time_interval'] == 'YEAR':
                latest_date = _latest_date.strftime('%Y')
            elif metric_info['time_interval'] == 'QUARTER':
                latest_date = _latest_date.strftime('%Y-%m')
        else:
            _latest_date = strptime(time_records[metric_info['metricId']][-1], metric_info['time_interval'])
            latest_date = time_records[metric_info['metricId']][-1]
        
        _startDate, _endDate = time_convert(startDate, endDate, _latest_date)
        if not _startDate:
            _startDate = latest_date
            if not is_today(_startDate):
                time_warning.append({'miss': '', 'replace': latest_date, 'msg': f'缺少{datetime.now().strftime("%Y-%m-%d")}的数据，已替换数据库中最新的日期：{latest_date}'})
        if not _endDate:
            _endDate = latest_date
            if not is_today(_endDate):
                time_warning.append({'miss': '', 'replace': latest_date, 'msg': f'缺少{datetime.now().strftime("%Y-%m-%d")}的数据，已替换数据库中最新的日期：{latest_date}'})
        _time_filters[metric_info['metricId']] = []
        if time_unit == 'None':
            windowDate[metric_info['metricId']] = metric_info['time_interval']
        elif time_level[metric_info['time_interval']] > time_level[time_unit]:
            windowDate[metric_info['metricId']] = metric_info['time_interval']
        else:
            windowDate[metric_info['metricId']] = time_unit
        date_range = strptime(_startDate, metric_info['time_interval'], end=False), strptime(_endDate, metric_info['time_interval'], end=True)
        for time_record in time_records[metric_info['metricId']]:
            try:
                _time_record = strptime(time_record, metric_info['time_interval'])
                if date_range[0] <= _time_record <= date_range[1]:
                    _time_filters[metric_info['metricId']].append(time_record)
            except (ValueError, TypeError):
                # 如果时间解析失败，跳过该时间记录
                continue
        
        # 去重并排序时间过滤器
        _time_filters[metric_info['metricId']] = sorted(list(set(_time_filters[metric_info['metricId']])))
        output_startDate[metric_info['metricId']] = _startDate
        output_endDate[metric_info['metricId']] = _endDate
    
    # 如果有时间记录，使用LLM进一步细化时间选择
    if time_records:
        with open(pkg_resources.resource_filename('configs', f'chain/metric_time_tool.json'), 'r', encoding='utf-8') as f:
            json_schema = json.load(f)
        for i, metric_info in enumerate(x['metric_infos']):
            _json_schema = deepcopy(json_schema)
            if metric_info['is_accumulative']:
                if time_level[windowDate[metric_info['metricId']]] < time_level[metric_info['time_interval']]:
                    metric_requirement = f"用户希望查询指标【{metric_info['name']}】的{windowDate[metric_info['metricId']]}度数据，但是【{metric_info['name']}】是{metric_info['time_interval']}度指标。请选择合适的时间区间或离散的时间点。"
                elif time_level[windowDate[metric_info['metricId']]] > time_level[metric_info['time_interval']]:
                    metric_requirement = f"用户希望查询指标【{metric_info['name']}】的{windowDate[metric_info['metricId']]}度数据，但是【{metric_info['name']}】是累加指标，所以只需要给出每{windowDate[metric_info['metricId']]}的最新的{metric_info['time_interval']}的离散时间即可。"
                else:
                    metric_requirement = f"用户希望查询指标【{metric_info['name']}】的{windowDate[metric_info['metricId']]}度数据，请选择合适的时间区间或离散的时间点。"
            else:
                if time_level[windowDate[metric_info['metricId']]] < time_level[metric_info['time_interval']]:
                    metric_requirement = f"用户希望查询指标【{metric_info['name']}】的{windowDate[metric_info['metricId']]}度数据，但是【{metric_info['name']}】是{metric_info['time_interval']}度指标。请选择合适的时间区间或离散的时间点。"
                elif time_level[windowDate[metric_info['metricId']]] > time_level[metric_info['time_interval']]:
                    metric_requirement = f"用户希望查询指标【{metric_info['name']}】的{windowDate[metric_info['metricId']]}度数据，【{metric_info['name']}】是非累加指标，所以需要给出每{windowDate[metric_info['metricId']]}的所有的{metric_info['time_interval']}的**连续时间**。"
                else:
                    metric_requirement = f"用户希望查询指标【{metric_info['name']}】的{windowDate[metric_info['metricId']]}度数据，请选择合适的时间区间或离散的时间点。"

            if _time_filters[metric_info['metricId']]:
                _json_schema['properties']['pre_thinking']['description'] = _json_schema['properties']['pre_thinking']['description'].replace('{latest_date}', _time_filters[metric_info['metricId']][-1]).replace('{metric_requirement}', metric_requirement)
                time_filters[metric_info['metricId']] = RunnablePassthrough.assign(
                    json_schema=lambda x, v=_json_schema: v,
                    time_records=lambda x, v=_time_filters[metric_info['metricId']]: v,
                    template_name=RunnableValue(value='metric_query_select_time_template'),
                    question=lambda x, v=metric_info['name']: x['question'].replace(v, f'[{v}]'),
                    current_time_info=lambda x, v=datetime.now().strftime('%Y-%m-%d'): v,
                ) | model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser() | \
                RunnableLambda(lambda x, v=_time_filters[metric_info['metricId']], w=metric_info['time_interval']: limit_time_filters(x, v, w))
            else:
                time_filters[metric_info['metricId']] = lambda x: []
                
    if check_comparisons_in_question(x['question']):
        _logger = RunnablePassthrough(lambda x: logger.info(f"time_comparisons: {x}"))
        with open(pkg_resources.resource_filename('configs', f'chain/metric_comparisons_intent.json'), 'r', encoding='utf-8') as f:
            json_schema = json.load(f)
        if not any(word in x['question'] for word in ['同比', '环比']):
            json_schema['properties']['timeComparisons_pre_thinking']['description'] = json_schema['properties']['timeComparisons_pre_thinking']['description'].replace('{fixedDate_thinking}', '3.请判断文字顺序。用户问题中对比词有表示对比的词（类如"较"，"相较于"），请判断对比词左边和右边的时间点是什么。如果只有一个时间，那么默认是当前时间比较其他时间。请分别回答对比词左边的时间点和右边的时间点是什么？另外，判断对比的时间点时，如果用户要求按照月度对比，请依次给出每一组相邻的月份的对比。')
            json_schema['properties']['timeComparisons']['items']['oneOf'] = json_schema['properties']['timeComparisons']['items']['oneOf'][:1]
        else:
            json_schema['properties']['timeComparisons']['items']['oneOf'] = json_schema['properties']['timeComparisons']['items']['oneOf'][1:2]
            json_schema['properties']['timeComparisons_pre_thinking']['description'] = json_schema['properties']['timeComparisons_pre_thinking']['description'].replace('{fixedDate_thinking}', '')
            
        for i, metric_info in enumerate(x['metric_infos']):
            _json_schema = deepcopy(json_schema)
            if time_level[windowDate[metric_info['metricId']]] != time_level[metric_info['time_interval']]:
                if any(word in x['question'] for word in ['同比', '环比']):
                    _json_schema['properties']['timeComparisons']['items']['oneOf'][0]['properties'].pop('t')
                elif not metric_info['is_accumulative']:
                    continue
            dynamic_requirements = ''
            if metric_info['is_accumulative']:
                dynamic_requirements = f"当前的指标是累加指标，所以需要给出每{windowDate[metric_info['metricId']]}的最新的{metric_info['time_interval']}粒度的时间。"
            
            now = time2str(datetime.now(), metric_info['time_interval'])
            comparisons[metric_info['metricId']] = RunnablePassthrough.assign(
                json_schema=lambda x, v=_json_schema: v,
                time_records=lambda x, v=_time_filters[metric_info['metricId']]: sorted(list(set(v + [now]))),
                template_name=RunnableValue(value='metric_comparison_check_template'),
                time_insight=lambda x, v=time_insight: v,
                dynamic_requirements=lambda x, v=dynamic_requirements: v,
                question=lambda x, v=metric_info['name']: x['question'].replace(v, f'[{v}]'),
                current_date=lambda x, v=now: now,
            ) | model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser() | _logger
        
    result = {}
    result['startDate'] = lambda x, v=output_startDate: v
    result['endDate'] = lambda x, v=output_endDate: v
    result['windowDate'] = lambda x, v=windowDate: v
    result['time_records'] = lambda x, v=time_records: v
    result['time_warning'] = lambda x, v=time_warning: v
    for metric_id in comparisons:
        result[f'comparisons_{metric_id}'] = comparisons[metric_id]
    for metric_id in time_filters:
        result[f'time_filters_{metric_id}'] = time_filters[metric_id]
    return RunnableParallel(**result)

# ==================== 时间比较处理 ====================
# 代码来源：text2metric_chain.py（原第2078-2208行）
# 注意：此函数目前未被使用，时间比较处理逻辑已集成到 query_builder.py 的 make_metric_query 函数中（第82-210行）
# 保留此函数作为参考，如需使用请确保逻辑与 make_metric_query 保持一致
def process_time_comparisons(x, passthrough):
    """
    处理时间比较逻辑
    
    该函数处理时间比较的复杂业务逻辑，将LLM识别的时间比较意图转换为查询可用的格式。
    
    支持两种比较类型：
    1. fixedDate（固定日期对比）：
       - 格式：{comparisonType: 'fixedDate', sourceDataDate: ['2024-01'], targetDataDate: ['2024-02']}
       - 含义：对比sourceDataDate和targetDataDate的数据
       - 示例：用户查询"1月和2月的销售额对比"
    
    2. period（周期对比）：
       - 格式：{comparisonType: 'period', comparisonInterval: 1, comparisonTimeUnit: 'MONTH', time_filters: ['2024-02']}
       - 含义：对比指定时间点和往前N个周期的时间点
       - 示例：用户查询"2月环比" -> 对比2024-02和2024-01
    
    处理逻辑：
    1. 分类比较项：将所有timeComparisons分为fixedDate和period两类
    2. 多比较项合并：
       - 多个period比较：合并所有比较时间点到time_filters中
       - 多个fixedDate比较：合并为第一个，将所有日期加入time_filters
    3. 单一比较项：直接使用，并提取相关时间到time_filters
    4. 空比较项：设置为空字典
    
    参数:
        x: 包含time_intent的字典，time_intent.comparisons结构为：
           {metric_id: {'timeComparisons': [{...}, ...]}}
        passthrough: 透传数据，包含metric_infos用于获取指标信息
    
    返回:
        time_warning: 时间警告字典，目前返回空字典（警告在query_builder中生成）
    
    注意:
        - 该函数会原地修改x['time_intent']['comparisons']和x['time_intent']['time_filters']
        - 对于period比较，会根据comparisonInterval和comparisonTimeUnit计算对比时间点
        - 例如：comparisonInterval=1, comparisonTimeUnit='MONTH'，表示往前推1个月
    """
    time_warning = defaultdict(list)
    # reset time_filters if comparisons is not empty
    for metric_id in x['time_intent']['comparisons']:
        metric_info = list(filter(lambda m: m['metricId'] == metric_id, passthrough['metric_infos']))[0]
        fixed_date_comparisons = []
        period_comparisons = []
        for item in x['time_intent']['comparisons'][metric_id].get('timeComparisons', []):
            result = {}
            if item.get('t1') and item.get('t2'):
                result['comparisonType'] = 'fixedDate'
                if not result.get('sourceDataDate'):
                    result['sourceDataDate'] = []
                result['sourceDataDate'].append(item['t1'])
                if not result.get('targetDataDate'):
                    result['targetDataDate'] = []
                result['targetDataDate'].append(item['t2'])
                fixed_date_comparisons.append(result)
            elif item.get('periodUnit') and item.get('periodQuantity'):
                result['comparisonType'] = 'period'
                result['comparisonInterval'] = item['periodQuantity']
                result['comparisonTimeUnit'] = item['periodUnit']
                if item.get('t'):
                    result['time_filters'] = [item.get('t')]
                    result['t'] = item.get('t')
                else:
                    result['time_filters'] = []
                period_comparisons.append(result)
        if len(period_comparisons) > 1:
            x['time_intent']['comparisons'][metric_id] = {}
            comparisons_time_filters = []
            for item in period_comparisons:
                if item.get('t'):
                    date = strptime(item['t'], metric_info['time_interval'])
                    if item['comparisonInterval'] == 'YEAR':
                        date = date - relativedelta(years=item['comparisonTimeUnit'])
                    elif item['comparisonInterval'] == 'MONTH':
                        date = date - relativedelta(months=item['comparisonTimeUnit'])
                    elif item['comparisonInterval'] == 'DAY':
                        date = date - relativedelta(days=item['comparisonTimeUnit'])
                    comparisons_time_filters.append(time2str(date, metric_info['time_interval']))
            if comparisons_time_filters:
                x['time_intent']['time_filters'][metric_id] = comparisons_time_filters
        elif len(fixed_date_comparisons) > 1:
            x['time_intent']['comparisons'][metric_id] = fixed_date_comparisons[0]
            x['time_intent']['time_filters'][metric_id] = [*fixed_date_comparisons[0]['sourceDataDate'], *fixed_date_comparisons[0]['targetDataDate']]
            for item in fixed_date_comparisons[1:]:
                for date in item['sourceDataDate']:
                    x['time_intent']['time_filters'][metric_id].append(date)
                    x['time_intent']['comparisons'][metric_id]['sourceDataDate'].append(date)
                for date in item['targetDataDate']:
                    x['time_intent']['time_filters'][metric_id].append(date)
                    x['time_intent']['comparisons'][metric_id]['targetDataDate'].append(date)
            x['time_intent']['comparisons'][metric_id]['sourceDataDate'] = sorted(list(set(x['time_intent']['comparisons'][metric_id]['sourceDataDate'])))
            x['time_intent']['comparisons'][metric_id]['targetDataDate'] = sorted(list(set(x['time_intent']['comparisons'][metric_id]['targetDataDate'])))
        elif len(fixed_date_comparisons):
            x['time_intent']['time_filters'][metric_id] = []
            x['time_intent']['time_filters'][metric_id].append(time2str(strptime(fixed_date_comparisons[0]['sourceDataDate'][0], metric_info['time_interval']), metric_info['time_interval']))
            x['time_intent']['time_filters'][metric_id].append(time2str(strptime(fixed_date_comparisons[0]['targetDataDate'][0], metric_info['time_interval']), metric_info['time_interval']))
            x['time_intent']['comparisons'][metric_id] = fixed_date_comparisons[0]
        elif len(period_comparisons):
            if period_comparisons[0].get('t'):
                x['time_intent']['time_filters'][metric_id] = []
            x['time_intent']['comparisons'][metric_id] = period_comparisons[0]
        else:
            x['time_intent']['comparisons'][metric_id] = {}
    return time_warning

