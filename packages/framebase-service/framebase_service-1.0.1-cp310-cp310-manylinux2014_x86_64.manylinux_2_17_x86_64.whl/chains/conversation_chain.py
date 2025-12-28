# cython: annotation_typing = False
from datetime import datetime

from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBinding, RunnableBranch,
    chain as chain_decorator,
    RunnableSequence,
    RunnableGenerator,
    RunnableParallel,
    RunnableLambda,
    RunnablePick
)
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
import json, pkg_resources, uuid, copy, traceback, time, re, asyncio
import re
from collections import defaultdict

from framebase.models import models, update_llm_runnables, get_input_len
from framebase import config_maps, update_enum_names
from framebase.prompts import chain as prompt, mappings as prompt_mappings
from framebase.values import RunnableValue
from framebase.output_parsers import astreaming_parser, charge, make_sources_documents
from framebase.retrievers import mappings as VS_POINT_DATA_TYPE
from framebase.notices import RunnableNotice
from framebase.synonyms import chain as synonym_word_detect_chain,synonym_history_detect_chain
from framebase.protocol import SourceDocumentModel
from framebase.embeddings import find_max_similarity_item
from framebase.parameters_extractor import chain as parameters_extractor
from utils.dbs import redis_hget, get_redis_data, set_thought
from utils import exceptions
from utils.logger import logger
from utils.tools import add_time_stamp_start
from utils.langfuse_tools import langfuse_handler, get_langfuse_handler, get_langfuse_trace

from .retriever_chain import multi_kbs_retrieve_chain, remote_retrieve_chain, multi_src_retrieve_chain
from .protocol import ConversationChainInputModel, ConversationChainOutputModel, ConversationHistory
from .table2chart_chain import chain as table2chart_chain, table2chart_interface, table2chart_interface_for_cypher
from .text2metric_chain import chain as text2metric_chain
from .text2metric.core.infrastructure import metric_service_api_configs
from .metric_template_analysis_chain import metric_template_analysis_chain
from openai._exceptions import OpenAIError, RateLimitError, InternalServerError, APIConnectionError, APITimeoutError
from utils.exceptions import LLMCallError, LLMCallTimeoutError, LLMRateLimitError, format_error_response

with open(pkg_resources.resource_filename('configs', 'service/conversation_layout.json'), 'r', encoding='utf-8') as f:
    layout_schema = json.load(f)



def format_history(history, multi_round_num):
    chat_history_list = []
    if multi_round_num:
        multi_round_num=int(multi_round_num)
    else:
        multi_round_num=0
    if multi_round_num == 0:
        history = []
    multi_round_num_history = history[-multi_round_num * 2:] 

    for msg in multi_round_num_history:
        if type(msg) == dict:
            msg = ConversationHistory(**msg)
        if msg.role == "human" or msg.role == "user":
            chat_history_list.append(f"用户：{msg.content}")
        elif msg.role == "ai" or msg.role == "assistant":
            cleaned_content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL)
            if msg.thoughts:
                metric_name_mapping={}
                thoughts=[json.loads(thought) for thought in msg.thoughts]
                thought_str=''
                for thought in thoughts:
                    if 'type' not in thought:
                        continue
                    if thought['type']=='insight':
                        pass
                        #if type(thought['thought'])==dict:
                        #    thought_str+=thought['thought']['chunk']
                        #else:
                        #    thought_str+=thought['thought']
                    if thought['type']=='clarify':
                        thought_str+=str(thought['thought'])
                    if thought['type'].startswith('metric_data_'):
                        thought_str+=f"{str(thought['thought'][:int(metric_service_api_configs.get('metric_query_reject_answer_row_number'))])}"
                    if thought['type'].startswith('metric_query_description_'):
                        if type(thought['thought'])==dict:
                            thought_str+=thought['thought']['chunk']
                        else:
                            thought_str+=thought['thought']
                    if thought['type']=='intent':
                        if type(thought['thought'])==dict:
                            for group in thought['thought'].get('formdata',[]):
                                for metric in group:
                                    metric_name_mapping[metric['metricId']]=metric['metricName']
                        else:
                            for metric in thought['thought']:
                                metric_name_mapping[metric['metricId']]=metric['metricName']

                    if thought['event']=='sub_request' and thought['type']=='text2metric_chain':
                        if thought['thought'].get('text2metric_chain'):
                            sub_request=thought['thought']['text2metric_chain']
                            if sub_request.get('startDate'):
                                thought_str+=f"\n在上一次查询中，查询到指标{[metric_name_mapping.get(m) for m in sub_request['metricIdList']]}，起始时间{sub_request['startDate']}，结束时间{sub_request['endDate']}，查询中对维度{sub_request['dimensionHolds']}做了下钻，对维度{sub_request['dimensionFilters']}做了过滤。\n"
                            else:
                                thought_str+=f"\n在上一次查询中，查询到指标{[metric_name_mapping.get(m) for m in sub_request['metricIdList']]}，起始时间{sub_request['sourceDate']}，结束时间{sub_request['targetDate']}，查询中对维度{sub_request['dimensionHolds']}做了下钻，对维度{sub_request['dimensionFilters']}做了过滤。\n"
                cleaned_content=thought_str+f"{cleaned_content}"
            chat_history_list.append(f"助手：{cleaned_content}")
        elif msg.role == "file":
            chat_history_list.append(f"用户：我上传了一个文件《{msg.content}》。")
            chat_history_list.append(f"助手：好的。")
    chat_history = "\n".join(chat_history_list)
    return chat_history

# def extract_object_name(url: str, minio_bucket_name: str) -> str:
#     """
#     从完整的 MinIO URL 中提取 object_name。
#     例如：
#     http://host:port/bucket_name/path/to/file.png
#     提取为 path/to/file.png
#     """
#     parsed = urlparse(url)
#     path_parts = parsed.path.lstrip("/").split("/", 1)
#     if len(path_parts) != 2:
#         # 无法提取有效 object_name
#         return ""
#     bucket, object_name = path_parts
#     if bucket != minio_bucket_name:
#         # bucket 名不匹配
#         return ""
#     return object_name

def convert_image_to_markdown(content: str, doc: dict, minio_bucket_name: str) -> str:
    """
    替换文本中的 <图片>...</图片> 为 markdown 格式。
    如果没有 image_url 或数量不足，则直接删除这些 <图片> 标签区域。
    """
    image_urls = doc.metadata.get("image_url", [])
    
    pattern = r"(?s)<图片>(.*?)</图片>"
    matches = list(re.finditer(pattern, content))

    offset = 0
    for i, match in enumerate(matches):
        alt_text = match.group(1)

        start = match.start() + offset
        end = match.end() + offset

        if i < len(image_urls):
            image_uuid = image_urls[i]
            if not image_uuid:
                replacement = ''
            else:
                markdown_img = f"![image](/api/con/files/{image_uuid}/file-preview)<{alt_text}>"
                replacement = markdown_img
        else:
            # 不足的图片数量，直接清空
            replacement = ''

        content = content[:start] + replacement + content[end:]
        offset += len(replacement) - (end - start)

    return content


@chain_decorator
def combine_docs(x):
    # docs
    docs = x.get('recall_nodes', [])
    combine_docs_list = []
    for doc in docs:

        if doc.metadata.get("data_type") in [
            VS_POINT_DATA_TYPE['Q']['value'], 
            VS_POINT_DATA_TYPE['QA']['value'],
            VS_POINT_DATA_TYPE['Q_E']['value']
        ]:
            content = ""
            try:
                q, a = doc.page_content.split("-->")
                content = "question:[q] --> answer:[a]".replace("[q]", q).replace("[a]", a)
            except Exception as e:
                content = doc.page_content
        else:
            content = doc.page_content
        
        if (x['configurable'].get('image_text_mix_response_enabled', 'off') == 'on'):
            # if doc.metadata.get('doc_content_type') == 'image_mix':
            content = convert_image_to_markdown(content, doc, "ekc-public")
        # doc.metadata['show_content'] = content
        combine_docs_list.append(content)
    if len(docs):
        docs_str = '已知信息(文档片段和参考QA)如下：\n'
    else:
        docs_str = "\n"
    for i, doc in enumerate(combine_docs_list):
        docs_str += f'<chunk {i + 1}>\n{doc}\n</chunk {i + 1}>\n'
    docs_str = docs_str.strip()
    return docs_str


@chain_decorator
def combine_historys(x):
    # historys
    history = x['history']
    history_context = format_history(history,x.get("multi_round_num", 0)) if history else ""
    return history_context


@chain_decorator
def remove_docs(x):
    e: exceptions.ExceedModelCapabilityError = x['exception']
    docs = x['recall_nodes']
    context = ''
    all_context = '\n'.join(list(map(lambda doc: doc.page_content, docs)) if len(docs) > 0 else "")

    avaliable_length = e.model_capability - e.max_tokens - (e.prompt_length - get_input_len(None, all_context))
    for doc in docs:
        doc.metadata['used'] = True
        if len(context) + len(doc.page_content) < avaliable_length:
            context += doc.page_content
        else:
            doc.metadata['used'] = False
    return context


def reformat_config(inputs, config=None):
    if config:
        trace = get_langfuse_trace(config)
        if trace:
            span = trace.span(name='reformat_config_inner')
        else:
            start_time = time.time()
    else:
        start_time = time.time()
        trace = None
    update_llm_runnables()
    update_enum_names()
    chain_configs = [spec.id for spec in chain.config_specs]

    for c in chain_configs:
        if c in inputs and 'value' in config_maps[c].fields and hasattr(config_maps[c].fields['value'], 'options'):
            try:
                inputs[c] = {v: k for k, v in config_maps[c].fields['value'].options.items()}[inputs[c]]
            except:
                inputs[c] = config_maps[c].fields['value'].options[inputs[c]]
        elif c in inputs and 'dict_values' in config_maps[c].fields and hasattr(config_maps[c].fields['dict_values'], 'options'):
            reverse_dict = {json.dumps(eval(v),ensure_ascii=False): k for k, v in config_maps[c].fields['dict_values'].options.items()}
            recovery_dict = defaultdict(list)
            for k,v in inputs[c].items():
                str_value = json.dumps({k:v},ensure_ascii=False)
                recovery_dict[c].append(reverse_dict.get(str_value, v))
            inputs[c] = recovery_dict[c]

    langchain_config = copy.deepcopy(inputs)
    langchain_config.update(inputs.get('config', {}).get('configurable', {}))

    for key, value in inputs.get('config', {}).get('llm_configurable', {}).items():
        if key in chain_configs:
            langchain_config[key] = value
        elif key in layout_schema['definitions']['llm_configurable']['properties']:
            for sub_key in inputs['config']['llm_configurable'][key]:
                langchain_config[sub_key] = inputs['config']['llm_configurable'][key][sub_key]
    for key, value in inputs.get('config', {}).get('strategy_configurable', {}).items():
        langchain_config[key] = value
        inputs[key] = value
    if config:
        langchain_config.update({k:v for k,v in config.items() if k not in ['tags', 'metadata', 'callbacks', 'recursion_limit', 'input', 'config', 'headers', 'configurable']})
    inputs['configurable'] = langchain_config
    inputs.update(langchain_config)
    if inputs['configurable'].get('output_llm') and not inputs['configurable'].get('sql_or_api_analysis_llm'):
        inputs['configurable']['sql_or_api_analysis_llm'] = inputs['configurable']['output_llm']
    if 'chat_assistant_llm' not in inputs:
        inputs['configurable']['chat_assistant_llm'] = inputs['configurable'].get('output_llm','default_llm')
        inputs['chat_assistant_llm']=inputs['configurable']['chat_assistant_llm']
    if 'chat_assistant_summary_llm' not in inputs:
        inputs['configurable']['chat_assistant_summary_llm'] = inputs['configurable'].get('sql_or_api_analysis_llm','default_llm')
        inputs['chat_assistant_summary_llm']=inputs['configurable']['chat_assistant_summary_llm']
    #logger.debug(f"the real used configurables are:{inputs['configurable']}")
    if trace:
        span.end()
    else:
        logger.debug(f'reformat_config time elasped {time.time() - start_time}')
    return inputs

inputs = {
    'app_id': lambda x: x.get('app_id'),
    "question": lambda x: x["question"],
    'history': lambda x: x['history'],
    'tags': lambda x: x['tags'],
    'org': lambda x: x['org'],
    "allow": lambda x: x.get('allow') or [],
    "deny": lambda x: x.get('deny') or [],
    "custom_tags": lambda x: x.get('custom_tags'),
    'custom_items': lambda x: x.get('custom_items'),
    'session_id': lambda x: x.get('session_id'),
    'kb_ids': lambda x: x.get('kb_ids'),
    "table_src_ids": lambda x: x.get('table_src_ids'),
    'multi_src_kb_ids':  lambda x: x.get('multi_src_kb_ids'),
    'data_src_ids': lambda x: x.get('data_src_ids'),
    'tool_ids': lambda x: x.get('tool_ids'),
    "metric_base_ids": lambda x: x.get('metric_base_ids'),
    'metric_template_base_ids': lambda x: x.get('metric_template_base_ids'),
    'search_tools': lambda x: x.get('search_tools'),
    "agent_id": lambda x: x.get('agent_id'),
    "client_id": lambda x: x.get('client_id'),
}


redis_data = RunnablePassthrough.assign(app_key=lambda x: f"app:{x['app_id']}") | \
             RunnablePassthrough.assign(**{
                 'kb_ids': lambda x: redis_hget(x['app_key'], 'kb_ids') if x.get('kb_ids') is None else x.get('kb_ids'),
                 "table_src_ids": lambda x: redis_hget(x['app_key'], 'table_src_ids') if x.get('table_src_ids') is None else x.get('table_src_ids'),
                 'data_src_ids': lambda x: redis_hget(x['app_key'], 'data_src_ids') if x.get('data_src_ids') is None else x.get('data_src_ids'),
                 'tool_ids': lambda x: redis_hget(x['app_key'], 'tool_ids', {}) if x.get('tool_ids') is None else x.get('tool_ids'),
                 'multi_src_kb_ids': lambda x: redis_hget(x['app_key'], 'multi_src_kb_ids') if x.get('multi_src_kb_ids') is None else x.get('multi_src_kb_ids'),
                 'config': lambda x: redis_hget(x['app_key'], 'config', {}),
                 'question': synonym_word_detect_chain,
                 "metric_base_ids": lambda x: redis_hget(x['app_key'], 'metric_base_ids') if x.get('metric_base_ids') is None else x.get('metric_base_ids'),
                 'metric_template_base_ids': lambda x: redis_hget(x['app_key'], 'metric_template_base_ids') if x.get('metric_template_base_ids') is None else x.get('metric_template_base_ids'),
                 'search_tools': lambda x: redis_hget(x['app_key'], 'search_tools', {}) if x.get('search_tools') is None else x.get('search_tools'),
             })
             
def merge_recall_nodes(x):
    if not x:
        return {'recall_nodes':[]}
    if x.get('multi_src_recall_nodes'):
        if x.get('recall_nodes'):
            x['recall_nodes']+=x.get('multi_src_recall_nodes')
        else:
            x['recall_nodes']=x.get('multi_src_recall_nodes')
    if x.get('data_src_recall_nodes'):
        if x.get('recall_nodes'):
            x['recall_nodes']+=x.get('data_src_recall_nodes')
        else:
            x['recall_nodes']=x.get('data_src_recall_nodes')
    return x

@chain_decorator
def retriever_binding(x, config):
    logger.info("start retriever binding")
    chain_config = x['configurable']
    chain_config.update(config['configurable'])
    response={}
    if x.get('kb_ids') or x.get('search_tools'):
        retriever = RunnableBinding(bound=multi_kbs_retrieve_chain, config={'configurable': chain_config})
        response['recall_nodes']=retriever
    if x.get('multi_src_kb_ids'):
        response['multi_src_recall_nodes']=multi_src_retrieve_chain
    if x.get('data_src_ids') or x.get('table_src_ids'):
        data_src_chain=db_retrieve_chain
        data_src_chain=data_src_chain.with_fallbacks([RunnableLambda(lambda x:[])], exceptions_to_handle=(exceptions.DBInfoError, exceptions.NoRetrivalError))
        response['data_src_recall_nodes']=data_src_chain
    return RunnablePassthrough.assign(**response)|merge_recall_nodes

@chain_decorator
def remote_retriever_binding(x, config):
    logger.info("start retriever binding")
    chain_config = x['configurable']
    chain_config.update(config['configurable'])
    retriever = RunnableBinding(bound=remote_retrieve_chain, config={'configurable': chain_config})
    return RunnablePassthrough.assign(recall_nodes=retriever)

@chain_decorator
def get_question_intent_method(inputs, config):
    recall_nodes = inputs.get('recall_nodes', [])
    logger.info("recall_nodes num: {}".format(len(recall_nodes)))

    if inputs['metric_template_base_ids'] and not inputs['search_tools']:
        sub_chain = 'metric_template_analysis_chain'
        set_thought(inputs['session_id'], 'chain', sub_chain)
        return RunnablePassthrough.assign(sub_chain=lambda x, v=sub_chain: v)
    
    if inputs['metric_base_ids'] and not inputs['search_tools']:
        sub_chain = 'text2metric_chain'
        set_thought(inputs['session_id'], 'chain', sub_chain)
        return RunnablePassthrough.assign(sub_chain=lambda x, v=sub_chain: v)
    response_type = []
    sub_chain=None
    recall_nodes_type=list(map(lambda x: x.metadata['data_type'], recall_nodes))
    kb_types= [
        VS_POINT_DATA_TYPE['QA']['value'],
        VS_POINT_DATA_TYPE['Q']['value'],
        VS_POINT_DATA_TYPE['Q_E']['value'],
        VS_POINT_DATA_TYPE['DOC']['value'],
        VS_POINT_DATA_TYPE['WEBSITE']['value'],
        VS_POINT_DATA_TYPE['WEB_SEARCH']['value'],
        VS_POINT_DATA_TYPE['external_src']['value']
    ]
    if recall_nodes and recall_nodes[0].metadata['data_type'] == VS_POINT_DATA_TYPE['Q_API']['value']:
        sub_chain = "text2kb_chain"
        response_type.append('QaApi')
    elif recall_nodes and recall_nodes[0].metadata['data_type'] == VS_POINT_DATA_TYPE['tool']['value']:
        sub_chain = "text2kb_chain"
        response_type.append('Api')
    elif recall_nodes and recall_nodes[0].metadata['data_type'] == VS_POINT_DATA_TYPE['Q_DB']['value']:
        sub_chain = "text2kb_chain"
        response_type.append('QaDbQuery')
    elif recall_nodes and any(_x in kb_types for _x in recall_nodes_type):
        sub_chain = "text2kb_chain"
        if VS_POINT_DATA_TYPE['QA']['value'] in recall_nodes_type or \
           VS_POINT_DATA_TYPE['Q']['value'] in recall_nodes_type or \
           VS_POINT_DATA_TYPE['Q_E']['value'] in recall_nodes_type:
            response_type.append('QA')
        if VS_POINT_DATA_TYPE['DOC']['value'] in recall_nodes_type:
            response_type.append('DOC')
        if VS_POINT_DATA_TYPE['WEBSITE']['value'] in recall_nodes_type:
            response_type.append('Website')
        if VS_POINT_DATA_TYPE['WEB_SEARCH']['value'] in recall_nodes_type:
            response_type.append('WebSearch')
            web_search_nodes = list(filter(lambda x: x.metadata['data_type'] == VS_POINT_DATA_TYPE['WEB_SEARCH']['value'], recall_nodes))
            web_search_results = make_sources_documents(web_search_nodes)[1]

            if web_search_results:
                set_thought(inputs['session_id'], 'web_search_results', [m.dict() for m in web_search_results])
        if VS_POINT_DATA_TYPE['external_src']['value'] in recall_nodes_type:
            response_type.append('ExternalKnowledge')

    if recall_nodes and any(_x in [VS_POINT_DATA_TYPE['data_src']['value']] for _x in recall_nodes_type):
        response_type=['MultiSrc']
        sub_chain='text2sql_kb_chain'
        # set_thought(inputs['session_id'], 'chain', 'text2sql_chain')
    
    if recall_nodes and any(_x in [VS_POINT_DATA_TYPE['MULTISRC']['value']] for _x in recall_nodes_type):
        response_type.append('MultiSrc')
    # text2cypher_chain only by answer_priority
    if inputs.get('answer_priority', "") == '知识图谱优先' or inputs.get("configurable", {}).get('answer_priority',
                                                                                                 "") == 'graph_filter':
        sub_chain = "text2kb_chain"
        response_type.append('GRAPH')
    logger.debug(f"locate chain: 【{sub_chain}】 based on question intent")
    # set_thought(inputs['session_id'], 'chain', sub_chain) 
    return RunnablePassthrough.assign(sub_chain=lambda x, v=sub_chain: v, response_type=lambda x, v=response_type: v)


@chain_decorator
def model_binding(x, config):
    # chain_config is from redis
    chain_config = x['configurable'] if 'configurable' in x else {}
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config 
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])
    subscript_enabled = config['configurable'].get("response_subscript_enabled", "false")
    image_text_mix_enabled = config['configurable'].get("image_text_mix_response_enabled", 'off')
    
    if not 'template_name' in x:
        # 根据subscript_enabled和image_text_mix_response_enabled选择模板
        # 没有角标的优先级最高
        if subscript_enabled == "false":
            template_value = 'Chinese_answer_template'
        elif image_text_mix_enabled != 'on':
            template_value = 'knowledge_base_system_prompt_orginal'
        else:
            template_value = 'knowledge_base_prompt'
        return RunnablePassthrough.assign(template_name=RunnableValue(value=template_value)) | \
            RunnablePassthrough.assign(question=lambda x: x['origin_question']) | \
            RunnableBinding(bound=prompt, config={'configurable': chain_config}) | \
            RunnableBinding(bound=models[x.get('model_name', 'output_llm')], config={'configurable': chain_config})
    else:
        return RunnablePassthrough.assign(question=lambda x: x['origin_question']) | \
            RunnableBinding(bound=prompt, config={'configurable': chain_config}) | \
            RunnableBinding(bound=models[x.get('model_name', 'output_llm')], config={'configurable': chain_config})



@chain_decorator
def question_refine_model_binding(x, config):
    # chain_config is from redis
    chain_config = x['configurable']
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])
    # use output_llm
    chat_model = RunnableBinding(bound=models[x.get('model_name', 'output_llm')], config={'configurable': chain_config})
    return prompt | chat_model


@chain_decorator
def unknown_binding(x, config):
    chain_config = x['configurable']
    chain_config.update(config['configurable'])
    return {'requirement':
                RunnableBranch(
                    (lambda x: x.get('template_name'), RunnablePassthrough()),
                    RunnablePassthrough.assign(template_name=RunnableValue(value='Chinese_answer_template'))
                ) | \
                RunnablePassthrough.assign(context=RunnableValue(value='')) | \
                prompt
            } | \
        RunnablePassthrough.assign(template_name=RunnableValue(value='unknown_prompt')) | \
        RunnableBinding(bound=prompt, config={'configurable': chain_config}) | \
        RunnableBinding(bound=models['output_llm'], config={'configurable': chain_config})


model_output_runnable = {
    'response_variables': charge,
    'model_output': model_binding
}

unkonwn_output_runnable = {
    'response_variables': charge,
    'model_output': unknown_binding
}

text2kb_chain = RunnablePassthrough.assign(history_context=combine_historys) | \
                model_output_runnable
text2kb_chain = text2kb_chain.with_fallbacks(
    [RunnablePassthrough.assign(context=remove_docs) | model_output_runnable],
    exceptions_to_handle=(exceptions.ExceedModelCapabilityError,),
    exception_key='exception')

rag_chain = RunnableBranch(
    (lambda x: 'UNKNOWN' in x.get('response_type', []), unkonwn_output_runnable),
    text2kb_chain
)


@chain_decorator
def llm_or_unknown(inputs, config):
    chain_config = inputs['configurable']
    chain_config.update(config['configurable'])

    if inputs.get('recall_nodes'):
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['MultiSrc']))
    elif inputs['free_mode']=='off':
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['UNKNOWN']))
    else:
        return RunnablePassthrough.assign(response_type=RunnableValue(values=['LLM']),
                                            template_name=RunnableValue(value='free_prompt'),
                                            model_name=RunnableValue(value='free_mode_llm'))



def update_response_type(x):
    if 'MultiSrc' in x['response_type']:
        x['response_type']=['DbQuery','MultiSrc']
    else:
        x['response_type']=['DbQuery']
    return x

text2db_or_rag = RunnableBranch(
    (lambda x: x['answer_priority'] == 'data_filter',
     (update_response_type | rag_chain).with_fallbacks(
            [llm_or_unknown | rag_chain], exceptions_to_handle=(exceptions.DBInfoError, exceptions.NoRetrivalError))),
    rag_chain
)

text2db_or_api = RunnableBranch(
    (lambda x: x['answer_priority'] == 'data_filter',
     (update_response_type | rag_chain).with_fallbacks(
            [llm_or_unknown | rag_chain], exceptions_to_handle=(exceptions.DBInfoError, exceptions.NoRetrivalError))),
    rag_chain
)

sub_chain_dispatcher = RunnablePassthrough.assign(context=combine_docs) | \
    RunnableBranch(
        (lambda x: x['sub_chain'] == 'text2sql_chain', rag_chain),
        (lambda x: x['sub_chain'] == 'text2api_chain', rag_chain),
        (lambda x: x['sub_chain'] == 'text2kb_chain', text2db_or_rag),
        (lambda x: x['sub_chain'] == 'text2cypher_chain', rag_chain),
        (lambda x: x['sub_chain'] == 'text2metric_chain', (text2metric_chain ).with_fallbacks(
            [llm_or_unknown | rag_chain], exceptions_to_handle=(exceptions.DBInfoError, exceptions.NoRetrivalError))),
        (lambda x: x['sub_chain'] == 'text2sql_kb_chain',RunnablePassthrough.assign(data_source_query_info=lambda x:x['data_src_recall_nodes'][0].metadata['data_source_query']) |\
                                                         model_output_runnable| table2chart_interface),
        (lambda x: x['sub_chain'] == 'metric_template_analysis_chain', (metric_template_analysis_chain ).with_fallbacks(
            [llm_or_unknown | rag_chain], exceptions_to_handle=(exceptions.DBInfoError, exceptions.NoRetrivalError))),
        (lambda x: x.get('sub_chain') is None,llm_or_unknown|RunnablePassthrough.assign(history_context=combine_historys) | RunnableBranch((lambda x:'UNKNOWN' in x['response_type'],unkonwn_output_runnable),model_output_runnable)),
        rag_chain
)


@chain_decorator
def question_refine_binding(x, config):
    # chain_config is from redis
    chain_config = x['configurable']
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])

    multi_round_num = RunnableValue(value=chain_config.get("multi_round_num", 0))

    return RunnablePassthrough.assign(multi_round_num=multi_round_num) | \
        RunnablePassthrough.assign(origin_question=lambda x: x.get("origin_question", x["question"])) | \
        RunnableBranch(
            (lambda x: x.get('refined_question', None) is not None,
             RunnablePassthrough.assign(question=lambda x: x['refined_question'])),
            # reuse
            RunnablePassthrough.assign(question=refine_query_with_history)
        ) | RunnablePassthrough(lambda x: logger.debug(
            "multi_round_num config is {}, Origin question is: {}, refined with history question is: {}".format(
                x["multi_round_num"], str(x["origin_question"]), str(x["question"]))))


get_retriever_doc_kvs = RunnableBranch(
    (lambda x: x.get('retriever_doc_kvs', None) is not None, lambda x: x['retriever_doc_kvs']),  # reuse
    parameters_extractor
)


@chain_decorator
def sub_request_chain(x):
    # TODO support other sub chains
    sub_chain_mapping = {'text2metric_chain': text2metric_chain, "metric_template_analysis_chain": metric_template_analysis_chain}
    # TODO support multiple sub requests
    for sub_chain, requests in x['sub_requests'][0]:
        if requests:
            return RunnablePassthrough(lambda x: set_thought(x['session_id'], 'chain', sub_chain)) | \
                RunnablePassthrough.assign(sub_requests=lambda x, v=requests: v) | sub_chain_mapping[sub_chain]
    else:
        return x


@chain_decorator
def klg_app_chain(x, config):
    chain_config = x['configurable']
    chain_config.update(config['configurable'])
    chain = RunnableSequence(RunnableParallel(input1=question_refine_binding, retriever_doc_kvs=get_retriever_doc_kvs) | \
                             RunnableLambda(lambda x: {**x['input1'], 'retriever_doc_kvs': x['retriever_doc_kvs']}) | \
                             RunnablePassthrough(lambda x: logger.debug(
                                 f"app_id:{x['app_id']}, kb_ids:{x['kb_ids']},api_ids:{x['tool_ids']}, parameters_extractor result:{x['retriever_doc_kvs']}")) | \
                             RunnableBranch(
                                 (lambda x: x.get('sub_requests'),
                                  RunnablePassthrough(
                                      lambda x: set_thought(x['session_id'], 'chain', 'text2metric_chain')) | \
                                  sub_request_chain),
                                 (lambda x: int(x.get('retrieve_mode', 0)) == 1,
                                  RunnableSequence(
                                      RunnableLambda(lambda x: {**x, 'recall_nodes': []}),
                                      remote_retriever_binding,
                                      get_question_intent_method,
                                      sub_chain_dispatcher
                                  )
                                  ),
                                 (lambda x: not any([x.get('kb_ids'), x.get('tool_ids', {}).get('api_ids'), x.get('data_src_ids'),
                                                     x.get('multi_src_kb_ids'), x.get('search_tools'),x.get('table_src_ids')]),
                                  RunnableSequence(
                                      RunnableLambda(lambda x: {**x, 'recall_nodes': []}),
                                      get_question_intent_method,
                                      sub_chain_dispatcher
                                  )
                                  ),
                                 RunnableSequence(
                                     retriever_binding,
                                     get_question_intent_method,
                                     sub_chain_dispatcher
                                 )
                             ),
                             astreaming_parser,
                             name='klg_app_chain_sequece')

    return RunnableBinding(bound=chain, config={'configurable': chain_config})


@chain_decorator
def chat_chain(x, config):
    chain_config = x['configurable']
    chain_config.update(config['configurable'])
    chain = question_refine_binding | RunnablePassthrough.assign(
        template_name=RunnableValue(value='chat_assistant_attachment_chat_prompt'),
        context=RunnableValue(value=''),
        history_context=combine_historys,
        response_type=RunnableValue(values=['LLM'])) | \
            model_output_runnable | astreaming_parser
    return RunnableBinding(bound=chain, config={'configurable': chain_config})


redis_dispatcher = RunnableBranch(
    # has klg_app_id 
    (lambda x: x.get('app_id') or x.get('metric_base_ids') or x.get('metric_template_base_ids'), RunnableSequence(redis_data,
                                                 reformat_config,
                                                 klg_app_chain,
                                                 name='redis_dispatcher_with_app_id')
     ),
    # no klg_app_id
    reformat_config | chat_chain
)
redis_dispatcher.name = 'redis_dispatcher'





def check_history(x):
    if isinstance(x['history'], dict):
        #history_length = len([history for history in x["history"] if history.get("role") != 'file'])
        history_length = len([history for history in x["history"]])
    else:
        #history_length = len([history for history in x["history"] if history.role != 'file'])
        history_length = len([history for history in x["history"]])
    return int(x["multi_round_num"]) >= 0 and history_length > 0


refine_query_with_history = RunnablePassthrough.assign(history=synonym_history_detect_chain)|\
    RunnableBranch(
        (check_history,
        RunnablePassthrough.assign(chat_history=lambda x: format_history(x["history"], int(x["multi_round_num"]))) | \
        RunnablePassthrough.assign(template_name=RunnableValue(value='refine_query_with_history_template')) | \
        question_refine_model_binding | \
        ekcStrOutputParser()
        ),

        lambda x: x["question"]
    )


@chain_decorator
async def throw_exception(inputs, config):
    exception = inputs['exception']
    try:
        if isinstance(exception, exceptions.EarlyStopError):
            return dict(**exception.response_variables, **exception.model_output)
        if isinstance(exception, OpenAIError):
            logger.error(traceback.format_exception(exception))
            if hasattr(exception, 'message'):
                message = exception.message
            else:
                message = "empty message error"
            if isinstance(exception, InternalServerError):
                status_code = 500
                message = format_error_response(status_code)
                exception = LLMCallError(message=message, status_code=status_code)
            elif isinstance(exception, APITimeoutError):
                status_code = 408
                message = format_error_response(status_code)
                exception = LLMCallTimeoutError(message=message, status_code=status_code)
            elif isinstance(exception, APIConnectionError):
                status_code = 402
                message = format_error_response(status_code)
                exception = LLMCallError(message=message, status_code=status_code)
            elif isinstance(exception, RateLimitError):
                status_code = 429
                message = format_error_response(status_code)
                exception = LLMRateLimitError(message=message, status_code=status_code)
            else:
                if hasattr(exception, 'status_code'):
                    status_code = exception.status_code
                    message = format_error_response(status_code=status_code)
                else:
                    status_code = 501
                exception = LLMCallError(message=message, status_code=status_code)
        if isinstance(exception, exceptions.ReadTimeout):
            status_code = 408
            message = format_error_response(status_code)
            exception = exceptions.LLMCallTimeoutError(message=message, status_code=status_code)
        hasattr(exception, 'status_code')
        hasattr(exception, 'error_code')
        hasattr(exception, 'message')
    except:
        logger.error(traceback.format_exception(exception))
        exception = exceptions.ApplicationError(str(exception))

    session_id = inputs.get('session_id')
    if session_id:
        set_thought(session_id, 'end', 1)
    return RunnableNotice(error=exception)


exception_handler = throw_exception | astreaming_parser


def insert_custom_items(x):
    if x.get('custom_items'):
        custom_items = x.pop('custom_items')
        x.update(custom_items)
    return x


chain = add_time_stamp_start | \
        RunnablePassthrough.assign(**inputs, **config_maps) | \
        RunnablePassthrough.assign(origin_question=lambda x:x['question'])| \
        insert_custom_items
        
chain = RunnableSequence(chain,
                         redis_dispatcher,
                         name='convsersation_chain')

chain = chain.with_fallbacks([exception_handler], exceptions_to_handle=exceptions.errors, exception_key='exception')
chain = chain.with_types(input_type=ConversationChainInputModel, output_type=ConversationChainOutputModel)
