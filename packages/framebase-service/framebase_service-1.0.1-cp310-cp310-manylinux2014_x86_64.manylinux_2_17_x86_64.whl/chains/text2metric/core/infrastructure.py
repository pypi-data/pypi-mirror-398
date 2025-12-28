# cython: annotation_typing = False
"""
代码来源：chains/text2metric_chain.py
原始行数：第53-75行（配置）、第77-158行（工具函数）、第167-179行（重排序）、
         第646-781行（数据处理）、第2469-2499行（异常处理）
功能说明：基础设施层 - 包含配置、工具函数、重排序、数据处理、异常处理
重构日期：2024-12-19
"""
import os
import re
import urllib
import traceback
import jieba
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from rank_bm25 import BM25Okapi

from configs import get_configs
from framebase.text2metric import SelfMetricService
from framebase.values import RunnableValue
from framebase.output_parsers import charge
from framebase.prompts import chain as prompt
from framebase.models import models
from langchain_core.runnables import (
    RunnablePassthrough,
    chain as chain_decorator,
)
from utils.logger import logger
from utils.dbs import set_thought
from utils.exceptions import (
    DBInfoError,
    MetricQueryError,
    dimensionValueError,
    NoPermissionError,
    ClarifyInteruptError,
    MetricDateQueryError,
)

# ==================== 配置部分 ====================
# 代码来源：text2metric_chain.py（原第53-57行）
metric_service_api_configs = get_configs('service').get("ekc_service")
metric_service = SelfMetricService(
    metric_service_config_token=metric_service_api_configs.get('default_token'),
    metric_service_config_url=urllib.parse.urljoin(
        metric_service_api_configs.get('ekc_host'),
        metric_service_api_configs.get('metric_url')
    ),
    metric_service_config_timeout=metric_service_api_configs.get('ekc_timeout')
)

# 代码来源：text2metric_chain.py（原第59-71行）
metric_messages = get_configs('service').get("metric_messages")
Metric_General_Error_Message = metric_messages.get("Metric_General_Error_Message")
Metric_Permission_Denied_Message = metric_messages.get("Metric_Permission_Denied_Message")
HSJ_Metric_Permission_Denied_Message = metric_messages.get("HSJ_Metric_Permission_Denied_Message")
Metric_Dimension_Permission_Denied_Message = metric_messages.get("Metric_Dimension_Permission_Denied_Message")
HSJ_Metric_Dimension_Permission_Denied_Message = metric_messages.get("HSJ_Metric_Dimension_Permission_Denied_Message")
Metric_Not_Found_Message = metric_messages.get("Metric_Not_Found_Message")
Metric_Low_Relevance_Message = metric_messages.get("Metric_Low_Relevance_Message")
Metric_No_Dimension_Message = metric_messages.get("Metric_No_Dimension_Message")
Metric_No_Dimension_Details_Message = metric_messages.get("Metric_No_Dimension_Details_Message")
Metric_Service_Error_Message = metric_messages.get("Metric_Service_Error_Message")
Metric_Null_Result_Message = metric_messages.get("Metric_Null_Result_Message")
Metric_Analysis_Error_Message = metric_messages.get("Metric_Analysis_Error_Message")

# 代码来源：text2metric_chain.py（原第74-75行）
date_mapping = {
    '月': 'MONTH', '年': 'YEAR', '日': 'DAY', '季度': 'QUARTER',
    'MONTH': 'MONTH', 'YEAR': 'YEAR', 'DAY': 'DAY', 'QUARTER': 'QUARTER'
}
date_mapping_reverse = {
    'MONTH': '月', 'YEAR': '年', 'DAY': '日', 'QUARTER': '季度',
    '月': '月', '年': '年', '日': '日', '季度': '季度'
}

# ==================== 工具函数部分 ====================
# 代码来源：text2metric_chain.py（原第77-78行）
async def hold_stream(x):
    """流式处理占位函数"""
    return x

# 代码来源：text2metric_chain.py（原第2501-2504行），曾在 entry.py 中使用
@chain_decorator
def time_info(x):
    """添加当前时间信息到输入字典"""
    x['current_time_info'] = datetime.now().strftime('%Y-%m-%d')
    return x

# 代码来源：text2metric_chain.py（原第80-85行）
def is_multi_app_id(app_id):
    """判断是否为多应用ID（允许多指标选择模式）"""
    multi_app_ids = os.environ.get('Multi_app_id', '')
    if not multi_app_ids:
        return False
    # 从环境变量中解析多应用ID列表（逗号分隔）
    app_id_list = [aid.strip() for aid in multi_app_ids.split(',') if aid.strip()]
    return str(app_id) in app_id_list

# 代码来源：text2metric_chain.py（原第87-92行）
def is_spec_pdt_app(app_id):
    """判断是否为特殊PDT应用"""
    spec_pdt_app_ids = os.environ.get('SPEC_PDT_APP', '')
    if not spec_pdt_app_ids:
        return False
    app_id_list = [aid.strip() for aid in spec_pdt_app_ids.split(',') if aid.strip()]
    return str(app_id) in app_id_list

# 代码来源：text2metric_chain.py（原第94-98行）
def is_number(char):
    """判断字符串是否为数字"""
    if re.match(r'^[-+]?[0-9]*\.?[0-9]+$', char):
        return True
    else:
        return False

# 代码来源：text2metric_chain.py（原第100-103行）
@chain_decorator
async def model_binding(x, config):
    """
    模型绑定装饰器函数，根据model_name选择对应的LLM模型
    
    从配置中获取模型名称，并使用对应的模型进行推理
    """
    llm = models[x.get('model_name', 'metric_to_text_llm')]
    return prompt | llm

# 代码来源：text2metric_chain.py（原第106-109行）
model_output_runnable = {
    'response_variables': charge,
    'model_output': model_binding
}


# 代码来源：text2metric_chain.py（原第161-165行）
def merge_list_by_order(list1, list2):
    """按顺序合并两个列表，保持公共元素的顺序"""
    common = [x for x in list1 if x in list2]
    rest_list1 = [x for x in list1 if x not in common]
    rest_list2 = [x for x in list2 if x not in common]
    return common + rest_list1 + rest_list2

# ==================== 重排序部分 ====================
# 代码来源：text2metric_chain.py（原第167-179行）
def bm25_rerank(query: str, corpus: list[str], n: int):
    """
    BM25重排序算法
    
    使用BM25算法对corpus中的元素进行重排序，返回相关性最高的n个结果
    """
    # jieba token
    tokenized_corpus = [jieba.lcut(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = jieba.lcut(query)
    # str token
    str_tokenized_corpus = [list(doc) for doc in corpus]
    str_bm25 = BM25Okapi(str_tokenized_corpus)
    str_tokenized_query = list(query)
    # merge and remove duplicate
    bm25_result = bm25.get_top_n(tokenized_query, corpus, n)
    str_bm25_result = str_bm25.get_top_n(str_tokenized_query, corpus, n)
    return merge_list_by_order(bm25_result, str_bm25_result)

# ==================== 数据处理部分 ====================
# 代码来源：text2metric_chain.py（原第646-655行）
operator_mapping = {
    "=": "EQUAL",
    "!=": "NOT_EQUAL",
    ">": "GREATER_THAN",
    ">=": "GREATER_THAN_OR_EQUAL_TO",
    "<": "LESS_THAN",
    "<=": "LESS_THAN_OR_EQUAL_TO",
    "is null": "IS_NULL",
    "is not null": "IS_NOT_NULL"
}

# 代码来源：text2metric_chain.py（原第657-676行）
def replace_operator(data):
    if isinstance(data, dict) and data:
        # Iterate through each key-value pair in the dictionary
        for key, value in data.items():
            # Check if the key is one of the operator fields and the value is in the mapping
            if key in ("operator", "comparisonsOperator") and value in operator_mapping:
                # Replace the operator with the corresponding string
                data[key] = operator_mapping[value]
            # Otherwise, recursively handle nested dictionaries and lists
            elif value:
                data[key] = replace_operator(value)
        return data
    elif isinstance(data, list):
        # Recursively handle each item in the list
        for i, item in enumerate(data):
            if isinstance(item, dict):
                data[i] = replace_operator(item)
        data = [item for item in data if item]
        return data
    return data

# 代码来源：text2metric_chain.py（原第678-692行）
magnitude_dict = {
    "HUNDRED_MILLION": 100000000,
    "MILLION": 1000000,
    "TEN_THOUSAND": 10000,
    "THOUSAND": 1000,
    "HUNDRED": 100,
    "TEN": 10,
    "ONE": 1
}

# dict for auto adapt
magnitude_mappings = {
    "HUNDRED_MILLION": '亿',
    "TEN_THOUSAND": '万',
}

# 代码来源：text2metric_chain.py（原第694-708行）
def half_round(num, decimal):
    """四舍五入处理，返回小数部分"""
    if decimal == -1:
        return num
    num_str = str(num or '').strip()
    if not num_str:
        num_str = '0'
    else:
        filtered = ''.join(ch for ch in num_str if ch.isdigit())
        num_str = filtered or '0'
    str_deci = Decimal('1').scaleb(-decimal)
    result = Decimal(f'0.{num_str}').quantize(str_deci, rounding=ROUND_HALF_UP)
    if decimal == 0:
        return ''
    decimal_part = f'{result:.{decimal}f}'.split('.')[-1]
    return decimal_part

# 代码来源：text2metric_chain.py（原第710-746行）
def data_format(formater, data_array):
    """
    数据格式化
    
    根据formater配置格式化数据数组，包括单位转换、精度处理等
    """
    if formater.get('needConversion', True):
        reals = []
        for value in data_array:
            # check if value is not None and value is not NaN
            if value is not None and value == value:
                if type(value) != str:
                    value = str(value)
                reals.append(float(value) * magnitude_dict[formater['originalMagnitude']])
            else:
                reals.append(value)
        if not reals:
            if type(data_array) == list:
                return data_array
            return data_array.tolist()
        _reals = [value for value in reals if value is not None and value == value]
        min_value = min(_reals) if _reals else None
        if formater['targetMagnitude'] == 'AUTO_ADAPT':
            if min_value is None:
                target_magnitude = "ONE"
            else:
                for magnitude, value in magnitude_dict.items():
                    if abs(min_value) >= value:
                        target_magnitude = magnitude
                        break
                else:
                    target_magnitude = "ONE"
        elif formater['targetMagnitude'] == 'NONE':
            if type(data_array) == list:
                return data_array
            return data_array.tolist()
        else:
            target_magnitude = formater['targetMagnitude']
        data_array = reals
    else:
        target_magnitude = formater['targetMagnitude']
    return list(map(lambda x: _format(x, formater, target_magnitude), data_array))

# 代码来源：text2metric_chain.py（原第748-781行）
def _format(value: str, formater, target_magnitude):
    """内部格式化函数，格式化单个数值"""
    if not value or value != value:
        return None
    value = str(value)
    if not formater.get('needConversion', True):
        if formater['unit']:
            return value + formater['unit']
        else:
            return value
    if target_magnitude in magnitude_mappings:
        value = float(value) / magnitude_dict[target_magnitude]
    else:
        value = float(value)
    value_str = format(value, 'f')
    parts = value_str.split('.')
    if len(parts) == 1:
        decimal = ''
        integer = parts[0]
    else:
        decimal = parts[1]
        integer = parts[0]
    if formater['thousandthsPlace']:
        integer = f'{int(integer):,}'
    decimal = half_round(decimal, formater['decimalPlaces'])
    if formater['unit']:
        if target_magnitude in magnitude_mappings:
            return integer + '.' + decimal + magnitude_mappings[target_magnitude] + formater['unit']
        else:
            return integer + '.' + decimal + formater['unit']
    else:
        if target_magnitude in magnitude_mappings:
            return integer + '.' + decimal + magnitude_mappings[target_magnitude]
        else:
            return integer + '.' + decimal

# ==================== 异常处理部分 ====================
# 代码来源：text2metric_chain.py（原第2469-2499行）
@chain_decorator
def handle_exception(x, config):
    """
    异常处理器
    
    统一处理各种异常类型（MetricQueryError、ClarifyInteruptError、DBInfoError、NoPermissionError等），
    设置对应的错误消息和响应类型
    """
    session_id = config['input']['session_id']
    app_id = config['input']['app_id']
    exception_str = "\n".join(traceback.format_exception(x.get('exception')))
    logger.error(f"Exception: {exception_str}")
    if isinstance(x.get('exception'), MetricQueryError):
        set_thought(session_id, 'metric_query_description_1', {'chunk': Metric_Service_Error_Message, "end": True})
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['Metric'])) | RunnablePassthrough.assign(model_output=lambda x: f"", response_variables=charge)
    elif isinstance(x.get('exception'), ClarifyInteruptError):
        set_thought(session_id, 'clarify', {'message': x.get('exception').message, 'choices': x.get('exception').clarify_choices})
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['LLM'])) | RunnablePassthrough.assign(model_output=lambda x: "", response_variables=charge)
    elif isinstance(x.get('exception'), DBInfoError):
        raise x.get('exception')
    elif isinstance(x.get('exception'), NoPermissionError):
        if x.get('exception').status_code == 'DIM403' and app_id != str(os.environ.get('HSJ_Message_app_id')):
            message = Metric_Dimension_Permission_Denied_Message
        elif x.get('exception').status_code == 'DIM403' and app_id == str(os.environ.get('HSJ_Message_app_id')):
            message = HSJ_Metric_Dimension_Permission_Denied_Message
        elif app_id == str(os.environ.get('HSJ_Message_app_id')):
            message = HSJ_Metric_Permission_Denied_Message
        else:
            message = Metric_Permission_Denied_Message
        set_thought(session_id, 'metric_query_description_1', {'chunk': f"{message}{x.get('exception').no_permission_metric}。", "end": True})
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['Metric'])) | RunnablePassthrough.assign(model_output=lambda x: f"", response_variables=charge)
    elif isinstance(x.get('exception'), dimensionValueError):
        set_thought(session_id, 'metric_query_description_1', {'chunk': f"{Metric_Not_Found_Message} {','.join(x.get('exception').invalid_dimensions)}。", "end": True})
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['Metric'])) | RunnablePassthrough.assign(model_output=lambda x: f"", response_variables=charge)
    elif isinstance(x.get('exception'), MetricDateQueryError):
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['Metric'])) | RunnablePassthrough.assign(model_output=lambda x: Metric_Service_Error_Message, response_variables=charge)
    else:
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['Metric'])) | RunnablePassthrough.assign(model_output=lambda x: Metric_General_Error_Message, response_variables=charge)

