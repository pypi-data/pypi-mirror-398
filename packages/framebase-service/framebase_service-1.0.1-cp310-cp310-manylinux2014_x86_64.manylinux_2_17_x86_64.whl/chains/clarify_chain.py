# cython: annotation_typing = False
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBinding,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    chain as chain_decorator,
)
import uuid
from community.models.stroutput_parser import ekcStrOutputParser
from langchain.schema.messages import HumanMessage, AIMessage
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langchain_core.output_parsers import JsonOutputParser
from framebase.models import models,model_option_mapping
from framebase import config_maps
from framebase.values import RunnableValue
from framebase.notices import RunnableNotice
from framebase.prompts import chain as prompt, mappings as prompt_mappings
from framebase.retrievers import mappings as VS_POINT_DATA_TYPE
from chains.text2metric.service.metric import process_metric_retrieve_result
from utils.dbs import redis_hget,get_redis_data,hscan_redis_data
from utils.logger import logger
from utils.tools import get_now_time, add_time_stamp_start
from utils.langfuse_tools import langfuse_handler

from .protocol import ClarifyChainInputModel,ClarifyChainOutputModel
from .retriever_chain import recommend_chain,metric_retrieve_chain
from .conversation_chain import reformat_config,format_history


CONFIG_MAX_RELATED_QUESTIONS = 3 #maximum related questions returned
CONFIG_MAX_HISTORY_LEN = 1500
CONFIG_MAX_RECALL_LEN = 2048

def get_kb_ids(app_key):
    ids = get_redis_data(app_key, "kb_ids")
    if ids is None or len(ids) == 0:
        return None
    return ids

redis_data=RunnableBranch(
    # no app id
    (lambda x:not x.get('app_id'), RunnablePassthrough()),
    # has app id
    RunnablePassthrough.assign(app_key=lambda x:f"app:{x['app_id']}") | \
    RunnablePassthrough.assign(**{
        'kb_ids': lambda x: redis_hget(x['app_key'], 'kb_ids') if x.get('kb_ids')is None else x.get('kb_ids'),
        "metric_base_ids": lambda x: redis_hget(x['app_key'], 'metric_base_ids') if x.get('metric_base_ids') is None else x.get('metric_base_ids'),
        'config':lambda x:redis_hget(x['app_key'],'config',{})
    })
)

def get_latest_human_question(x):
    history = x["history"]
    #history should have at least 2 msg: human, ai
    return history[-2].content


def clarify_questions_output(x):
    return x.get('clarify_choices',[])

no_clarify_questions_generated_chain = RunnableLambda(lambda x: {}) | \
     RunnableLambda(clarify_questions_output)

@chain_decorator
def clarify_without_knowledge(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain= RunnablePassthrough.assign(chat_history = lambda x: format_history(x["history"]),information=lambda x:"") | \
           RunnablePassthrough.assign(template_name=RunnableValue(value='clarify_recommend_template')) | \
           prompt | models['output_llm'] | \
           JsonOutputParser() | \
           RunnableLambda(clarify_questions_output)

    return chain

free_mode_checker_chain = RunnableBranch(
    (lambda x: x["free_mode"] == 'on' or x["free_mode"] == '是' or x.get("app_type",'') == 'chat_assistants', clarify_without_knowledge),
    no_clarify_questions_generated_chain)




@chain_decorator
def combine_docs(x):
    docs=x['recall_nodes']
    return '\n\n'.join(list(map(lambda doc:doc.page_content, docs)) if len(docs)>0 else "")[:CONFIG_MAX_RECALL_LEN]

@chain_decorator
def clarify_with_knowledge(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain= RunnablePassthrough.assign(chat_history = lambda x: format_history(x["history"],x['multi_round_num'])) | \
           RunnablePassthrough.assign(information = combine_docs,
                                      template_name=RunnableValue(value='clarify_recommend_template')) | \
           prompt| models['output_llm'] | \
           JsonOutputParser() | \
           RunnableLambda(clarify_questions_output)

    return chain

recall_nodes_dispatcher=RunnableBranch(
    # has recall_nodes
    (lambda x:x.get('recall_nodes'),   clarify_with_knowledge),
    # no recall_nodes
    free_mode_checker_chain
)

@chain_decorator
def recommend_retrieve_chain(x,config):
    chain= RunnablePassthrough.assign(negative_query = lambda x: x.get('candidates',[])) | \
           RunnablePassthrough.assign(recall_nodes = recommend_chain) | \
           recall_nodes_dispatcher

    return chain

def get_usage(x, config):
    token_cost = []
    usage = hscan_redis_data('usage:'+x['session_id'],'*')
    for k, v in usage.items():
        if v is not None:
            v.update({'model_name': model_option_mapping.get(k),'id':k})
            token_cost.append(v)
          
    usage = {
        "time_stamp": config["metadata"].get("time_stamp", {}),
        "token_cost": token_cost
    }
    usage['time_stamp']["chain_end_time"] = get_now_time()
    if not usage['time_stamp'].get("first_char_time"):
        usage['time_stamp']["first_char_time"] = usage['time_stamp']["chain_end_time"]
    return usage


dispatcher=RunnableBranch(
    # has metric base id or kb_ids
    (lambda x:x.get('metric_base_ids') or x.get('kb_ids'), recommend_retrieve_chain),

    # no kb_ids
    free_mode_checker_chain
)

app_id_dispatcher=RunnableBranch(
    # has app_id
    (lambda x:x.get('app_id'), dispatcher),
    no_clarify_questions_generated_chain
)

invalid_candidates_chain = RunnablePassthrough(lambda x: logger.warning("clairfy chain:Too short candidates: "+str(x['candidates']))) |\
    no_clarify_questions_generated_chain

candidate_dispatcher= RunnableBranch(
    # if
    (lambda x:not len(x['candidates']), invalid_candidates_chain),
    # else
    app_id_dispatcher
)

def check_session_id(x,config):
    if not x.get('session_id'):
        x['session_id'] = str(uuid.uuid4())
    config['input']['session_id'] = x['session_id']
    return x

chain = add_time_stamp_start |\
        RunnablePassthrough.assign(**config_maps) |\
        RunnablePassthrough.assign(answer_priority=lambda x:'指标和问答优先') |\
        check_session_id |\
        redis_data |reformat_config |\
        RunnablePassthrough.assign(clarify_choices = candidate_dispatcher) |\
        RunnablePassthrough.assign(usage=get_usage)


chain = chain.with_types(input_type=ClarifyChainInputModel,output_type=ClarifyChainOutputModel)
