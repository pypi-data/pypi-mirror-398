# cython: annotation_typing = False
import json
from langchain_core.runnables import (
    RunnablePassthrough,RunnableParallel,
    RunnableBranch,RunnableSequence,
    RunnablePick,
    RunnableLambda,
    chain as chain_decorator
)
from langchain_community.docstore.document import Document
from framebase.output_parsers import astreaming_parser, charge
from framebase.prompts import chain as prompt_template
from framebase.models import models

import pandas as pd
import numpy as np
from typing import List

from community.retrievers.remote_retriever import remote_agent_retriever
from community.retrievers.multi_src_retriever import multi_src_retriever
from framebase.retrievers import retrievers, config_map, mappings as retriever_mappings
from framebase.values import RunnableValue
from framebase.embeddings import rerank_embeddings,get_embedding_runnables,bm25_embedding
from .loader_splitter_chain import chain as loader_splitter_chain
from utils.exceptions import NoRetrivalError,ApplicationError
from utils.langfuse_tools import get_langfuse_trace
from utils.dbs import collection_exists,get_collection
from .protocol import RetrieverChainInputModel, MultiRetrieverChainInputModel, RetrieverChainOutputModel, \
    RemoteRetrieverChainInputModel
from utils.dbs import get_redis_data
from utils.logger import logger
from utils.exceptions import DBInfoError

def sigmoid(x):  
    return 1 / (1 + np.exp(-x))  

@chain_decorator
def make_retriever_input(x):
    if x.get('queries'):
        query=chain_decorator(lambda x:x['queries'])
    else:
        query=chain_decorator(lambda x:x['question'])
    # get embedding runnable by kb_id
    embedding_ids=[]
    for kb_id in x.get("retriever_settings"):
        embedding_id = x.get("retriever_settings")[kb_id].get("embedding_model",{}).get("embedding_id")
        if embedding_id:
            embedding_ids.append(embedding_id)
    embedding_ids=list(set(embedding_ids))
    embedding_runnable = {}
    for embedding_id in embedding_ids: 
        for i,er in enumerate(get_embedding_runnables()[embedding_id]):
            embedding_runnable[er["model_name"]]=er["runnable"]
            embedding_runnable['bm25']=bm25_embedding['runnable']
    vector_configs={}
    collections=[]
    if x.get('tool_ids') and x.get('tool_ids').get('api_ids'):
        if collection_exists('API_summary_collection'):
            collections.append('API_summary_collection')
    for kb_id in x.get('kb_ids') or []:
        # 特殊处理 app_-1，直接添加到collections，不检查kb_type
        if str(kb_id) == 'app_-1':
            collections.append(str(kb_id))
        else:
            kb_type = get_redis_data(f"knowledge_base:{kb_id}", "type")
            if kb_type != 'external':
                collections.append(str(kb_id))
    for metric_base in x.get('metric_base_ids',[]):
        collections.append('metric_'+str(metric_base))
    for collection_name in collections:
        collection=get_collection(collection_name)
        if collection:
            vectors=collection['config']['params']['vectors']
            vector_configs.update(vectors)
            if collection['config']['params'].get('sparse_vectors'):
                sparse_vectors=collection['config']['params']['sparse_vectors']
                vector_configs.update(sparse_vectors)
        else:
            raise ApplicationError(f'collection {collection_name} not found.')

    embedding_runnable={k:v for k,v in embedding_runnable.items() if k in vector_configs}
    if x.get('negative_query'):
        negative_embedding={'query':lambda x:x.get('negative_query')}|RunnableParallel(embedding_runnable)
        embedding_runnable['negative_embedding']=negative_embedding

    if embedding_runnable:
        return RunnablePassthrough.assign(query=query)|RunnablePassthrough.assign(**embedding_runnable)
    else:
        return RunnablePassthrough.assign(query=query)

@chain_decorator
def make_remote_retriever_input(x):
    query=chain_decorator(lambda x:x['question'])
    return RunnablePassthrough.assign(query=query)

@chain_decorator
def get_retriever_settings(x):
    retriever_settings=x.get('retriever_settings',{})
    if isinstance(retriever_settings, str):
        retriever_settings = json.loads(retriever_settings)
    if not isinstance(retriever_settings, dict):
        retriever_settings = {}
    kb_ids = [str(kb_id) for kb_id in x.get("kb_ids") or []]
    for setting in [setting for setting in retriever_settings if setting not in kb_ids]:
        retriever_settings.pop(setting)
    for kb_id in kb_ids:
        kb_id = str(kb_id)
        # load kb retrieve setting from redis or default(yaml config)
        if kb_id not in  retriever_settings:
            embedding_model = get_redis_data(f"knowledge_base:{kb_id}", 'embedding_model')
            recall_topk = get_redis_data(f"knowledge_base:{kb_id}", 'recall_topk')
            # 特殊处理 app_-1：获取 recall_threshold 而不是 recall_threshold_score
            if kb_id == 'app_-1':
                recall_threshold_score = get_redis_data(f"knowledge_base:{kb_id}", 'recall_threshold')
            else:
                recall_threshold_score = get_redis_data(f"knowledge_base:{kb_id}", 'recall_threshold_score')
            retriever_settings[kb_id] = {
                "embedding_model": embedding_model if embedding_model else {"embedding_id": "internal_embedding",
                                                                            "embedding_name": "Fabarta_Text_Embedding_Model"},
                "recall_topk": recall_topk if recall_topk and embedding_model and embedding_model.get('embedding_id')!='internal_embedding' else retriever_mappings['retriever']['search_kwargs']['k'],
                "recall_threshold_score": recall_threshold_score if recall_threshold_score and embedding_model and embedding_model.get('embedding_id')!='internal_embedding' else retriever_mappings['retriever']['search_kwargs']['score_threshold']}
        # check kb retrieve setting, if null, load setting from redis or default(yaml config)
        else:
            if not retriever_settings[kb_id].get('embedding_model'):
                embedding_model = get_redis_data(f"knowledge_base:{kb_id}", 'embedding_model')
                retriever_settings[kb_id]['embedding_model']=embedding_model if embedding_model else {"embedding_id": "internal_embedding",
                                                                            "embedding_name": "Fabarta_Text_Embedding_Model"}
            if not retriever_settings[kb_id].get('recall_topk'):   
                recall_topk = get_redis_data(f"knowledge_base:{kb_id}", 'recall_topk')
                retriever_settings[kb_id]['embedding_model']=recall_topk if recall_topk and embedding_model and embedding_model.get('embedding_id')!='internal_embedding' else retriever_mappings['retriever']['search_kwargs']['k']
            if not retriever_settings[kb_id].get('recall_threshold_score'):   
                # 特殊处理 app_-1：获取 recall_threshold 而不是 recall_threshold_score
                if kb_id == 'app_-1':
                    recall_threshold_score = get_redis_data(f"knowledge_base:{kb_id}", 'recall_threshold')
                else:
                    recall_threshold_score = get_redis_data(f"knowledge_base:{kb_id}", 'recall_threshold_score')
                retriever_settings[kb_id]['recall_threshold_score']=recall_threshold_score if recall_threshold_score and embedding_model and embedding_model.get('embedding_id')!='internal_embedding' else retriever_mappings['retriever']['search_kwargs']['score_threshold']

    retriever_settings["API_summary_collection"] = {
        "embedding_model": {"embedding_id": "internal_embedding", "embedding_name": "Fabarta_Text_Embedding_Model"},
        "recall_topk": retriever_mappings['tool_retriever']['top_k'],
        "recall_threshold_score": retriever_mappings['tool_retriever']['threshold']}
    retriever_settings["metric"] = {
        "embedding_model": {"embedding_id": "internal_embedding", "embedding_name": "Fabarta_Text_Embedding_Model"},
        "recall_topk":  retriever_mappings['metric_base']['top_k'],
        "recall_threshold_score": retriever_mappings['metric_base']['threshold']}
    
    sub_queries = x.get('web_search_sub_queries')
    if sub_queries:
        for idx, query in enumerate(sub_queries):
            retriever_settings[f'search_tool_retriever_{idx}'] = {
                "recall_topk":  retriever_mappings['web_search']['top_k'],
                "recall_threshold_score": retriever_mappings['web_search']['threshold']
            }
    else:
        retriever_settings["search_tool_retriever"] = {
            "recall_topk":  retriever_mappings['web_search']['top_k'],
            "recall_threshold_score": retriever_mappings['web_search']['threshold']}

    logger.info(f"get kbs info:{retriever_settings}")
    x['retriever_settings']=retriever_settings
    return x

def check_retrivals(x):
    if len(x)==0:
        return False
    return True


# retrieve without filter
single_kb_retrieve_chain_without_filter=RunnablePassthrough.assign(filter=lambda x:{'must':[]},custom_tags=lambda x:None, retriever_doc_kvs=lambda x:{})|retrievers['vs_retriever']
single_kb_retrieve_chain_without_filter.name='single_kb_retrieve_chain_without_filter'
# retrieve with filter
single_kb_retrieve_chain_with_filter=retrievers['vs_retriever'] 
single_kb_retrieve_chain_with_filter.name='single_kb_retrieve_chain_with_filter'
single_kb_retrieve_chain = RunnableSequence(
    RunnableParallel({
        'priority_retrieve':single_kb_retrieve_chain_with_filter,
        'unpriority_retrieve':single_kb_retrieve_chain_without_filter,}),
    RunnableBranch(
        (lambda x:check_retrivals(x['priority_retrieve']),lambda x:x['priority_retrieve']),
        lambda x:x['unpriority_retrieve']
    ),
    name='single_kb_retrieve_chain'
)
single_kb_retrieve_chain = single_kb_retrieve_chain.with_types(input_type=RetrieverChainInputModel, output_type=RetrieverChainOutputModel)
single_kb_retrieve_chain.name='single_kb_retrieve_chain'
search_tool_retriever = retrievers['search_tool_retriever']
search_tool_retriever.name='search_tool_retriever'
@chain_decorator
def tool_retrieve(x):
    tool_ids = x["tool_ids"]
    api_ids = tool_ids["api_ids"]
    filter_condition = {'must': [
        {"key": "metadata.tool_id", "match": {"any": api_ids}},
        {"key": "metadata.tool_type", "match": {"value": "api"}}]}
    api_kb_retrieve_chain_with_id_filter = RunnablePassthrough.assign(filter=lambda x: filter_condition, custom_tags=lambda x: None) |\
                                           retrievers['vs_retriever']
    api_kb_retrieve_chain_with_id_filter.name = 'api_kb_retrieve_chain_with_id_filter'
    return api_kb_retrieve_chain_with_id_filter

@chain_decorator
def metric_retrieve(x):
    filter_condition = {}
    chain = RunnablePassthrough.assign(filter=lambda x: filter_condition, custom_tags=lambda x: None) |\
            retrievers['vs_retriever']   
    branches={'passthrough':RunnablePassthrough()}
    if x.get('metric_base_ids'):
        for mb_id in x.get('metric_base_ids'):
            if x.get('intent','query')=='query':
                x['retriever_settings'][f"metric_{mb_id}"]=x['retriever_settings']['metric']
                branches[f"metric_{mb_id}"]=RunnablePassthrough.assign(kb_id=RunnableValue(value=f"metric_{mb_id}")) | chain
            elif x.get('intent')=='definition':
                x['retriever_settings'][f"metric_{mb_id}_definition"]=x['retriever_settings']['metric']
                branches[f"metric_{mb_id}_definition"]=RunnablePassthrough.assign(kb_id=RunnableValue(value=f"metric_{mb_id}_definition")) | chain
            else:
                x['retriever_settings'][f"metric_{mb_id}"]=x['retriever_settings']['metric']
                branches[f"metric_{mb_id}"]=RunnablePassthrough.assign(kb_id=RunnableValue(value=f"metric_{mb_id}")) | chain
            
        chain=RunnableParallel(branches)
        chain.name='metric_retrieve_chain'
        return chain
    else:
        raise DBInfoError('no valid metric base')


model_output_runnable = {
    'response_variables': charge,
    'model_output': prompt_template | models['output_llm']
}

@chain_decorator
def web_search_segmentation(x, config):
    if x.get('segmentation_web_search') != 'on':
        return None
    
    # 如果不进行网络搜索则不进行问题拆分
    search_tools = config.get('input', {}).get('search_tools') or x.get('search_tools')
    if not search_tools:
        return None

    parse_str_to_list = lambda x: (
        json.loads(x) if x and isinstance(x, str) else []
        if x else []
    ) if x else []
    
    return RunnablePassthrough.assign(
        template_name=RunnableLambda(lambda x: 'segmentation_web_search_template'),
        response_type=RunnableLambda(lambda x: ['DOC'])
    ) | prompt_template | models['output_llm'] | RunnableLambda(lambda x: parse_str_to_list(x.content))

@chain_decorator
def multi_retrieve(x, config):
    branches={'passthrough':RunnablePassthrough()}
    # if klg_app has no kb record in redis, multi_retrieve will return None
    for kb_id in x.get('kb_ids',[]):  
        # 检查kb_type，如果是external则使用external_retriever
        # 特殊处理 app_-1：不走Redis查询，直接使用默认逻辑（非external）
        if str(kb_id) == 'app_-1':
            kb_type = 'app_-1'
        else:
            kb_type = get_redis_data(f"knowledge_base:{kb_id}", "type")
        if kb_type == 'external':
            branches[kb_id]=RunnablePassthrough.assign(kb_id=RunnableValue(value=kb_id))|retrievers['external_retriever']
        else:
            branches[kb_id]=RunnablePassthrough.assign(kb_id=RunnableValue(value=kb_id))|single_kb_retrieve_chain
        branches[kb_id].name=f"kb_id:{kb_id}"
    if x.get('tool_ids') and x.get('tool_ids').get('api_ids') and collection_exists('API_summary_collection'):
        branches["API_summary_collection"] = RunnablePassthrough.assign(kb_id=RunnableValue(value="API_summary_collection")) | tool_retrieve
    if x.get('search_tools'):
        sub_queries = x.get('web_search_sub_queries')
        if sub_queries:
            for idx, query in enumerate(sub_queries):
                branches[f'search_tool_retriever_{idx}'] = RunnablePassthrough.assign(
                    query=RunnableValue(value=query)
                ) | search_tool_retriever
        else:
            branches["search_tool_retriever"] = search_tool_retriever
    
    chain=RunnableParallel(branches)
    chain.name='multi_retrieve_parallel'
    return chain 

@chain_decorator
def recommend_retrieve(x):
    filter_condition = {}
    _chain = RunnablePassthrough.assign(filter=lambda x: filter_condition, custom_tags=lambda x: None) | retrievers['vs_recommender']
            
    branches={'passthrough':RunnablePassthrough.assign(retrieve_threshold=lambda x:0)}
    if x.get('metric_base_ids'):
        for mb_id in x.get('metric_base_ids'):
            if x.get('intent','query')=='query':
                x['retriever_settings'][f"metric_{mb_id}"]=x['retriever_settings']['metric']
                branches[f"metric_{mb_id}"]=RunnablePassthrough.assign(kb_id=RunnableValue(value=f"metric_{mb_id}")) | _chain
            elif x.get('intent')=='definition':
                x['retriever_settings'][f"metric_{mb_id}_definition"]=x['retriever_settings']['metric']
                branches[f"metric_{mb_id}_definition"]=RunnablePassthrough.assign(kb_id=RunnableValue(value=f"metric_{mb_id}_definition")) | _chain
            else:
                x['retriever_settings'][f"metric_{mb_id}"]=x['retriever_settings']['metric']
                branches[f"metric_{mb_id}"]=RunnablePassthrough.assign(kb_id=RunnableValue(value=f"metric_{mb_id}")) | _chain

    # if klg_app has no kb record in redis, multi_retrieve will return None
    for kb_id in x.get('kb_ids',[]):  
        branches[kb_id]=RunnablePassthrough.assign(kb_id=RunnableValue(value=kb_id))|_chain
        branches[kb_id].name=f"kb_id:{kb_id}"

    chain=RunnableParallel(branches)
    chain.name='recommend_retrieve_chain'
    return chain 

@chain_decorator
def merge(inputs,config):
    if inputs is None:
        return []
    passthrough=inputs.pop('passthrough')
    question=passthrough.get('question')
    queries=passthrough.get('queries')
    top_k = int(passthrough.get('retrieve_top_k'))
    threshold = passthrough.get('retrieve_threshold')
    retriever_settings=passthrough.get('retriever_settings')
    weights = {
        k: float(v.get('weight', '1.0')) 
        for k, v in retriever_settings.items()
    }

    reranker=list(rerank_embeddings.values())[0]
    df = pd.DataFrame([dict(kb_id=key,**score_node.metadata) for key in inputs for score_node in inputs[key]]) 
    df['page_content']=[score_node.page_content if not score_node.metadata.get('page_content') else score_node.metadata.get('page_content') for key in inputs for score_node in inputs[key]]
    df.fillna('',inplace=True)
    df['hash_tags']=df.apply(lambda row:''.join(sorted([str(e) for tag in row.get('tags',[]) for e in tag])) , axis=1)
    # check recall with answer_priority
    priority_types=[] 
    if x:=config['configurable'].get('answer_priority'):
        option=config_map['answer_priority'].fields['value'].options[x]
        for filter_condition in retriever_mappings[option].get('kwargs',{}).get('must',{}).get('value',[]):
            for data_type in filter_condition.get('match',{}).get('any',[]):
                priority_types.append(data_type)
    logger.info(f"merge result: {len(df)}")
    if len(df):
        df['priority']=0
        if priority_types:
            df.loc[df['data_type'].isin(priority_types), 'priority'] = 1  
    if not len(df):
        return []

    df['show_content']=df.apply(lambda row: row.get('show_content') or row.get('doc_content') or row.get('answer') or row.get('page_content'), axis=1) 

    import uuid;
    if 'groupby_id' not in df.columns:
        df['groupby_id'] = [uuid.uuid4().hex for _ in range(len(df))]
    
    if 'doc_file_id' in df:
        df['groupby_id']=df['groupby_id']+'_'+df['doc_file_id']
    if df['groupby_id'].unique().size==1 and 'metric_id' in df:
        df['groupby_id']=df['metric_id']
    df = df.sort_values(by = ['priority','score'], ascending=False)
    agg_dict={col:'first' for col in df.columns}
    # groupby will rerank df with alphabet order, so need rerank again
    df=df.groupby(['groupby_id','hash_tags']).agg(agg_dict)
    # rerank again
    df = df.sort_values(by = ['priority','score'], ascending=False)
    trace=get_langfuse_trace(config)
    if trace:
        span=trace.span(name='reranker')
    df = df.drop_duplicates(subset='show_content', keep='first')
    rerank_results=[]
    for batch in range(0,len(df),reranker.rerank_input_point_num):
        df_batch=df.iloc[batch:batch+reranker.rerank_input_point_num]
        if queries:
            _rerank_results=reranker.compute_score(queries,[df_batch['show_content'].tolist() for m in queries])
        else:
            _rerank_results=reranker.compute_score([question],[df_batch['show_content'].tolist()])
        for i in range(len(df_batch)):
            _rerank_results[0][i]['score']=max([sigmoid(_m[i]['score']) for _m in _rerank_results])
        rerank_results.extend(_rerank_results[0])

    if trace:
        span.end()
    

    df['score']=[result['score'] for result in rerank_results]
    
    df['weight']=[weights[kb_id] for kb_id in df['kb_id']]
    df['score']=df['score']*df['weight']
    df['score'] = df['score'].clip(upper=1.0)

    # Use threshold filtering set by the application
    df = df[df['score'] >= threshold]
    if not len(df):
        return []

    if int(config['configurable'].get('retrieve_mode', 0)) != 1:
        result_df = pd.DataFrame()
        # iterater retriever_settings
        for kb_id, setting in retriever_settings.items():
            # get each kb_id data, keep head of recall_topk
            topk_df = df[df['kb_id'] == kb_id].head(setting.get('recall_topk', 5))
            result_df = pd.concat([result_df, topk_df])
        df=result_df

    df = df.sort_values(by = ['priority','score'], ascending=False)
    df.drop('hash_tags', axis=1, inplace=True)

    result = []
    for hit in df.to_dict('records'):
        metadataStr = ""
        
        if "properties" in hit and hit['properties']:
            for k in hit['properties']:
                metadataStr += f" {k}:{hit['properties'][k]} "
            metadataStr = "[" + metadataStr + "] "
            hit['show_content'] = metadataStr + hit['show_content']
        chunk=Document(page_content=hit['show_content'], metadata=hit)
        
        #logger.debug(f"img score: {chunk.metadata['score']}")
        # if chunk.metadata.get('image_url') and chunk.metadata['score'] < retriever_mappings['image']['threshold']:
        #     chunk.metadata['image_url']=[]

        result.append(chunk)

    return result[:top_k]

def web_fetch(docs,config):

    @chain_decorator
    def concat(x):
        return x['web_docs']+x['docs']

    urls=[]
    for doc in docs:
        if doc.metadata.get('data_type')=='web_search':
            urls.append(doc.metadata['url'])
    if urls:
        crawler_name=config['configurable'].get('crawler_name','AsyncChromiumLoader')
        loader=loader_splitter_chain.with_config({'configurable':{'loader_name':crawler_name}})
        
        return {'web_docs':{'urls':RunnableValue(values=urls),'data_type':RunnableValue(value='web_search')}|loader,'docs':lambda x,v=docs:v}|concat
    else:
        return docs

multi_kbs_retrieve_chain = RunnablePassthrough.assign(retrieve_top_k=config_map['retrieve_top_k'],
                                                      retrieve_threshold=config_map['retrieve_threshold'],
                                                      retriever_settings=config_map['retriever_settings'],
                                                      web_search_sub_queries=web_search_segmentation
                                                      )|\
                            get_retriever_settings|\
                            make_retriever_input|multi_retrieve|\
                            merge
multi_kbs_retrieve_chain=multi_kbs_retrieve_chain.with_types(input_type=MultiRetrieverChainInputModel, output_type=List[Document])

metric_retrieve_chain = (RunnablePassthrough.assign(retrieve_top_k=config_map['retrieve_top_k'],
                                                    retrieve_threshold=config_map['retrieve_threshold'],
                                                    retriever_settings=config_map['retriever_settings'])
                        | get_retriever_settings | make_retriever_input | metric_retrieve | merge)


remote_retrieve_chain = (RunnablePassthrough.assign(retrieve_top_k=config_map['retrieve_top_k'],
                                                    retrieve_threshold=config_map['retrieve_threshold'],
                                                    retriever_settings=config_map['retriever_settings'])
                         | get_retriever_settings | make_remote_retriever_input | remote_agent_retriever | merge)
remote_retrieve_chain=remote_retrieve_chain.with_types(input_type=RemoteRetrieverChainInputModel, output_type=List[Document])

multi_src_retrieve_chain=get_retriever_settings|multi_src_retriever

recommend_chain = get_retriever_settings | make_retriever_input | recommend_retrieve|merge
