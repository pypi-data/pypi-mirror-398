from pydantic import BaseModel,fields
from typing import List,Literal,Optional,Union
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBinding,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnableGenerator,
    RunnablePick,
    chain as chain_decorator,
)
from framebase import model_configs,prompt_configs,config_map as additional_configs
from framebase.models import models
from framebase.values import RunnableValue
from framebase.prompts import chain as prompt
from framebase.output_parsers import charge
from framebase.embeddings import rerank_embeddings
from utils.dbs import set_thought, getall_redis_data, scroll_arcvector
from utils.logger import logger
from framebase import thought_wait_time
from datetime import datetime,timedelta
import jieba,urllib,re
from rank_bm25 import BM25Okapi
from collections import defaultdict
from utils.exceptions import DBInfoError,MetricQueryError,dimensionValueError,NoPermissionError,ClarifyInteruptError,APICallError,MetricDateQueryError,APICallTimeOutError
from app.admin_operation import get_global_config_info
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.text2sql import sql_json_2_md
from langchain.schema.messages import BaseMessage
import pkg_resources,json,asyncio,traceback
import pandas as pd
from langchain_core.output_parsers import JsonOutputParser
from utils.connections import r, redis_cluster, r_slaver
from itertools import groupby
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed

from chains.analytic_metric_chain import metric_time_recognizer, metric_dimension_recognizer, time_convert
from chains.text2metric.core.infrastructure import bm25_rerank, metric_service
from chains.text2metric.service.time import get_metric_time_records, strptime, time2str
from chains.text2metric.service.dimension import dimension_intent
from configs import get_configs
from decimal import Decimal, ROUND_HALF_UP

def normalize_scores_to_range(scores, min_val=-1.0, max_val=1.0):
    """
    将分数归一化到指定范围 [min_val, max_val]
    """
    if not scores:
        return scores

    score_values = [item['score'] for item in scores]
    
    if not score_values:
        return scores

    min_score = min(score_values)
    max_score = max(score_values)

    if min_score == max_score:
        mid_val = (min_val + max_val) / 2
        for item in scores:
            item['normalized_score'] = mid_val
        return scores

    for item in scores:
        normalized = (item['score'] - min_score) / (max_score - min_score)
        item['normalized_score'] = min_val + normalized * (max_val - min_val)
    
    return scores

def normalize_scores_to_range(scores, min_val=-1.0, max_val=1.0):
    """
    将分数归一化到指定范围 [min_val, max_val]
    """
    if not scores:
        return scores

    score_values = [item['score'] for item in scores]
    
    if not score_values:
        return scores

    min_score = min(score_values)
    max_score = max(score_values)

    if min_score == max_score:
        mid_val = (min_val + max_val) / 2
        for item in scores:
            item['normalized_score'] = mid_val
        return scores

    for item in scores:
        normalized = (item['score'] - min_score) / (max_score - min_score)
        item['normalized_score'] = min_val + normalized * (max_val - min_val)
    
    return scores

class ConversationHistory(BaseModel): #Same as EKC
    content: str
    role: str
    thoughts: Optional[List[str]]

class MetricTemplateAnalysisSubRequest(BaseModel):
    template_ids:List[str]
    dimension_filters:List[dict]
    start_date: str
    end_date: str
    time_filters: List[str]
    
class MetricTemplateAnalysisInput(BaseModel):
    question: str
    history: List[ConversationHistory]
    kb_ids:Optional[List[str]]
    metric_base_ids:Optional[List[str]]
    metric_template_base_ids:Optional[List[str]]
    sub_request: Optional[MetricTemplateAnalysisSubRequest]

class MetricTemplateRecommendQuestionInput(BaseModel):
    question: str
    history: List[ConversationHistory]
    metric_template_base_ids:Optional[List[str]]

class MetricCandidate(BaseModel):
    analysisTemplateId: str
    question: str

class MetricTemplateRecommendQuestionOutput(BaseModel):
    candidates:List[MetricCandidate]





metric_type={'原子指标':0,'派生指标':1,'复合指标':2}
# date_mapping={'月':'MONTH','年':'YEAR','日':'DAY','季度':'QUARTER','MONTH':'MONTH','YEAR':'YEAR','DAY':'DAY','QUARTER':'QUARTER'}
# date_mapping_reverse={'MONTH':'月','YEAR':'年','DAY':'日','QUARTER':'季度','月':'月','年':'年','日':'日','季度':'季度'}
time_level={'DAY':1,"MONTH":2,"QUARTER":3,"YEAR":4}

metric_messages=get_configs('service').get("metric_messages")
Metric_General_Error_Message=metric_messages.get("Metric_General_Error_Message")
Metric_Permission_Denied_Message=metric_messages.get("Metric_Permission_Denied_Message")
Metric_Dimension_Permission_Denied_Message=metric_messages.get("Metric_Dimension_Permission_Denied_Message")
Metric_Not_Found_Message=metric_messages.get("Metric_Not_Found_Message")
Metric_Low_Relevance_Message=metric_messages.get("Metric_Low_Relevance_Message")
Metric_No_Dimension_Message=metric_messages.get("Metric_No_Dimension_Message")
Metric_Service_Error_Message=metric_messages.get("Metric_Service_Error_Message")
Metric_Null_Result_Message=metric_messages.get("Metric_Null_Result_Message")
Metric_Analysis_Error_Message=metric_messages.get("Metric_Analysis_Error_Message")


magnitude_dict = {  
    "HUNDRED_MILLION": 100000000,
    "MILLION": 1000000,
    "TEN_THOUSAND": 10000, 
    "THOUSAND": 1000, 
    "HUNDRED": 100,  
    "TEN": 10,  
    "ONE": 1,  
}  

magnitude_mappings = {
    "HUNDRED_MILLION": '亿', 
    "TEN_THOUSAND": '万', 
}

async def hold_stream(x):
    return x

def scan_redis_values(pattern, count=1000):
    cursor = 0
    all_templates = []  # 直接存储值的列表
    while True:
        cursor, batch = r.scan(cursor, match=pattern, count=count)
        for key in batch:
            key_str = key.decode("utf-8")
            # 获取该键的所有hash数据
            if redis_cluster:
                redis_data = r_slaver.hgetall(key_str)
            else:
                redis_data = r.hgetall(key_str)
            if redis_data:
                # 处理每个字段和值
                template_data = {}
                for field, value in redis_data.items():
                    try:
                        field_str = field.decode('utf-8')
                        value_str = value.decode('utf-8')
                        template_data[field_str] = json.loads(value_str)
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        # 如果解析失败，记录日志并保持原值
                        logger.warning(f"Failed to parse JSON for field {field} in key {key_str}: {e}")
                        try:
                            field_str = field.decode('utf-8')
                            value_str = value.decode('utf-8')
                            template_data[field_str] = value_str
                        except UnicodeDecodeError:
                            # 如果解码也失败，跳过这个字段
                            continue
                if template_data:
                    all_templates.append(template_data)
        if cursor == 0:
            break
    return all_templates

def scan_kb_ids(pattern="business_analysis_templates:*", count=1000):
    cursor = 0
    kb_ids = set()
    while True:
        cursor, batch = r.scan(cursor, match=pattern, count=count)
        for key in batch:
            key_str = key.decode("utf-8")
            parts = key_str.split(":")
            if len(parts) >= 2:  # 至少有 business_analysis_templates:kbId
                kb_ids.add(parts[1])
        if cursor == 0:
            break
    return sorted(kb_ids)

async def stream_process(chunks,config):
    session_id=config['input']['session_id']
    async for chunk in chunks:
        if chunk.get('insight'):
            set_thought(session_id,'metric_template_insight',{'chunk':chunk.get('insight')})
        yield chunk
    set_thought(session_id,'metric_template_insight',{'chunk':chunk.get('insight'),'end':True})
    await asyncio.sleep(thought_wait_time)
    logger.info('metric_router: '+str(chunk))
    yield chunk

@chain_decorator
async def model_binding(x, config):
    llm=models[x.get('model_name', 'metric_to_text_llm')]
    return prompt | llm

def metric_template_pick(x):
    all_metrics = x['all_metrics']
    question = x['question']
    template_slim = []
    for template in all_metrics:
        extracted = {
            "description": template.get("description", ""),  # 安全获取，避免 KeyError
            "templateId": template.get("templateId", ""),
            "templateName": template.get("name", ""),
        }
        template_slim.append(extracted)

    with open(pkg_resources.resource_filename('configs',f'chain/metric_pick_tcl.json'),'r',encoding='utf-8')as f:
        schema=json.load(f)
    vars=RunnablePassthrough.assign(template_name=RunnableValue(value='metric_router_template_tcl'),
                                    question=RunnableValue(value=question),
                                    json_schema=lambda x:schema,
                                    all_metrics=RunnableLambda(lambda _: template_slim)) # 指定提示词模板
    chain = vars|model_binding|JsonOutputParser()|RunnableGenerator(stream_process)
    # x["top1_result"] = chain.invoke({})
    # logger.info(x["top1_result"])
    logger.info("metric template pick flow")
    return chain


def get_metric_info(x):
    templateId = x['top1_template']['templateId']
    x['top1_result'] = {}
    all_metrics = x['all_metrics']
    for metric in all_metrics:
        if templateId == int(metric['templateId']):
            x['top1_result'] = metric


    set_thought(x['session_id'],'metric_template_template',{'top1_result': x['top1_template_id']})
    template_metrics = []
    logger.info(f"get_top1_result: {x.get('top1_result')}")
    if x.get('top1_result'):
        metric_base_id = x.get("top1_result").get("metricBaseId")
        logger.info(f"metric_base_id: {metric_base_id}")
        x['chartConfigs'] = x.get('top1_result').get('chartConfigs')

        for metric_group in x['chartConfigs']:
            for metric in metric_group["metrics"]:
                template_metrics.append({
                    'name': metric['name'],
                    'id': metric['id']
                })
    raw_metric_info=[]
    template_metric_ids=[metric['id'] for metric in template_metrics]
    logger.info(f"history_metric_ids (template_metric_ids): {template_metric_ids}")
   
    metrics=scroll_arcvector(f'metric_{metric_base_id}',{"must": [{"key": "metadata.metric_id","match": {"any": template_metric_ids}}]})
    raw_metric_info.extend(metrics)

    # logger.info(f"raw_metric_info: {raw_metric_info}")
    metric_infos=[]
    x['raw_metric_info']=raw_metric_info

    for item in raw_metric_info:
        metric_info = {}
        metadata = item.metadata
        metric_info['name']=metadata.get('page_content')
        metric_info['alias']=metadata.get('alias')
        metric_info['metric_code']=metadata.get('groupby_id')
        metric_info['metricId']=metadata['metric_id']
        metric_info['unit']=metadata['unit']
        metric_info['type']=metadata['type']
        metric_info['time_interval']= metadata['time_interval']
        metric_info['is_accumulative']= metadata['is_accumulative']
        associated_dimension = metadata.get('associated_dimension', []) or []
        valid_associated_dimension=list(filter(lambda x:x['name'] and any(x['values']),associated_dimension))
        metric_info["associated_dimension"]=valid_associated_dimension
        metric_info['definition']=metadata['definition']
        metric_info['description']=metadata['description']
        metric_infos.append(metric_info)
    x['metric_infos']=metric_infos
  
    return x

@chain_decorator
def metric_template_rerank(x):
    # 检索模板
    # x['question'] 和redis中所有模板的name+description做bm25+reranker，匹配1
    # x['question'] 和redis中所有模板的sample question做bm25+reranker，匹配2
    # 这两路结果对相同的模板merge、分数合并，取top15
    # LLM filter template top 1

    templates = []

    for kbid in x['metric_template_base_ids']:
        kb_templates = scan_redis_values(pattern=f"business_analysis_templates:{kbid}:*")
        for template in kb_templates:
            templates.append(template)
    query = x['question']
    # 路径1：name+description 匹配
    # bm25 匹配 name+description
    name_desc_corpus = []
    for template in templates:
        name_desc_text = template['name'] + ' ' + template['description']
        name_desc_corpus.append(name_desc_text)
    name_desc_bm25_results = bm25_rerank(query, name_desc_corpus, 15)
    
    # 路径2：sampleQuestions 匹配
    # bm25 匹配 sampleQuestions
    sample_questions_corpus = []
    for template in templates:
        sample_questions_text = ' '.join(template['sampleQuestions'])
        sample_questions_corpus.append(sample_questions_text)
    sample_questions_bm25_results = bm25_rerank(query, sample_questions_corpus, 15)
    
    # reranker 对两路结果进行评分
    reranker = list(rerank_embeddings.values())[0]
    name_desc_reranker_scores = reranker.compute_score([query], [name_desc_bm25_results])
    sample_questions_reranker_scores = reranker.compute_score([query], [sample_questions_bm25_results])
    
    # 合并分数，按模板ID聚合
    template_scores = defaultdict(float)
    # template_dict = {i: template for i, template in enumerate(templates)}
    
    # 处理 name+description 路径的分数
    if name_desc_reranker_scores and name_desc_reranker_scores[0]:
        # 对name_desc分数进行归一化处理
        normalized_name_desc_scores = normalize_scores_to_range(name_desc_reranker_scores[0])
        for score_item in normalized_name_desc_scores:
            text = score_item['data']
            normalized_score = score_item['normalized_score']
            # 根据文本找到对应的模板索引
            for i, corpus_text in enumerate(name_desc_corpus):
                if corpus_text == text:
                    template_scores[i] += normalized_score * 0.1
                    break
    
    # 处理 sampleQuestions 路径的分数  
    if sample_questions_reranker_scores and sample_questions_reranker_scores[0]:
        # 对sample_questions分数进行归一化处理
        normalized_sample_questions_scores = normalize_scores_to_range(sample_questions_reranker_scores[0])
        for score_item in normalized_sample_questions_scores:
            text = score_item['data']
            normalized_score = score_item['normalized_score']
            # 根据文本找到对应的模板索引
            for i, corpus_text in enumerate(sample_questions_corpus):
                if corpus_text == text:
                    template_scores[i] += normalized_score * 0.9
                    break
    
    for i, template in enumerate(templates):
        template['rerank_score'] = template_scores.get(i, 0.0)

    top15_templates = sorted(templates, key=lambda x: x['rerank_score'], reverse=True)[:15]
    x['all_metrics'] = top15_templates
    
    logger.info(f"Question: {query}")
    logger.info("Template matching results:")
    logger.info(f"Total templates with scores: {len([t for t in templates if t['rerank_score'] > 0])}")
    for i, template in enumerate(top15_templates):
        logger.info(f"Rank {i+1}: {template['name']} (ID: {template['templateId']}) - Score: {template['rerank_score']:.4f}")

    # 识别用户问题中的时间，维度
    time_info = x.get('time_info', {})
    dimension_info = x.get('dimension_info', {})
    
    logger.info(f"识别到的时间信息: {time_info}")
    logger.info(f"识别到的维度信息: {dimension_info}")
    return x

recognition_assignment = RunnablePassthrough.assign(
    time_info=RunnableLambda(lambda x: {'question': x['question']}) | metric_time_recognizer,
    dimension_info=RunnableLambda(lambda x: {'question': x['question']}) | metric_dimension_recognizer
)


def call_template_metric_query(metric_query,cookie=None):
    try:
        result=metric_service.template_metric_query(metric_query,cookie)
        if str(result['code'])!='200':
            raise MetricQueryError(f"Metric query failed: {result}")
        return metric_query,result
    except NoPermissionError as e:
        raise e
    except Exception as e:
        raise MetricQueryError(f"Metric query failed: {e}")

async def metric_query_description_process(chunks, config):
    session_id = config['input']['session_id']
    id = config['metadata']['id']    
    content=''
    async for chunk in chunks:
        if isinstance(chunk,BaseMessage):
            if chunk.content:
                content += chunk.content
        else:
            if chunk and type(chunk)==str:
                content+=chunk
            
        set_thought(session_id, f"metric_template_text_{id}", {'chunk': content})
        yield chunk
    set_thought(session_id, f"metric_template_text_{id}", {'chunk': content, 'end': True})



def half_round(num, decimal):
    if decimal==-1:
        return num
    str_deci = 1
    for _ in range(decimal):
        str_deci = str_deci / 10
    str_deci = str(str_deci)
    result = Decimal(f'.{num}').quantize(Decimal(str_deci), rounding=ROUND_HALF_UP)
    return str(result).split('.')[-1]

def data_format(formater,data_array):
    if formater.get('needConversion',True):  
        reals = []
        for value in data_array:
            # check if value is not None and value is not NaN
            if value is not None and value==value:
                if type(value)!=str:
                    value=str(value)
                reals.append(float(value)*magnitude_dict[formater['originalMagnitude']])
            else:
                reals.append(value)
        if not reals:
            if type(data_array)==list:
                return data_array
            return data_array.tolist()
        _reals=[value for value in reals if value is not None and value == value]
        min_value=min(_reals) if _reals else None 
        if formater['targetMagnitude']=='AUTO_ADAPT':
            if min_value is None:
                target_magnitude="ONE"
            else:
                for magnitude, value in magnitude_dict.items():
                    if abs(min_value)>=value:
                        target_magnitude=magnitude
                        break
                else:
                    target_magnitude="ONE"
        else:
            target_magnitude=formater['targetMagnitude']
        data_array = reals
    else:
        target_magnitude=formater['targetMagnitude']
    return list(map(lambda x:_format(x,formater,target_magnitude),data_array))

def _format(value:str, formater, target_magnitude):
    if not value or value!=value:
        return None
    value=str(value)
    if not formater.get('needConversion',True):
        if formater['unit']:
            return value+formater['unit']
        else:
            return value
    if target_magnitude in magnitude_mappings:
        value = float(value)/magnitude_dict[target_magnitude]
    else:
        found_magnitude=None
        for mag in magnitude_mappings:
            if magnitude_dict[mag] <= magnitude_dict[target_magnitude]:
                found_magnitude = mag
                break
        
        if found_magnitude:
            value = float(value) / magnitude_dict[found_magnitude]
            target_magnitude = found_magnitude 
        else:
            value = float(value)
    parts=str(value).split('.')
    if len(parts)==1:
        decimal=''
        integer=parts[0]
    else:
        decimal=parts[1]
        integer=parts[0]
    if formater['thousandthsPlace']:
        integer=f'{int(integer):,}'
    decimal=half_round(decimal,1)
    if target_magnitude in magnitude_mappings:
        return integer+'.'+decimal+magnitude_mappings[target_magnitude]
    else:
        return integer+'.'+decimal

@chain_decorator
async def call_template_metric_query_service(x,config):
    branches={}
    if x['metric_query']:
        metric_querys=x['metric_query']
        set_thought(x['session_id'],'metric_queries',{'thought':metric_querys})
        logger.info('metric intents requests:\n'+json.dumps(metric_querys,ensure_ascii=False,indent=4))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_template_metric_query, metric_query, config.get('headers',{}).get('cookie')) for metric_query in metric_querys]

            # 收集结果
            results = [None]*len(metric_querys)
            for future in as_completed(futures):
                try:
                    query,result = future.result()
                    result['data_source_query_info'] = {
                        "question_id": "",
                        "question_content": "",
                        "sql": result.get('data',{}).get('sql', "")
                    }
                    
                    results[int(query['chartOrder'])-1]=(query,result)
                    
                except Exception as exc:
                    logger.error(f"Generated an exception: {exc}\n{traceback.format_exception(exc)}")
                    continue
            
            
            prompt_name='metric_query_answer_template_refine'
            metric_result = {}
            current_idx = 1
            # results = sorted(results, key=lambda x: (x is None, x[0]['chartOrder'] if x and x[0] else 0))
            try:
                for i, (query,result) in enumerate(results):
                    logger.info(f"check_query: {query}")
                    chartOrder=i+1 if not query.get('chartOrder') else query.get('chartOrder')
                    current_idx = i
                    current_idx +=1
                    extracted_data_1 = {
                        'data': result['data']['data'],
                        'headers': result['data']['headers'],
                        'fieldFormatConfigList': result['data']['fieldFormatConfigList'],
                        'analysis_template_id': x['top1_result']['templateId'],
                        'startDate':query['startDate'],
                        'endDate': query['endDate'],
                        'analysis_template_name': x['top1_template']['templateName']
                    }
                    
                    
                    # logger.info(f"extracted_data_1: {extracted_data_1}")
                    df=pd.DataFrame(result['data']['data'],columns=result['data']['headers'],dtype=str)
                    for j,formater in enumerate(result['data'].get('fieldFormatConfigList',[]) or []):  
                        df[df.columns[j]]=data_format(formater,df[df.columns[j]])
                    

                    result['data']['data']=df.values.tolist()

                    set_thought(x['session_id'], f"metric_template_metric_{chartOrder}",extracted_data_1)

                    set_thought(x['session_id'], f"sql_{chartOrder}",result['data'].get('sql',''))
                    set_thought(x['session_id'], f"metric_data_{chartOrder}",df.to_dict('records'))
                    if x.get('disable_description'):
                        return RunnablePassthrough()
                    metric_result[str(chartOrder)] = sql_json_2_md(result['data'])
            except Exception as e:
                logger.warning("get error")
                logger.info(f"error message: {e}")
                # metric_result[str(chartOrder)] = ""

                extracted_data_1 = {
                        'data': [],
                        'headers': [],
                        'fieldFormatConfigList': [],
                        'analysis_template_id': x['top1_result']['templateId'],
                        'startDate':[],
                        'endDate': []
                    }
                chartOrder = current_idx
                set_thought(x['session_id'], f"metric_template_metric_{chartOrder}",extracted_data_1)
                current_idx+=1
            current_time = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"metric_result keys: {list(metric_result.keys())}")
            chartConfigs = x['top1_result']['chartConfigs']
            if not list(metric_result.keys()):
                for i, chartConfig in enumerate(chartConfigs):
                    chart_order = chartConfig['order']
                    logger.info(f"查询错误: branch {i} for chart_order {chart_order}")
                    set_thought(x['session_id'], f"metric_template_text_{chart_order}", {'chunk': "暂无信息"})
                    branches[f'{i}'] = RunnablePassthrough.assign(placeholder=RunnableValue(value='暂无信息'))
            else:
                for i, chartConfig in enumerate(chartConfigs):
                    chart_order = chartConfig['order']
                    if str(chart_order) in metric_result.keys():
                        metrics_def = ""
                        for metric in chartConfig['metrics']:
                            for metirc_info in x['metric_infos']:
                                if metric['name'] == metirc_info['name']:
                                    metrics_def += "指标名：" + metirc_info['name'] + "，定义：" + metirc_info['description'] + "\n"
                        logger.info(f"成功创建 branch {i} for chart_order {chart_order}")
                        branches[f'{i}'] = \
                        RunnablePassthrough.assign(template_name=RunnableValue(value=prompt_name),
                                                    query_result=RunnableValue(value=metric_result[str(chart_order)]),
                                                    question=lambda x,v=x['question']:v,
                                                    chart_prompt = lambda x,v=chartConfig['prompt']:v,
                                                    metrics_def=RunnableValue(value=metrics_def),
                                                    current_time = RunnableValue(value=current_time)
                        )|\
                        RunnablePassthrough.assign(placeholder=model_binding|RunnableGenerator(metric_query_description_process).with_config(config={'metadata':{'id':chart_order}}))
                    else:
                        logger.warning(f"分析图表配置 {chart_order} 不在 metric_result 中")
            logger.info(f"branches: {branches}")
        logger.info("done")
        return RunnablePassthrough.assign(**branches)

def process_model_results(x):
    model_results = {}
    for key, value in x.items():
        if key.isdigit():
            placeholder_result = value.get('placeholder')
            if placeholder_result:
                try:
                    model_results[f"chart_llm_{key}"] = placeholder_result.content
                except:
                    model_results[f"chart_llm_{key}"] = placeholder_result
    llm_result = ""
    for i, key in enumerate(model_results.keys()):
        llm_result += f"第{i+1}次模型输出的结果：{model_results[key]}\n\n"
    summaryPromptTemplateId = x['top1_result'].get('summaryPromptTemplateId')
    llm=models[x.get('model_name', 'metric_to_text_llm')] 
    logger.info(f"summaryPromptTemplateId: {summaryPromptTemplateId}")
    
    current_time = datetime.now().strftime('%Y-%m-%d')
    if summaryPromptTemplateId:
        summaryPromptTemplate = scan_redis_values(pattern=f"business_analysis_prompt_templates:{summaryPromptTemplateId}")
        dynamic_prompt = summaryPromptTemplate[0].get('promptTemplate')
        # logger.info(f"dynamic_prompt: {dynamic_prompt}")
        _prompts=prompt.with_config({'configurable':{'answer_prompt_chart_summary':dynamic_prompt}})
        vars=RunnablePassthrough.assign(template_name=RunnableValue(value='chart_summary_tcl'),
                                        llm_result=RunnableValue(value=llm_result),
                                        SummaryPrompt=RunnableValue(value=x['top1_result']['summaryPrompt']),
                                        question = RunnableValue(value=x["question"]),
                                        current_time = RunnableValue(value=current_time)
                                        )
        chain = vars|_prompts|llm|RunnableGenerator(summary_stream_process)
    else:
        vars=RunnablePassthrough.assign(template_name=RunnableValue(value='chart_summary_tcl'),
                                        llm_result=RunnableValue(value=llm_result),
                                        SummaryPrompt=RunnableValue(value=x['top1_result']['summaryPrompt']),
                                        question = RunnableValue(value=x["question"]),
                                        current_time = RunnableValue(value=current_time)
                                        # json_schema=lambda x:schema,
                                        )
        chain = vars|prompt|llm|RunnableGenerator(summary_stream_process)

    return chain

async def summary_stream_process(chunks,config):
    session_id=config['input']['session_id']
    accumulated_content = ""
    async for chunk in chunks:
        
        if chunk.content:
            accumulated_content += chunk.content
            set_thought(session_id,'metric_template_summary',{'chunk':accumulated_content})
        yield chunk
    set_thought(session_id,'metric_template_summary',{'chunk':accumulated_content,'end':True})
    await asyncio.sleep(thought_wait_time)
    logger.info('metric_router: '+str(chunk))
    yield chunk

async def make_metric_query(x):
    passthrough=x['passthrough']
    metric_query=[]
    for _, chartConfig in enumerate(passthrough['chartConfigs']):
        metricIdList = [metric['id'] for metric in chartConfig["metrics"]]
        query={
            "metricIdList": metricIdList,
            "metricNameList":[metric['name'] for metric in chartConfig["metrics"]],
            "chartOrder":chartConfig['order'],
            "startDate":x['time_intent']['startDate'][metricIdList[0]],
            "endDate":x['time_intent']['endDate'][metricIdList[0]],
            # "windowDate":"MONTH",
            "windowDate":x['time_intent']['windowDate'][metricIdList[0]],
            "dimensionFilters":x['dimension_intent'][metricIdList[0]].get('dimensionFilters',{}),
            "templateId": passthrough["top1_result"]["templateId"],
            "chartOrder": chartConfig['order']
        }      
        metric_query.append(query)

    logger.info(f"1metric_query: {metric_query}")
    passthrough['metric_query']=metric_query
    return passthrough



def raise_error_DBInfoError(x=None):
    raise DBInfoError('text2metric but no metric')  

metric_query_execute_chain=RunnableBranch(
        (lambda x: x.get('metric_query'), call_template_metric_query_service|{"model_output":lambda x:process_model_results(x),'response_variables':charge}),
        raise_error_DBInfoError
        )

model_conifg={k:v for k,v in model_configs.items() if k in ['output_llm','sql_or_api_analysis_llm','temperature','top_p','max_tokens']}
metric_template_configs={'response_type':lambda x,v=['MetricTemplate']:v,'configurable':model_conifg}
output_process={"model_output":lambda x:"",'response_variables':charge}



@chain_decorator
async def analysis_time_intent(x,config):
    startDate=x['time_recognizer'].get('startDate')
    endDate=x['time_recognizer'].get('endDate')
    time_unit=x['time_recognizer'].get('time_unit')
    output_startDate={}
    output_endDate={}
    windowDate={}
    
    # set time_filters and windowDate
    for metric_info in x['metric_infos']:
        if time_unit=='None':
            windowDate[metric_info['metricId']]=metric_info['time_interval']
        elif time_level[metric_info['time_interval']]>time_level[time_unit]:
            windowDate[metric_info['metricId']]=metric_info['time_interval']
        else:
            windowDate[metric_info['metricId']]=time_unit        
        _latest_date=datetime.now()
        _startDate,_endDate=time_convert(startDate,endDate,_latest_date)
        output_startDate[metric_info['metricId']]=_startDate
        output_endDate[metric_info['metricId']]=_endDate
    
    result={}
    result['startDate']=lambda x,v=output_startDate:v
    result['endDate']=lambda x,v=output_endDate:v
    result['windowDate']=lambda x,v=windowDate:v

    return RunnableParallel(**result)

metric_query_chain= RunnableParallel(
        time_intent=RunnableParallel(time_records=get_metric_time_records|RunnablePick('time_records'),
                                     metric_infos=RunnablePick('metric_infos'),
                                     question=RunnablePick('question'),
                                     time_recognizer=RunnablePick('time_info'))|analysis_time_intent,
                                     
        dimension_intent=dimension_intent,
        passthrough=RunnablePassthrough()
    )|make_metric_query|metric_query_execute_chain

def condition_func(x):
    res = next(
        (item.get('metric_template_analysis_chain', {}).get('top1_template_id')
        for item in x.get('sub_requests', [])
        if 'metric_template_analysis_chain' in item
    ), None)

    return res is not None

def branch_func(x):
    res = next(
        (item.get('metric_template_analysis_chain', {}).get('top1_template_id')
        for item in x.get('sub_requests', [])
        if 'metric_template_analysis_chain' in item
    ), None)
    
    template = scan_redis_values(pattern=f"business_analysis_templates:*:{res}")
    if not template:
            raise ValueError(f"Template {res} not found in Redis")
    return {
        'templateId': res,
        'templateName': template[0]['name']
    }



metric_template_chain=recognition_assignment|metric_template_rerank|RunnablePassthrough.assign(top1_template=RunnableBranch(
            (condition_func, branch_func),
            lambda x: metric_template_pick(x)),
            dimensions=RunnablePick('dimension_info')|\
            RunnablePick('dimensions'))|RunnableLambda(lambda x: {**x, 'top1_template_id': x['top1_template']['templateId']})|\
            get_metric_info|metric_query_chain|output_process

metric_template_analysis_chain=RunnablePassthrough.assign(**metric_template_configs)|metric_template_chain
metric_template_analysis_chain=metric_template_analysis_chain.with_types(input_type=MetricTemplateAnalysisInput)


@chain_decorator
async def fetch_template(x):
    last_summary = ""
    analysisTemplateId = ""
    drillDownTemplates = []
    AllsampleQuestions = []
    if "history" in x.keys():
        for history in x["history"]:
            if history.role == "human":
                human_question = history.content  
            if history.role == "ai":
                for thought_str in history.thoughts:
                    try:
                        thought = json.loads(thought_str)
                        if thought.get("type") == "metric_template_template":
                            analysisTemplateId = thought["thought"].get("top1_result")
                        if thought.get("type") == "metric_template_summary":
                            last_summary += thought["thought"].get("chunk", "")
                    except:
                        logger.error(f"invalid thought_str: {thought_str}")
                        continue
    
    # logger.info(f"analysisTemplateId: {analysisTemplateId}")
    template = scan_redis_values(pattern=f"business_analysis_templates:*:{analysisTemplateId}")
    if template:
        drillDownTemplates = template[0]['drillDownTemplates']
        logger.info(f"get template from analysisTemplateId:{template}")
    
    if drillDownTemplates:
        for template_id in drillDownTemplates:
            extracted_data = {}
            template = scan_redis_values(pattern=f"business_analysis_templates:*:{template_id}")
            if template:
                logger.info(f"get template from drillDownTemplates: {template}")
                extracted_data['analysisTemplateId'] = template[0]['templateId']
                extracted_data['sampleQuestions'] = template[0]['sampleQuestions']
                AllsampleQuestions.append(extracted_data)
        x['human_question'] = human_question
        x['last_summary'] = last_summary
        x['AllsampleQuestions'] = AllsampleQuestions
        x['reconmmend_question_num'] = min(5, len(AllsampleQuestions))
    else:
        x['human_question'] = ""
        x['last_summary'] = ""
        x['AllsampleQuestions'] = []
        x['reconmmend_question_num'] = 0
    return x

@chain_decorator
async def reconmmend_question(x):
    if x['human_question']:
        with open(pkg_resources.resource_filename('configs',f'chain/recommend_question_tcl.json'),'r',encoding='utf-8')as f:
            schema=json.load(f)
        vars=RunnablePassthrough.assign(template_name=RunnableValue(value='metric_recommend_question'),
                                        question=RunnableValue(value=x['human_question']),
                                        last_summary=RunnableValue(value=x['last_summary']),
                                        sampleQuestions=RunnableLambda(lambda _: x['AllsampleQuestions']),
                                        reconmmend_question_num=RunnableValue(value=x['reconmmend_question_num']),
                                        json_schema=lambda x:schema,
                                        )
        chain = vars|model_binding|JsonOutputParser()
        return chain
    else:
        return RunnableLambda(lambda x: {'candidates':[]})

metric_template_recommend_question_chain=RunnablePassthrough.assign(**metric_template_configs)|fetch_template|reconmmend_question
metric_template_recommend_question_chain=metric_template_recommend_question_chain.with_types(input_type=MetricTemplateRecommendQuestionInput,output_type=MetricTemplateRecommendQuestionOutput)
