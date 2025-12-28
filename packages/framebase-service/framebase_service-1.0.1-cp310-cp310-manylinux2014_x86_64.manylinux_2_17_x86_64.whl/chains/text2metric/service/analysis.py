# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第783-1010行（analysis_service）、第1402-1420行（analysis_intent）、
         第1446-1615行（analysis_intent_refiner）
功能说明：分析处理 - 包含分析服务调用、分析意图识别、分析意图细化
重构日期：2024-12-19
"""
import json
import pkg_resources
from copy import deepcopy
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableGenerator,
    chain as chain_decorator,
)
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.values import RunnableValue

from chains.text2metric.core.infrastructure import (
    metric_service,
    Metric_Analysis_Error_Message,
    model_binding,
    hold_stream,
    data_format,
    replace_operator,
)
from chains.text2metric.core.analysis_utils import (
    METRIC_TYPE,
    handle_analysis_error_response,
    create_no_data_branch,
    format_invalid_dimension_info,
    format_clarify_information,
    format_dimension_dataframe,
    format_metric_link_nodes,
    filter_invalid_contribution_metrics,
    format_metric_links_string,
    merge_lineage_dataframes,
    merge_multi_source_knowledge,
    format_metric_info_string,
    ensure_single_selected_output,
    build_dimension_filters_with_defaults,
    create_simple_thought_branch,
    extract_dimension_info,
)
from chains.text2metric.core.stream_utils import (
    dimension_stream_process,
    link_stream_process,
    lineage_stream_process,
    multi_source_stream_process,
)
from chains.text2metric.service.intent import raise_clarify_interupt_error
from chains.text2metric.core.dimension_utils import (
    check_dimension_holds,
    check_dimension_filters,
)
from chains.text2metric.core.time_utils import (
    strptime,
    convert_date_format,
    is_date_after_today,
    subtract_minimum_unit,
)
from chains.analytic_metric_chain import time_convert
from app.admin_operation import get_global_config_info
from utils.dbs import set_thought, get_redis_data
from utils.logger import logger
from utils.exceptions import APICallError, APICallTimeOutError, MetricQueryError

# ==================== 分析服务调用 ====================
# 代码来源：text2metric_chain.py（原第783-1010行）
@chain_decorator
async def call_metric_analysis_service(x, config):
    """
    指标分析服务Chain
    
    执行不同类型的分析（维度分析、关联分析、血缘分析、下钻分析），生成分析结果描述
    """

    branches = {'passthrough': RunnablePassthrough()}
    if x['metric_query']:
        for gi, metric_group in enumerate(x['metric_query']):
            gi = gi + 1
            for metric_query in metric_group:
                gi = gi if not metric_query.get('request_index') else gi
                _type = metric_query['type']
                metric_query = replace_operator(metric_query)
                invalid_dimension_info = ''
                if metric_query.get('invalid_dimensions'):
                    set_thought(x['session_id'], f'invalid_dimensions_{gi}', metric_query['invalid_dimensions'])
                    invalid_dimension_info = format_invalid_dimension_info(metric_query['invalid_dimensions'])
                if x.get('clarify') == 'on' and metric_query.get('invalid_dimensions'):
                    clarify_information = format_clarify_information(
                        metric_query['invalid_dimensions'],
                        x.get('metric_dimension_info', '')
                    )
                    return RunnablePassthrough.assign(template_name=RunnableValue(value='clarify_template'),
                                                        information=lambda x, v=clarify_information: v) | model_binding | hold_stream | JsonOutputParser() | raise_clarify_interupt_error
                
                if _type in ['metric-link-analysis'] and str(metric_query['metricType']) != '2':
                    set_thought(x['session_id'], f'metric-link-analysis_{gi}', {'chunk': Metric_Analysis_Error_Message, 'end': True})
                    logger.warning(f'skip metric-link-analysis because metric type is not 2:{metric_query}')
                    continue
                try:
                    result = metric_service.metric_analysis(metric_query, config.get('headers', {}).get('cookie'))
                except (APICallError, APICallTimeOutError):
                    raise MetricQueryError(f"Metric analysis query failed: {metric_query}")

                if _type == 'dimension':
                    error_branch = handle_analysis_error_response(
                        result, _type, dimension_stream_process, gi, x['session_id'], str(x['app_id']), metric_query
                    )
                    if error_branch is not None:
                        branches[_type] = error_branch
                        continue
                    if not metric_query['dimensionHolds']:
                        # no dimensions
                        logger.warning(f'dimension query but no dimensions: {metric_query}')
                        branches[_type] = create_simple_thought_branch(result, _type, gi, x['session_id'])
                    else:
                        metric_dimension_result = result['data']['dimensionAnalysis']
                        if not metric_dimension_result['data']:
                            # dimension but no data
                            logger.warning(f'dimension query but no data: {metric_query}\n\t\t\t{result}')
                            branches[_type] = create_no_data_branch(
                                result, _type, dimension_stream_process, gi, x['session_id']
                            )
                        else:
                            # format data
                            df = format_dimension_dataframe(
                                metric_dimension_result['data'],
                                metric_dimension_result['headers'],
                                metric_dimension_result['fieldFormatConfigList']
                            )
                            source_value, target_value = data_format(result['data']['valueFormatConfig'], [result['data']['sourceValue'], result['data']['targetValue']])
                            if x.get('disable_description'):
                                branches[_type] = RunnablePassthrough.assign(metric_analysis_info=lambda x, v=df.to_dict('records'): v,
                                                set_thought=lambda x, v=result, w=_type: set_thought(x['session_id'], f'{w}_{gi}', v))
                            else:
                                branches[_type] = RunnablePassthrough.assign(metric_analysis_info=lambda x, v=df.to_dict('records'): v,
                                                set_thought=lambda x, v=result, w=_type: set_thought(x['session_id'], f'{w}_{gi}', v)) | \
                                    RunnablePassthrough.assign(template_name=RunnableValue(value='metric_dimension_describe_template'),
                                                invalid_dimension_info=lambda x, v=invalid_dimension_info: v,
                                                metric_name=RunnableValue(value=metric_query['metricName']),
                                                source_date=RunnableValue(value=metric_query['sourceDate']),
                                                target_date=RunnableValue(value=metric_query['targetDate']),
                                                source_value=RunnableValue(value=source_value),
                                                target_value=RunnableValue(value=target_value),
                                                model_name=RunnableValue(value='metric_to_text_llm')) | \
                                    RunnablePassthrough.assign(placeholder=model_binding | RunnableGenerator(dimension_stream_process).with_config(config={'metadata': {'index': gi}}))
                
                    # multi source analysis
                    source_value, target_value = data_format(result['data']['valueFormatConfig'], [result['data']['sourceValue'], result['data']['targetValue']])
                    multi_source_knowledge = merge_multi_source_knowledge(x.get('recall_nodes', []))
                    if multi_source_knowledge:
                        if not x.get('disable_description'):
                            branches['multiple-sources-analysis'] = \
                                    RunnablePassthrough.assign(template_name=RunnableValue(value='metric_multi_source_describe_template'),
                                                multi_source_knowledge=RunnableValue(value=multi_source_knowledge),
                                                metric_name=RunnableValue(value=metric_query['metricName']),
                                                source_date=RunnableValue(value=metric_query['sourceDate']),
                                                target_date=RunnableValue(value=metric_query['targetDate']),
                                                source_value=RunnableValue(value=source_value),
                                                target_value=RunnableValue(value=target_value),
                                                model_name=RunnableValue(value='metric_to_text_llm')) | \
                                    RunnablePassthrough.assign(placeholder=model_binding | RunnableGenerator(multi_source_stream_process).with_config(config={'metadata': {'index': gi}}))
                
                elif _type == 'metric-link-analysis':
                    error_branch = handle_analysis_error_response(
                        result, _type, link_stream_process, gi, x['session_id'], str(x['app_id']), metric_query
                    )
                    if error_branch is not None:
                        branches[_type] = error_branch
                        continue
                    if not result['data']['nodes'] or not result['data']['links']:
                        branches[_type] = create_no_data_branch(
                            result, _type, link_stream_process, gi, x['session_id']
                        )
                        continue
                    metric_id_dict = format_metric_link_nodes(result['data']['nodes'])
                    metric_name = metric_id_dict[metric_query['metricId']]['metricName']
                    metric_links = format_metric_links_string(result['data']['links'], metric_id_dict)
                    metric_id_dict = filter_invalid_contribution_metrics(metric_id_dict)
                    branches[_type] = RunnablePassthrough.assign(metric_analysis_info=lambda x, v=list(metric_id_dict.values()): v,
                                            metric_relation=RunnableValue(value=metric_links),
                                            metric_name=RunnableValue(value=metric_name),
                                            set_thought=lambda x, v=result, w=_type: set_thought(x['session_id'], f'{w}_{gi}', v)) | \
                                RunnablePassthrough.assign(template_name=RunnableValue(value='metric_link_describe_template'),
                                            invalid_dimension_info=lambda x, v=invalid_dimension_info: v,
                                            model_name=RunnableValue(value='metric_to_text_llm')) | \
                                RunnablePassthrough.assign(placeholder=model_binding | RunnableGenerator(link_stream_process).with_config(config={'metadata': {'index': gi}}))
                elif _type == 'lineage-analysis':
                    error_branch = handle_analysis_error_response(
                        result, _type, lineage_stream_process, gi, x['session_id'], str(x['app_id']), metric_query
                    )
                    if error_branch is not None:
                        branches[_type] = error_branch
                        continue
                    if not result['data'] or not any(result['data']):
                        branches[_type] = create_no_data_branch(
                            result, _type, lineage_stream_process, gi, x['session_id']
                        )
                        continue

                    # metric link detail analysis
                    new_data, lack_data, diff_data = merge_lineage_dataframes(result['data'])
                    branches[_type] = RunnablePassthrough.assign(
                                        set_thought=lambda x, v=result, w=_type: set_thought(x['session_id'], f'{w}_{gi}', v)) | \
                            RunnablePassthrough.assign(template_name=RunnableValue(value='metric_lineage_describe_template'),
                                                        invalid_dimension_info=lambda x, v=invalid_dimension_info: v,
                                                        metric_name=RunnableValue(value=metric_query['metricName']),
                                                        source_date=RunnableValue(value=metric_query['sourceDate']),
                                                        target_date=RunnableValue(value=metric_query['targetDate']),
                                                        new_data=RunnableValue(value=str(new_data.to_dict('records'))),
                                                        lack_data=RunnableValue(value=str(lack_data.to_dict('records'))),
                                                        diff_data=RunnableValue(value=str(diff_data.to_dict('records'))),
                                                        model_name=RunnableValue(value='metric_to_text_llm')) | \
                            RunnablePassthrough.assign(placeholder=model_binding | RunnableGenerator(lineage_stream_process).with_config(config={'metadata': {'index': gi}}))

                elif _type == 'dimension-drill-down':
                    branches[_type] = create_simple_thought_branch(result, _type, gi, x['session_id'])
    else:
        result = {}
    
    return RunnablePassthrough.assign(**branches)

# ==================== 分析意图识别 ====================
# 代码来源：text2metric_chain.py（原第1402-1420行）
@chain_decorator
async def metric_analysis_additional_intent(x, config):
    """
    分析额外意图识别Chain
    
    为每个指标识别分析相关的额外意图（如需要哪些维度、分析类型等）
    """
    with open(pkg_resources.resource_filename('configs', 'chain/metric_analysis_intent.json'), 'r', encoding='utf-8') as f:
        json_schema = json.load(f)
    branches = {}
    
    for i, metric_info in enumerate(x['metric_infos']):
        _json_schema = deepcopy(json_schema)
        metric_info_str = format_metric_info_string(metric_info)

        branches[metric_info['metricId']] = \
            RunnablePassthrough.assign(
                metric_info=lambda x, v=metric_info_str: v,
                json_schema=lambda x, v=_json_schema: v,
                template_name=RunnableValue(value='metric_analysis_intent_template'),
                question=lambda x, v=metric_info['name']: x['question'].replace(v, f'[{v}]'),
            ) | \
            model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser()
    
    return branches

# ==================== 分析意图细化 ====================
# 代码来源：text2metric_chain.py（原第1446-1615行）
@chain_decorator
def refine_metric_analysis_intents(x, config):
    """
    细化分析意图，构建最终查询
    
    根据意图类型（root cause analysis/dimension_analysis/link_analysis/lineage_analysis）
    构建对应的分析查询列表
    """
    passthrough = x['passthrough']
    outputs = [None] * len(x['dimension_intent'])
    intent_data = [None] * len(x['dimension_intent'])
    metric_base_dimension_order = {}
    for metric_base_id in passthrough.get('metric_base_ids'):
        dimension_order = get_redis_data('dimension_analysis_dimension_order', metric_base_id)
        metric_base_dimension_order[str(metric_base_id)] = dimension_order

    for i, metric_id in enumerate(x['dimension_intent']):
        raw_metric = list(filter(lambda x: x.metadata['metric_id'] == metric_id, passthrough.get('raw_metric_info')))
        if raw_metric:
            raw_metric = raw_metric[0]
            metric_base_id = raw_metric.metadata['kb_id'].strip('metric_').strip('_definition')
            dimension_order = metric_base_dimension_order.get(metric_base_id)
        else:
            dimension_order = None

        metric_info = passthrough.get('metric_infos')[i]
        latest_date = strptime(x['time_records'][metric_id][-1], metric_info['time_interval'])
        startDate = x['time_recognizer'].get('startDate') or convert_date_format(x['time_records'][metric_id][-1], metric_info['time_interval'])
        endDate = x['time_recognizer'].get('endDate') or convert_date_format(x['time_records'][metric_id][-1], metric_info['time_interval'])
        _startDate, _endDate = time_convert(startDate, endDate, latest_date)
        if x['time_recognizer'].get('time_unit') != metric_info['time_interval']:
            if _startDate != _endDate:
                _startDate = _endDate
        if not _startDate:
            _startDate = x['time_records'][metric_id][-1]
        if not _endDate:
            _endDate = x['time_records'][metric_id][-1]
        
        dimension_holds = x['dimension_intent'][metric_id].get('dimensionHolds', [])
        if not dimension_holds:
            if get_global_config_info('metric_dimension_analysis_mode') == 'one by one':
                if metric_info.get('associated_dimension'):
                    if not dimension_holds:
                        dimension_holds = [metric_info['associated_dimension'][0]['name']]
                    if not dimension_order:
                        dimension_order = metric_service.fetch_dimensions(config.get('headers', {}).get('cookie'))
                    for d in dimension_order:
                        if d in [m['name'] for m in metric_info['associated_dimension']]:
                            dimension_holds = [d]
                            break
                        else:
                            dimension_holds = [dimension_holds[0]]
            else:
                if not dimension_holds:
                    dimension_holds = [m['name'] for m in metric_info['associated_dimension']]
        if _startDate > _endDate:
            date2 = convert_date_format(_startDate, metric_info['time_interval'], True)
            date1 = convert_date_format(_endDate, metric_info['time_interval'])
        else:
            date1 = convert_date_format(_startDate, metric_info['time_interval'])
            date2 = convert_date_format(_endDate, metric_info['time_interval'], True)
        branch = {
            'sourceDate': date2,
            'targetDate': date1,
            'metricId': metric_id,
            'metricName': metric_info['name'],
            'selected': metric_info['selected'],
            'time_interval': metric_info['time_interval'],
            'dimensionHolds': dimension_holds,
            'dimensionFilters': x['dimension_intent'][metric_id].get('dimensionFilters', {}),
            'invalid_dimensions': [x['dimension_intent'][metric_id].get('invalid_dimensions', [])],
            'metricType': METRIC_TYPE[metric_info['type']],
        }
        
        dimension_names, dimension_kvs, dimension_defaults, mandatory_dimension = extract_dimension_info(
            metric_info['associated_dimension']
        )
        branch = check_dimension_holds(branch, dimension_names, mandatory_dimension)
        branch = check_dimension_filters(branch, dimension_kvs, dimension_defaults)
        if branch['sourceDate'] == branch['targetDate'] or is_date_after_today(branch['targetDate']):
            if is_date_after_today(branch['sourceDate']):
                branch['sourceDate'] = x['time_records'][metric_id][-1]
            branch['targetDate'] = subtract_minimum_unit(branch['sourceDate'])

        outputs[i] = branch
        outputs[i]['metricId'] = metric_info['metricId']
        outputs[i]['metricType'] = METRIC_TYPE[metric_info['type']]
        outputs[i]['metricName'] = metric_info['name']
        outputs[i]['selected'] = metric_info['selected']
        
        intent_data[i] = deepcopy(branch)
        intent_data[i]['availableDimensions'] = metric_info['associated_dimension']

    outputs = ensure_single_selected_output(outputs)
    
    metric_query = []
    for i, output in enumerate(outputs):
        if output['selected']:
            _metric_query = []
            
            if passthrough['intent'] in ['root cause analysis', 'dimension_analysis']:
                query = {
                    "metricId": output['metricId'],
                    "metricName": output['metricName'],
                    "sourceDate": output['sourceDate'],
                    "targetDate": output['targetDate'],
                    "dimensionHolds": output.get('dimensionHolds', []),
                    "dimensionFilters": output.get('dimensionFilters', {}),
                    "metricType": output['metricType'],
                    "sortBy": output.get('sortBy'),
                    "type": "dimension"
                }
                if not query.get('sortBy'):
                    del query['sortBy']
                _metric_query.append(query)
            if passthrough['intent'] in ['root cause analysis', 'link_analysis']:
                dimension_filters = output.get('dimensionFilters', {})
                if i < len(intent_data) and intent_data[i]:
                    available_dimensions = intent_data[i].get('availableDimensions', [])
                    dimension_filters = build_dimension_filters_with_defaults(dimension_filters, available_dimensions)
                    if dimension_filters != output.get('dimensionFilters', {}):
                        intent_data[i]['dimensionFilters'] = dimension_filters
                
                _metric_query.append({
                    "metricId": output['metricId'],
                    "sourceDate": output['sourceDate'],
                    "targetDate": output['targetDate'],
                    "dimensionFilters": dimension_filters,
                    "metricType": output['metricType'],
                    "type": "metric-link-analysis"
                })
            if passthrough['intent'] in ['root cause analysis', 'lineage_analysis']:
                _metric_query.append({
                    "metricId": output['metricId'],
                    "metricName": output['metricName'],
                    "sourceDate": output['sourceDate'],
                    "targetDate": output['targetDate'],
                    "metricType": output['metricType'],
                    "type": "lineage-analysis"
                })
            metric_query.append(_metric_query)
    set_thought(passthrough['session_id'], 'intent', intent_data)
    logger.info(f"metric_query:{json.dumps(metric_query, ensure_ascii=False, indent=4)}")
    passthrough['metric_query'] = metric_query
    return passthrough

