# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第2501-2525行（main_chain）
功能说明：入口层 - 主chain组合逻辑和导出
重构日期：2024-12-19
迁移日期：2024-12-19（从 chains/text2metric/api/entry.py 迁移至此）
"""
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBranch,
)

from chains.text2metric.core.infrastructure import (
    handle_exception,
    time_info,
)
from chains.text2metric.service.query import check_redis_metric_cache
from chains.text2metric.service.chains import (
    metric_router_chain,
    metric_query_execute_chain,
    sub_request_dispatcher,
)
from chains.protocol import Text2MetricChainInputModel, ConversationChainInputModel
from framebase.values import RunnableValue
from framebase.output_parsers import astreaming_parser
from framebase import config_maps
from utils.dbs import fetch_redis_metric_cache, set_thought
from utils.tools import add_time_stamp_start
from utils.exceptions import (
    MetricQueryError,
    ClarifyInteruptError,
    dimensionValueError,
    NoPermissionError,
)

# ==================== 无会话Chain ====================
# 代码来源：text2metric_chain.py（原第2506-2515行）
# 无会话Chain：不检查缓存，直接执行路由和查询
headless_inputs = add_time_stamp_start | time_info | RunnablePassthrough.assign(**config_maps) | \
    RunnablePassthrough(lambda x: set_thought(x['session_id'], 'chain', 'text2metric_chain')) | \
    RunnablePassthrough.assign(disable_description=lambda x: True)  # 禁用描述生成

# 优先处理子请求，否则执行路由流程
chain_without_conversation = headless_inputs | RunnableBranch(
    (lambda x: x.get('sub_requests'), sub_request_dispatcher),
    metric_router_chain
) | astreaming_parser
chain_without_conversation = chain_without_conversation.with_types(input_type=ConversationChainInputModel)
chain_without_conversation = chain_without_conversation.with_fallbacks(
    [handle_exception],
    exceptions_to_handle=(Exception, MetricQueryError, ClarifyInteruptError),
    exception_key='exception'
)

# ==================== 主Chain ====================
# 代码来源：text2metric_chain.py（原第2518-2525行）
# 主Chain：检查缓存，如果命中则直接执行查询，否则执行路由流程
chain = fetch_redis_metric_cache | time_info | RunnableBranch(
    (lambda x: x.get('sub_requests'), sub_request_dispatcher),  # 子请求优先处理
    (lambda x: check_redis_metric_cache(x), RunnablePassthrough.assign(response_type=RunnableValue(values=['Metric'])) | metric_query_execute_chain),  # 缓存命中直接执行
    metric_router_chain  # 缓存未命中，执行完整路由流程
)
chain = chain.with_types(input_type=Text2MetricChainInputModel)
chain = chain.with_fallbacks(
    [handle_exception],
    exceptions_to_handle=(Exception, MetricQueryError, dimensionValueError, NoPermissionError),
    exception_key='exception'
)
