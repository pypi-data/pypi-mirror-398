# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第465-468行（check_analysis_intent）、第470-487行（router）、
         第1938-1954行（additional_intent）、第2059-2061行（raise_clarify_interupt_error）、
         第2381-2387行（router_clarify）、第2388-2393行（passthrough）
功能说明：意图处理 - 包含路由、意图识别、透传处理
注意：model_binding 已移至 core/infrastructure.py
重构日期：2024-12-19
"""
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableParallel,
    chain as chain_decorator,
)
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.values import RunnableValue
from app.admin_operation import get_global_config_info

from chains.text2metric.core.infrastructure import (
    model_binding,
    hold_stream,
)
from chains.text2metric.core.intent_utils import (
    load_chain_json_schema,
    should_remove_clarify_choices,
    remove_clarify_choices_from_schema,
    extract_clarify_choices,
)
from utils.logger import logger
from utils.exceptions import ClarifyInteruptError

# ==================== 分析意图检查 ====================
# 代码来源：text2metric_chain.py（原第465-468行）
def check_analysis_intent(x):
    """检查是否为归因分析意图"""
    if '归因分析' in x['question']:
        x['router_json']['intent'] = 'root cause analysis'
    return x

# ==================== 指标路由 ====================
# 代码来源：text2metric_chain.py（原第470-487行）
def metric_router(x):
    """
    指标路由Chain
    
    使用LLM识别用户意图（query/analysis/scroll/definition等）
    """
    metric_router_version = get_global_config_info('metric_router_version') or 'metric_router.json'
    router_schema = load_chain_json_schema(metric_router_version)
    if should_remove_clarify_choices(x):  # 移除澄清选项（如果配置要求）
        remove_clarify_choices_from_schema(router_schema)
    return RunnablePassthrough.assign(router_json=
                RunnablePassthrough.assign(template_name=RunnableValue(value='metric_router_template'),
                                        model_name=RunnableValue(value='metric_to_text_llm'),
                                        json_schema=lambda x, v=router_schema: v) |
                model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser()) | \
    check_analysis_intent | \
    RunnablePassthrough.assign(intent=lambda x: x['router_json']['intent']) | \
    RunnablePassthrough(lambda x: logger.debug(f"router_reuslt: {x.get('router_json')}"))

# ==================== 额外意图 ====================
# 代码来源：text2metric_chain.py（原第1938-1954行）
@chain_decorator
async def additional_intent(x):
    """
    额外意图识别Chain
    
    为每个指标识别额外的查询需求（如排序、聚合等）
    """
    _logger = RunnablePassthrough(lambda x: logger.info(f"additional_intent: {x}"))
    json_schema = load_chain_json_schema('metric_additional_intent.json')
    branches = {}
    for i, metric_info in enumerate(x['metric_infos']):
        branches[metric_info['metricId']] = RunnablePassthrough.assign(
            json_schema=lambda x, v=json_schema: v,
            metric_name=lambda x, v=metric_info['name']: v,
            metric_unit=lambda x, v=metric_info.get('unit', ''): v,
            template_name=RunnableValue(value='metric_additional_intent_template'),
            question=lambda x, v=metric_info['name']: x['question'].replace(v, f'[{v}]'),
        ) | model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser() | _logger
    if branches:
        return RunnableParallel(branches)
    else:
        return {}

# ==================== 澄清中断错误 ====================
# 代码来源：text2metric_chain.py（原第2059-2061行）
def raise_clarify_interupt_error(x):
    """抛出澄清中断错误，用于需要用户确认的场景"""
    clarify_choices = extract_clarify_choices(x)
    raise ClarifyInteruptError(message=x.get('message'), clarify_choices=clarify_choices)

# ==================== 路由澄清检查 ====================
# 代码来源：text2metric_chain.py（原第2381-2387行）
@chain_decorator
def metric_router_clarify_check(x, config):
    """检查是否需要路由澄清"""
    return x.get('clarify') == 'on' and x.get('router_json', {}).get('clarify_choices')

@chain_decorator
def metric_router_clarify(x, config):
    """路由澄清Chain，用于多意图场景的用户确认"""
    return RunnablePassthrough.assign(message=lambda x: f"您的问题可能含有多个意图，请您确认要查询的问题是什么。") | raise_clarify_interupt_error

# ==================== 透传输入 ====================
# 代码来源：text2metric_chain.py（原第2388-2393行）
@chain_decorator
def passthrough_inputs(x, config):
    """透传输入参数，合并dimensions和time_recognizer到passthrough"""
    passthrough = x.pop('passthrough')
    passthrough['dimensions'] = x['metric_dimension_recognizer'].get('dimensions', [])
    passthrough['time_recognizer'] = x.get('time_recognizer', {})
    return passthrough

