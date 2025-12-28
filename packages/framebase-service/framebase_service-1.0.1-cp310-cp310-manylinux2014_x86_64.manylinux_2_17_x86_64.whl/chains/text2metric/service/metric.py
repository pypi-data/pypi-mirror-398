# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第434-463行（metric_pick_postprocess）、第489-533行（metric_pick）、
         第536-556行（metric_definition）、第559-644行（metric_retrieve）、
         第1956-1971行（metric_scroll）、第1973-1994行（metric_tree_pick）、
         第1996-2028行（metric_scroll_merge）、第2030-2057行（metric_scroll_answer）
功能说明：指标处理 - 包含指标检索、指标选择、指标定义、指标滚动
重构日期：2024-12-19
"""
from copy import deepcopy
from collections import defaultdict

from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBranch,
    RunnableGenerator,
    chain as chain_decorator,
)
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema.messages import BaseMessage
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.values import RunnableValue

from chains.text2metric.core.infrastructure import (
    metric_service,
    model_binding,
    model_output_runnable,
    bm25_rerank,
    is_multi_app_id,
    hold_stream,
)
from chains.text2metric.core.intent_utils import (
    load_chain_json_schema,
    should_remove_clarify_choices,
    remove_clarify_choices_from_schema,
)
from chains.text2metric.core.metric_utils import (
    extract_history_metrics,
    build_metric_info_from_metadata,
    recursive_flatten_tree,
    recursive_find_tree_path,
    format_definition_chunks,
)
from chains.text2metric.core.stream_utils import stream_process
from chains.text2metric.service.intent import raise_clarify_interupt_error
from utils.dbs import scroll_arcvector, set_thought
from utils.logger import logger
from utils.exceptions import DBInfoError

# ==================== 指标选择后处理 ====================
# 代码来源：text2metric_chain.py（原第434-463行）
def metric_pick_postprocess(x):
    """
    指标选择后处理，标记选中状态
    
    根据mentioned_metric和related_metric，设置metric_infos中每个指标的selected状态
    """
    result = []
    mentioned = False
    # 移除related_metric中已在mentioned_metric中的指标，避免重复
    x['metric_pick']['related_metric'] = [m for m in x['metric_pick']['related_metric'] if m not in x['metric_pick']['mentioned_metric']]
    for i in x['metric_pick']['mentioned_metric']:
        if i > len(x['metric_infos']):
            continue
        if not mentioned:
            x['metric_infos'][int(i)]['selected'] = True  # 第一个mentioned指标默认选中
            mentioned = True
        elif x.get('metric_pick_mode') == 'multiple' or (x.get('app_id') and is_multi_app_id(x.get('app_id'))):
            x['metric_infos'][int(i)]['selected'] = True  # 多指标模式下全部选中
        else:
            x['metric_infos'][int(i)]['selected'] = False  # 单指标模式，只选中第一个
    for _, i in enumerate(x['metric_pick']['related_metric']):
        if i > len(x['metric_infos']):
            continue
        if not mentioned and _ == 0:
            x['metric_infos'][int(i)]['selected'] = True
        else:
            x['metric_infos'][int(i)]['selected'] = False
    for i in x['metric_pick']['mentioned_metric'] + x['metric_pick']['related_metric']:
        if i > len(x['metric_infos']):
            continue
        if x['metric_infos'][int(i)]['selected']:
            result.append(x['metric_infos'][int(i)])
    if not result and x['intent'] != 'definition':
        logger.error('router return no metric')
        raise DBInfoError('text2metric but no metric')
    return result

# ==================== 指标检索结果处理 ====================
# 代码来源：text2metric_chain.py（原第559-644行）
def process_metric_retrieve_result(x):
    """
    处理指标检索结果
    
    合并历史指标，去重，构建metric_infos列表
    """
    history_metric = []
    if x.get('history'):
        multi_round_num = int(x.get('multi_round_num'))
        history_metric = extract_history_metrics(x.get('history'), multi_round_num)

    addional_metrics = []
    if history_metric:
        history_metric_ids = [metric['id'] for metric in history_metric]
        if x.get('intent') == 'definition':
            for metric_base_id in x.get('metric_base_ids'):
                metrics = scroll_arcvector(f'metric_{metric_base_id}_definition', {"must": [{"key": "metadata.metric_id", "match": {"any": history_metric_ids}}]})
                addional_metrics.extend(metrics)
        else:
            for metric_base_id in x.get('metric_base_ids'):
                metrics = scroll_arcvector(f'metric_{metric_base_id}', {"must": [{"key": "metadata.metric_id", "match": {"any": history_metric_ids}}]})
                addional_metrics.extend(metrics)

    _raw_metric_info = x.get('raw_metric_info')
    if _raw_metric_info:
        _raw_metric_info = addional_metrics + _raw_metric_info
    else:
        _raw_metric_info = addional_metrics
    
    raw_metric_ids = set()
    raw_metric_info = []
    for metric in _raw_metric_info:
        if 'score' not in metric.metadata:
            metric.metadata['score'] = 1
        if metric.metadata['metric_id'] not in raw_metric_ids:
            raw_metric_ids.add(metric.metadata['metric_id'])
            raw_metric_info.append(metric)

    metric_infos = []
    if not raw_metric_info or not len(raw_metric_info):
        raise DBInfoError('text2metric but no metric')
    x['raw_metric_info'] = raw_metric_info
    logger.info('retrieved metric:')
    for i, item in enumerate(raw_metric_info):
        logger.info(f'{item.metadata["score"]:.2f} {item.metadata.get("page_content")}')
        metric_info = build_metric_info_from_metadata(item, i, x.get('intent', 'query'))
        metric_infos.append(metric_info)
    x['metric_infos'] = metric_infos
    return x

# ==================== 指标选择 ====================
# 代码来源：text2metric_chain.py（原第489-533行）
@chain_decorator
async def metric_pick(x):
    """
    指标选择Chain
    
    使用LLM从metric_infos中选择相关的指标（mentioned_metric和related_metric）
    """
    _schema = load_chain_json_schema('metric_pick.json')
    if should_remove_clarify_choices(x):
        remove_clarify_choices_from_schema(_schema)
    if x.get('metric_infos'):
        _metric_infos = deepcopy(x.get('metric_infos', []))
        for metric in _metric_infos:
            if type(metric) == dict:
                dimension_retrivals = []
                for dimension in metric['associated_dimension']:
                    dimension_retrivals.append({dimension['name']: bm25_rerank(x['question'], dimension['values'], 5)})
                metric['associated_dimension'] = dimension_retrivals
                metric.pop('definition', None)
        if x['intent'] == 'scroll':
            _schema['properties'].pop('mentioned_metric')
            _schema['properties'].pop('related_metric')
            _schema['properties']['mentioned_metric'] = {
                "type": "array",
                "items": {
                    "type": "integer",
                    "description": "指标序号。"
                },
                "description": "能直接回答用户问题的指标序号，可以是用户提到的指标，也可以是最相关的指标，用户没有明确提到指标时，请选择所有相关的指标。如果用户需要所有的指标，你可以在mentioned_metric中写入*，*表示所有指标。注意，所有序号都必须真实有效，不要给出不存在的序号。"
            }
        return RunnablePassthrough.assign(metric_pick=
                    RunnablePassthrough.assign(template_name=RunnableValue(value='metric_pick_template'),
                                          model_name=RunnableValue(value='metric_to_text_llm'),
                                          metric_info=lambda x: _metric_infos,
                                          json_schema=lambda x, v=_schema: v) |
                    model_binding | ekcStrOutputParser() | JsonOutputParser() | RunnableGenerator(stream_process)
        ) | RunnableBranch(
            (lambda x: x.get('clarify') == 'on' and x.get('metric_pick', {}).get('clarify_choices'), RunnablePassthrough.assign(message=lambda x: f"抱歉，没有检索到您要查找的指标，请问你要检索的是以下指标吗？") | raise_clarify_interupt_error),
            (lambda x: x['intent'] == 'scroll', RunnablePassthrough()),
            RunnablePassthrough.assign(metric_infos=metric_pick_postprocess)
        )
    else:
        return x

# ==================== 指标定义 ====================
# 代码来源：text2metric_chain.py（原第536-556行）
def metric_definition(x):
    """
    指标定义Chain
    
    生成指标定义的说明文本
    """
    if x.get('metric_infos'):
        return RunnablePassthrough.assign(template_name=RunnableValue(value='metric_definition_template'),
                                          model_name=RunnableValue(value='output_llm'),
                                          definitions=process_defination,
                                          response_type=lambda x, v=['Metric', 'DOC']: v,
                                          recall_nodes=lambda x: [x['raw_metric_info'][int(i)] for i in x['metric_pick']['mentioned_metric'] + x['metric_pick']['related_metric'] if i < len(x['raw_metric_info'])]
                                        ) | \
                    model_output_runnable
    else:
        return x

def process_defination(x):
    return format_definition_chunks(x.get('metric_infos', []))

# ==================== 指标滚动 ====================
# 代码来源：text2metric_chain.py（原第1956-1971行）
@chain_decorator
def scroll_metric_base(x, config):
    """
    滚动指标基础数据
    
    从向量数据库获取所有指标，过滤出用户有权限访问的指标
    """
    metrics = []
    for metric_base_id in x['metric_base_ids']:
        metrics.extend(scroll_arcvector(f"metric_{metric_base_id}", {}))
    metric_infos = [metric.metadata['page_content'] for metric in metrics]
    avaliable_metrics = metric_service.fetch_metrics(config.get('headers', {}).get('cookie'))
    x['metric_infos'] = []
    x['recall_nodes'] = []
    for m in metric_infos:
        if m in avaliable_metrics:
            x['metric_infos'].append(m)
            x['recall_nodes'].append(list(filter(lambda x: x.metadata['page_content'] == m, metrics))[0])
            x['recall_nodes'][-1].metadata['directory'] = avaliable_metrics[m]['directory']

    return x

# 代码来源：text2metric_chain.py（原第1973-1994行）
@chain_decorator
async def metric_tree_pick(x, config):
    """
    指标树选择Chain
    
    使用LLM从指标树中选择相关的目录路径
    """
    _logger = RunnablePassthrough(lambda x: logger.info(f"metric_tree_pick: {x}"))
    tree = metric_service.fetch_metric_tree(config.get('headers', {}).get('cookie'))
    json_schema = load_chain_json_schema('metric_tree_pick.json')
    chain = RunnablePassthrough.assign(
        json_schema=lambda x, v=json_schema: v,
        tree=lambda x, v=recursive_flatten_tree(tree): v,
        question=lambda x, v=x['question']: v,
        template_name=RunnableValue(value='metric_tree_pick_template'),
    ) | model_binding | ekcStrOutputParser() | hold_stream | JsonOutputParser()
    return chain | _logger | RunnablePassthrough.assign(tree=lambda x, v=tree: v)

# 代码来源：text2metric_chain.py（原第1996-2028行）
async def metric_scroll_merge(x):
    """
    合并指标滚动结果
    
    根据metric_tree_pick的结果，将指标按目录分组组织
    """
    result = x['metric_pick_result']
    tree_pick_result = x['metric_tree_pick_result']
    metric_in_directory = []
    if result.get('metric_pick', {}).get('mentioned_metric') and "*" not in result['metric_pick']['mentioned_metric']:
        result['metric_infos'] = [result['metric_infos'][int(i)] for i in result['metric_pick']['mentioned_metric'] if int(i) < len(result['metric_infos'])]
    
    for directory in tree_pick_result['related_directory']:
        path = recursive_find_tree_path(tree_pick_result['tree'], directory)
        _metric_in_directory = defaultdict(list)
        for i in range(len(result['recall_nodes'])):
            if result['recall_nodes'][i].metadata.get('directory') and result['recall_nodes'][i].metadata.get('directory') in path:
                _path = "/".join(path[:path.index(result['recall_nodes'][i].metadata.get('directory')) + 1])
                _metric_in_directory[_path].append(result['recall_nodes'][i].metadata['page_content'])
                if result['recall_nodes'][i].metadata['page_content'] in result['metric_infos']:
                    result['metric_infos'].remove(result['recall_nodes'][i].metadata['page_content'])
        if _metric_in_directory:
            _metric_in_directory = dict(_metric_in_directory)
            metric_in_directory.append(_metric_in_directory)
    result['recall_nodes'] = [m for m in result['recall_nodes'] if m.metadata['page_content'] in result['metric_infos'] + [x for y in metric_in_directory for x in y.values()]]
                
    result['metric_in_directory'] = metric_in_directory
    return result

# 代码来源：text2metric_chain.py（原第2030-2043行）
async def metric_scroll_description_process(chunks, config):
    """指标滚动描述流式处理，保存滚动描述"""
    session_id = config['input']['session_id']
    content = ''
    async for chunk in chunks:
        if isinstance(chunk, BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk) == str:
                content += chunk
            
        set_thought(session_id, f"metric_scroll_description", {'chunk': content})
        yield chunk
    set_thought(session_id, f"metric_scroll_description", {'chunk': content, 'end': True})

# 代码来源：text2metric_chain.py（原第2045-2057行）
@chain_decorator
def metric_scroll_answer(x):
    """
    生成指标滚动答案Chain
    
    根据选择的指标和目录结构生成滚动答案
    """
    if not x.get('metric_pick'):
        return {"model_output": lambda x: "抱歉，您无法查看任何指标", 'response_variables': model_output_runnable['response_variables']}
    if any(i == '*' for i in x['metric_pick']['mentioned_metric']):
        x['metric_pick']['mentioned_metric'] = list(range(len(x['metric_infos'])))
    chain = RunnablePassthrough.assign(metric_infos=lambda x: x['metric_infos'],
                                    metric_in_directory=lambda x: x['metric_in_directory'],
                                    recall_nodes=lambda x: x['recall_nodes'],
                                    template_name=RunnableValue(value='metric_scroll_template'),
                                    model_name=RunnableValue(value='output_llm')) | \
        RunnablePassthrough.assign(placeholder=model_binding | RunnableGenerator(metric_scroll_description_process))
    return chain | {"model_output": lambda x: "", 'response_variables': model_output_runnable['response_variables']}

