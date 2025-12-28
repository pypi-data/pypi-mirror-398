# cython: annotation_typing = False
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBinding,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    chain as chain_decorator,
)
from community.models.stroutput_parser import ekcStrOutputParser
from langchain.schema.messages import HumanMessage, AIMessage
from langchain_community.callbacks.openai_info import OpenAICallbackHandler

from framebase.models import models,model_option_mapping
from framebase import config_maps
from framebase.values import RunnableValue
from framebase.notices import RunnableNotice
from framebase.prompts import chain as prompt, mappings as prompt_mappings
from framebase.retrievers import mappings as VS_POINT_DATA_TYPE
from chains.text2metric.service.metric import process_metric_retrieve_result
from utils.dbs import redis_hget,get_redis_data
from utils.logger import logger
from utils.tools import get_now_time, add_time_stamp_start
from utils.langfuse_tools import langfuse_handler

from .protocol import RelatedQuestionsChainInputModel,RelatedQuestionsChainOutputModel
from .retriever_chain import multi_kbs_retrieve_chain,metric_retrieve_chain
from .conversation_chain import reformat_config


CONFIG_MAX_RELATED_QUESTIONS = 3 #maximum related questions returned
CONFIG_MAX_HISTORY_LEN = 1500
CONFIG_MAX_RECALL_LEN = 2048

inputs = {
    'app_id': lambda x: x.get('app_id'),
    'history': lambda x: x['history'],
    'kb_ids': lambda x: x.get('kb_ids'),
    "allow": lambda x: x.get('allow'),
    "deny": lambda x: x.get('deny'),
}

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

def format_history(history):
    chat_history = ""
    #the last one must be "ai" msg and len(history)>=2
    for i in range(len(history)-2, -1, -2):
        item = f"用户：{history[i]['content']}" + "\n" + f"助手：{history[i+1]['content']}"
        if len(chat_history)+len(item) <= CONFIG_MAX_HISTORY_LEN:
            chat_history = item + "\n" + chat_history
        else:
            item_len = CONFIG_MAX_HISTORY_LEN - len(chat_history)
            chat_history = item[:item_len] + "\n" + chat_history

    return chat_history

def get_latest_human_question(x):
    history = x["history"]
    #history should have at least 2 msg: human, ai
    return history[-2]['content']

@chain_decorator
def rel_questions_no_kb_ids_model_binding(x,config):
    # chain_config is from redis
    chain_config = x['configurable']
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])
    chat_model=RunnableBinding(bound=models['related_question_llm'],config={'configurable':chain_config})
    return prompt | chat_model

def rel_questions_output(x:str):
    if x.strip() == '': return []
    qs = x.strip().split("\n")[:CONFIG_MAX_RELATED_QUESTIONS]
    qout = []
    for i,q in enumerate(qs):
        q = q.strip()
        prefixs = [str(i+1)+".", str(i+1)+"、", str(i+1)+" ", str(i+1)+")", str(i+1)+"）", "Q：", "Q:", "问：", "问:"] #2 chars prefix
        if len(q)> 0 and q[:2].upper() in prefixs:
            #remove digital prefix for baichuan2/qwen1.5
            q = q[2:].strip()
        if len(q)>0 and q[0]=='"' and q[-1]=='"':
            #remove unnecessary quotes at both end
            q=q[1:-1]
        #remove '-->' to get question part
        if '-->' in q:
            q=q.split('-->')[0].strip()
        if len(q)>0:
            qout.append(q)

    return qout

no_rel_questions_generated_chain = RunnableLambda(lambda x: "") | \
     RunnableLambda(rel_questions_output)

@chain_decorator
def rel_questions_no_kb_ids_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain= RunnablePassthrough.assign(chat_history = lambda x: format_history(x["history"])) | \
           RunnablePassthrough.assign(template_name=RunnableValue(value='related_questions_no_recall_template')) | \
           rel_questions_no_kb_ids_model_binding | \
           ekcStrOutputParser() | \
           RunnableLambda(rel_questions_output)

    return RunnableBinding(bound=chain,config={'configurable':chain_config})

free_mode_checker_chain = RunnableBranch(
    (lambda x: x["free_mode"] == 'on' or x["free_mode"] == '是' or x.get("app_type",'') == 'chat_assistants', rel_questions_no_kb_ids_chain),
    no_rel_questions_generated_chain)

@chain_decorator
def retriever_binding(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    retriever=RunnableBinding(bound=multi_kbs_retrieve_chain,config={'configurable':chain_config})
    return RunnablePassthrough.assign(recall_nodes = retriever)

@chain_decorator
def refine_metric_recall(x):
    metric_infos=process_metric_retrieve_result(x).get('metric_infos',[])
    metric_info_str=''
    for i,metric_info in enumerate(metric_infos[:x['metric_intent_max_num']]):
        metric_info_str+=",".join([f"{key}:'{value}'"[:500] for key,value in metric_info.items() if key != 'definition'])
        metric_info_str+='\n'
    return metric_info_str

@chain_decorator
def metric_retriever_binding(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    retriever=RunnableBinding(bound=metric_retrieve_chain,config={'configurable':chain_config})
    chain = RunnablePassthrough.assign(raw_metric_info=retriever)|refine_metric_recall
    
    return RunnablePassthrough.assign(metric_info = chain,chat_history=lambda x:format_history(x['history']))

@chain_decorator
def filter_recall_nodes(inputs):
    recall_nodes=inputs.get('recall_nodes')
    logger.info("recall_nodes num: {}".format(len(recall_nodes)))
    recall_nodes = recall_nodes[-3:] #get last 3 more irrelevant nodes
    new_recall_nodes = []
    for i in range(len(recall_nodes)):
        node = recall_nodes[i]
        if node.metadata['data_type'] in [VS_POINT_DATA_TYPE['QA']['value'],VS_POINT_DATA_TYPE['Q']['value'],
            VS_POINT_DATA_TYPE['Q_E']['value'], VS_POINT_DATA_TYPE['DOC']['value'],VS_POINT_DATA_TYPE['WEBSITE']['value']]:
            new_recall_nodes.append(node)
    logger.info("related question recall_nodes num: {}".format(len(new_recall_nodes)))
    if new_recall_nodes:
        logger.info("related question recall_nodes[0] is: {}".format(new_recall_nodes[0]))
    if len(new_recall_nodes) == 0:
        inputs['recall_nodes'] = None
    else:
        inputs['recall_nodes'] = new_recall_nodes

    return inputs

@chain_decorator
def combine_docs(x):
    docs=x['recall_nodes']
    return '\n\n'.join(list(map(lambda doc:doc.page_content, docs)) if len(docs)>0 else "")[:CONFIG_MAX_RECALL_LEN]

@chain_decorator
def rel_questions_with_recall_nodes_model_binding(x,config):
    # chain_config is from redis
    chain_config=x['configurable']
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])

    chat_model=models["related_question_llm"]

    return RunnablePassthrough.assign(template_name=RunnableValue(value='related_questions_with_recall_template')) | \
            RunnableBinding(bound=prompt,config={'configurable':chain_config}) | \
            RunnableBinding(bound=chat_model,config={'configurable':chain_config})

@chain_decorator
def rel_questions_with_recall_nodes_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain= RunnablePassthrough.assign(chat_history = lambda x: format_history(x["history"])) | \
           RunnablePassthrough.assign(context = combine_docs) | \
           rel_questions_with_recall_nodes_model_binding | \
           ekcStrOutputParser() | \
           RunnableLambda(rel_questions_output)

    return RunnableBinding(bound=chain,config={'configurable':chain_config})

recall_nodes_dispatcher=RunnableBranch(
    # has recall_nodes
    (lambda x:x.get('recall_nodes'), reformat_config | rel_questions_with_recall_nodes_chain),
    # no recall_nodes
    reformat_config| free_mode_checker_chain
)

@chain_decorator
def rel_questions_with_kb_ids_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain= RunnablePassthrough.assign(question = lambda x: get_latest_human_question(x)) | \
           retriever_binding | \
           filter_recall_nodes | \
           recall_nodes_dispatcher

    return RunnableBinding(bound=chain,config={'configurable':chain_config})

def get_usage(x, config):
    token_cost = []
    for k, v in config["metadata"].get("usage", {}).items():
        v.update({'id': model_option_mapping.get(k),'model_name':k})
        token_cost.append(v)
    usage = {
        "time_stamp": config["metadata"].get("time_stamp", {}),
        "token_cost": token_cost
    }
    usage['time_stamp']["chain_end_time"] = get_now_time()
    if not usage['time_stamp'].get("first_char_time"):
        usage['time_stamp']["first_char_time"] = usage['time_stamp']["chain_end_time"]
    return usage

def metric_base_related_chain(x,config):
    chain_config = x['configurable']
    chain_config.update(config['configurable'])
    chat_model=RunnableBinding(bound=models['related_question_llm'],config={'configurable':chain_config})

    return  RunnablePassthrough.assign(question = lambda x: get_latest_human_question(x),
                                       template_name=RunnableValue(value='metric_related_questions_template'))|\
            metric_retriever_binding| prompt | chat_model| ekcStrOutputParser() | \
            RunnableLambda(rel_questions_output)
    

dispatcher=RunnableBranch(
    # has metric base id
    (lambda x:x.get('metric_base_ids'), metric_base_related_chain),
    # has kb_ids
    (lambda x:x.get('kb_ids'), rel_questions_with_kb_ids_chain),
    # no kb_ids
    free_mode_checker_chain
)

app_id_dispatcher=RunnableBranch(
    # has app_id
    (lambda x:x.get('app_id'), dispatcher),
    # no app_id, ex. chat-assistant app during creating and testing
    free_mode_checker_chain
)

invalid_history_chain = RunnablePassthrough(lambda x: logger.warning("related_questions:Too short history: "+str(x['history']))) |\
    no_rel_questions_generated_chain

history_dispatcher= RunnableBranch(
    # history is incorrect
    (lambda x:len(x['history'])<2, invalid_history_chain),
    # else
    app_id_dispatcher
)

#to get related_question_llm_name for get_usage()
def get_related_question_llm_name(x):
    name = x.get('configurable', {}).get('related_question_llm', '')
    if name == '': name = x.get('configurable', {}).get('chat_assistant_llm', '')  #chat_assistant
    return name


chain = add_time_stamp_start |\
        RunnablePassthrough.assign(**inputs,**config_maps) |\
        RunnablePassthrough.assign(answer_priority=lambda x:'指标和问答优先') |\
        redis_data |reformat_config |\
        RunnableParallel(related_questions = history_dispatcher, related_question_llm_name = get_related_question_llm_name) |\
        RunnableParallel(related_questions=lambda x:x['related_questions'], usage=get_usage)

callbacks = []
if OpenAICallbackHandler:
    callbacks.append(OpenAICallbackHandler())
if callbacks:
    chain = chain.with_config(config={"callbacks": callbacks})
chain = chain.with_types(input_type=RelatedQuestionsChainInputModel,output_type=RelatedQuestionsChainOutputModel)
