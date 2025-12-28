# cython: annotation_typing = False
"""
指标工具函数 - Metric Utilities
代码来源：chains/text2metric_chain.py（从 service/metric.py 提取的工具函数）
功能说明：指标处理相关的通用工具函数，用于历史指标提取、树结构处理、指标信息构建等
创建日期：2024-12-19
"""
import json
from copy import deepcopy


def extract_history_metrics(history: list, multi_round_num: int) -> list:
    """
    从历史记录中提取已选择的指标
    
    参数:
        history: 历史消息列表
        multi_round_num: 多轮对话轮数
    
    返回:
        历史指标列表，每个元素包含 'name' 和 'id'
    """
    history_metric = []
    if not history:
        return history_metric
    
    # 提取最近N轮的对话历史（每轮包含用户和助手两条消息，所以是 *2）
    multi_round_num_history = history[-multi_round_num * 2:]
    for msg in multi_round_num_history:
        if not isinstance(msg, dict):
            msg = msg.dict()
        if msg.get('thoughts'):
            thoughts = [json.loads(thought) for thought in msg.get('thoughts')]
            for thought in thoughts:
                if thought.get('type') == 'intent':  # 只提取意图类型的思考记录
                    if isinstance(thought['thought'], dict) and thought['thought'].get('formdata'):
                        history_metric_groups = thought['thought'].get('formdata')
                        for metric_group in history_metric_groups:
                            for metric in metric_group:
                                if metric['selected']:
                                    history_metric.append({
                                        'name': metric['metricName'], 'id': metric['metricId']
                                    })
                    else:
                        metric_group = thought['thought']
                        for metric in metric_group:
                            if metric['selected']:
                                history_metric.append({
                                    'name': metric['metricName'], 'id': metric['metricId']
                                })
    return history_metric


def build_metric_info_from_metadata(item, index: int, intent: str = 'query') -> dict:
    """
    从metadata构建指标信息字典
    
    参数:
        item: 包含metadata的指标项
        index: 指标索引
        intent: 意图类型，默认为 'query'
    
    返回:
        指标信息字典
    """
    metric_info = {}
    metadata = item.metadata
    metric_info['name'] = metadata.get('page_content')
    metric_info['index'] = index
    metric_info['alias'] = metadata.get('alias')
    metric_info['metric_code'] = metadata.get('groupby_id')
    metric_info['metricId'] = metadata['metric_id']
    metric_info['unit'] = metadata['unit']
    metric_info['type'] = metadata['type']
    metric_info['time_interval'] = metadata['time_interval']
    metric_info['is_accumulative'] = metadata['is_accumulative']
    metric_info['is_point_metric'] = metadata.get('is_point_metric', False)
    associated_dimension = metadata.get('associated_dimension', []) or []
    valid_associated_dimension = list(filter(lambda x: x['name'] and any(x['values']), associated_dimension))
    metric_info["associated_dimension"] = valid_associated_dimension
    metric_info['definition'] = metadata['definition']
    if intent == 'definition':
        metric_info['calculation_rule'] = metadata.get('calculation_rule', '')
        metric_info['description'] = metadata.get('description', '')
        if metadata.get('metric_metadata'):
            metric_info['metadata'] = metadata['metric_metadata']
    return metric_info


def recursive_flatten_tree(data: list) -> list:
    """
    递归展平树结构，提取所有节点的名称
    
    参数:
        data: 树结构数据，每个节点包含 'name' 和 'children'
    
    返回:
        所有节点名称的扁平列表
    """
    result = []
    for m in data:
        result.append(m['name'])
        _result = recursive_flatten_tree(m['children'])
        if _result:
            result.extend(_result)
    return result


def recursive_find_tree_path(data: list, name: str) -> list:
    """
    递归查找树中指定名称节点的路径
    
    参数:
        data: 树结构数据，每个节点包含 'name' 和 'children'
        name: 要查找的节点名称
    
    返回:
        从根到目标节点的路径列表，如果未找到则返回空列表
    """
    for m in data:
        if m['name'] == name:
            return [m['name']]
        else:
            result = recursive_find_tree_path(m['children'], name)
            if result:
                return [m['name']] + result
    return []


def format_definition_chunks(metric_infos: list) -> str:
    """
    格式化指标定义为chunk字符串
    
    参数:
        metric_infos: 指标信息列表
    
    返回:
        格式化后的chunk字符串
    """
    result_str = ""
    _definitions = deepcopy(metric_infos)
    for i, item in enumerate(_definitions):
        for dimension in item['associated_dimension']:
            dimension.pop('values', ['具体维度请查看指标库'])
        result_str += f"<chunk {i+1}>{item}</chunk {i+1}>\n"
    return result_str

