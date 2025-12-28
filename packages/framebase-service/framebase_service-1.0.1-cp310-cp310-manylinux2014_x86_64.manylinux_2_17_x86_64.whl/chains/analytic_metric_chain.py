# cython: annotation_typing = False
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
from langchain_community.utilities.python import PythonREPL
import pkg_resources,json
from langchain_core.output_parsers import JsonOutputParser
from community.models.stroutput_parser import ekcStrOutputParser
from framebase import model_configs,prompt_configs,config_map as additional_configs
from framebase.models import models
from framebase.values import RunnableValue
from framebase.prompts import chain as prompt
from utils.exceptions import JsonEmptyError,JsonValidationError
from utils.logger import logger
from utils.tools import func_to_json_schema,call_from_json
from pydantic import BaseModel,Field,create_model
from pydantic.error_wrappers import ValidationError
from typing import Literal,List,Union,Tuple,Optional
from datetime import datetime,timedelta
from calendar import monthrange
from copy import deepcopy
import re
async def hold_stream(x):
    return x

@chain_decorator
async def model_binding(x, config):
    llm=models[x.get('model_name', 'metric_to_text_llm')]
    return prompt | llm

class MetricRouterInput(BaseModel):
    question:str

class MetricRouterOutput(BaseModel):
    intent:Literal['definition','query','root cause analysis','dimension_analysis','link_analysis','lineage_analysis','rank','scroll']
    
@chain_decorator
def metric_router(x):
    with open(pkg_resources.resource_filename('configs',f'chain/analytic_intent.json'),'r',encoding='utf-8')as f:
        router_schema=json.load(f)
    
    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='metric_router_template'),
                         json_schema=lambda x,v=router_schema:v)|\
        model_binding|ekcStrOutputParser()|hold_stream|JsonOutputParser()
    return chain|RunnablePassthrough(lambda x:logger.debug(f"metric_router: {x.get('intent')}"))
metric_model_conifgs={k:v for k,v in model_configs.items() if k in ['output_llm','sql_or_api_analysis_llm','temperature','top_p','max_tokens']}
metric_router_configs={**metric_model_conifgs,'metric_router_template':prompt_configs['metric_router_template']}
metric_router=RunnablePassthrough.assign(**metric_router_configs)|metric_router
metric_router=metric_router.with_types(input_type=MetricRouterInput,output_type=MetricRouterOutput)
class MetricTimeRecognizerInput(BaseModel):
    question:str

class MetricTimeRecognizerOutput(BaseModel):
    pre_thinking:str=Field(description='请简要思考，按照以下要求依次分析。0.请以“今天的时间是{current_year}-{current_month}-{current_day}。”开头回答。1.找出用户的问题中提到的最小粒度的时间单位（年、月、日、季度、半年等）。如果用户提到了月初、年初、月末、年末月底、年底等词，time_unit设置为DAY。如果用户在问题中提到了“哪月”、“哪年”等词，time_unit以这些词为准。如果用户的问题中没有提到任何时间，time_unit设置为None。2.判断用户的问题中是否提到了时间对比。时间对比需要有多个时间点，请指出对比的时间点分别是哪些。同比是current_year-1，月份环比是current_month-1，年环比是current_year-1。如果用户没有明确指出对比的时间，那么默认是与当前时间做对比；如果用户问题是近x年的对比，那么对比的时间是{current_year-x+1}和{current_year}；如果用户对比的时间是较前期或较同期，请判断这些比较是否是与用户提到的时间的比较或者与当前时间的前期/同期对比。3.请你判断用户问题中是否提到了具体的年份。4.**你需要按照yyyy-MM-dd的格式输出时间**，年份必须是4位数，月份和日都必须是2位数字。注意，默认的年份是current_year，如果用户没有指定年份，必须将年份设置为current_year。请你判断开始和结束时间是什么，**当用户提到具体的时间时，开始和结束时间以用户提到的时间为准**。开始时间是所有时间中最早的一天，结束时间是所有时间中最后一天。用户如果希望查询“当前”/“目前”/“现在”等时间，请把开始和结束时间设置为空。用户没有提到具体的时间时，请不要给出startDate和endDate。用户提到了部分时间，但用户没有提到具体的年份时，请将年份设置为current_year。用户没有提到具体的月份时，startDate的月份请设置为1月，endDate的月份请设置为12月；用户没有提到具体的日期时，startDate的日期请设置为1日，endDate的日期请设置为{last_day_of_month}。对于近x年类的问题，startDate设置为{current_year-x+1}-{current_month}-{current_day}，endDate设置为当前时间，即{current_year}-{current_month}-{current_day}。')
    time_unit:Literal['DAY','MONTH','QUARTER','YEAR','None']=Field(description='用户的问题中的时间名词的最小的粒度。要求：1.如果用户提到了月初、年初、月末、年末、月底、年底等词，time_unit设置为DAY。2.如果用户提到了特定的时间，那么time_unit设置为用户提到的时间中最小的粒度。3.如果用户的问题中没有提到任何时间，time_unit设置为DAY。')
    startDate:Optional[str]=Field(description='根据pre_thinking中的信息给出用户问题中涉及到的开始时间。startDate可以和endDate相同。用户提到每天时，startDate要设置为该月的最后一天或{last_day_of_month}。多个时间对比时，选择最早的时间作为startDate。')
    endDate:Optional[str]=Field(description='根据pre_thinking中的信息给出用户问题中涉及到的结束时间。startDate可以和endDate相同。用户提到每天时，endDate要设置为该月的最后一天或{last_day_of_month}。多个时间对比时，选择最晚的时间作为endDate。用户提到每月时，endDate要设置为该年的12-31。')
    class Config:
        schema_extra = {
            "description": "总体要求：1.使用current_year等特殊变量时，要加上花括号，例如{current_year-1}表示去年。对于current_month，不需要考虑做完减法后变成负数。特殊变量只能做加法和减法，不支持其他操作和运算。2.使用current_year等特殊变量时，要加上花括号，例如{current_year-1}-{current_month}表示中去年最新的一个月。3.用户的问题中没有提到任何时间时，不需要给出startDate和endDate。用户提到“当前”时，startDate和endDate都设置为当前的时间。4.用户的问题中提到的近一年、过去三个月等时间偏移，请在{current_year}-{current_month}-{current_day}基础上计算。5.上一年可以表示为{current_year-1}。同比可以表示为{current_year-1}-{current_month}-{current_day}。某个月份的最后一天可以用last_day_of_month来表示。current和latest的时间不能混用、不能组合使用。不要使用嵌套的花括号，也不要使用两重花括号。6.注意区分用户问题的指标名称，有些指标名称会包含时间性名词，不要把时间性名词当成时间变量。7.对比时如果没有明确指定时间，那么默认是与当前时间做对比。多个时间对比时，选择最早和最晚的时间作为开始和结束时间。"
        }
        extra = "forbid"


@chain_decorator
async def metric_time_recognize(x):

    @chain_decorator
    async def zhonghua_process(x,config):
        if any(word in config['configurable']['question'] for word in ['截止目前','截至目前','最新']):
            x['startDate']=''
            x['endDate']=''
        return x
    
    @chain_decorator
    def check_json(x,config):
        
        def repl(match):
            t=match.group(1)
            keywords = [
                'current_year', 'current_month', 'current_day', 'current_quarter',
                'latest_year', 'latest_month', 'latest_day', 'latest_quarter','last_day_of_month'
            ]

            # 构造正则表达式
            pattern = re.compile(
                r'\b(' + '|'.join(map(re.escape, keywords)) + r')(?:[+-]\d+)?\b'
            )
            if not pattern.match(t):
                raise ValueError(f'Invalid variable:{t}')
            return '1'
            
        if not x:
            raise JsonEmptyError('Json format error.',config['configurable']['json_schema'].schema())
        try:
            if x.get('startDate'):
                if '{{' in x['startDate']:
                    x['startDate']=x['startDate'].replace('{{','{')
                    x['startDate']=x['startDate'].replace('}}','}')
                    #raise ValueError(f'Not support nested json:{x["startDate"]}')
                counts=re.sub(r'\{(.*?)\}', repl, x['startDate'])
                if len(counts.split('-'))!=3:
                    raise ValueError(f'Date format error:{x["startDate"]}, must be yyyy-mm-dd')
            if x.get('endDate'):
                if '{{' in x['endDate']:
                    x['endDate']=x['endDate'].replace('{{','{')
                    x['endDate']=x['endDate'].replace('}}','}')
                    #raise ValueError(f'Not support nested json:{x["endDate"]}')
                counts=re.sub(r'\{(.*?)\}', repl, x['endDate'])
                if len(counts.split('-'))!=3:
                    raise ValueError(f'Date format error:{x["endDate"]}, must be yyyy-mm-dd')
            config['configurable']['json_schema'].validate(x)
        except (ValidationError,ValueError) as e:
            raise JsonValidationError(str(e),config['configurable']['json_schema'].schema())
        return x

    @chain_decorator
    async def repair_json(x,config):
        _logger=RunnablePassthrough(lambda x:logger.debug(f"repair_json: {x}"))
        if '{{' in x['json'] and '}}' in x['json']:
            x['exception']=JsonValidationError('Not support nested json. Fobid to use nested json.',x['exception'].schema)
        chain={
            'template_name':RunnableValue(value='json_repair_template'),
            'json_str':lambda x:x,
            'question':lambda x:config['configurable']['question']
        }|\
            model_binding|ekcStrOutputParser()|hold_stream|_logger|JsonOutputParser()
        return chain

    @chain_decorator
    async def formatter(x,config):
        
        def repl(match):
            if 'latest' in match.group(1):
                return '{'+match.group(1)+'}'
            t=eval(match.group(1),{'last_day_of_month':'last_day_of_month'})
            if t=='last_day_of_month':
                return 'last_day_of_month'
            if len(str(t))==4:
                if t<=0:
                    t*=-1
                    return f'p{t:04d}'
                else:
                    return f'{t:04d}'
            else:
                if t<=0:
                    t*=-1
                    return f'p{t:02d}'
                else:
                    return f'{t:02d}'
            
        try:
            for k,v in x.items():
                if 'current_year' in v:
                    v=v.replace('current_year',str(datetime.now().year))
                if 'current_month' in v:
                    v=v.replace('current_month',str(datetime.now().month))
                    # Fix format 0{number-number} (e.g., 0{11-5} -> {11-5}) only when after - or at start
                    v=re.sub(r'(-\s*|^)0\{(\d+)-(\d+)\}', r'\1{\2-\3}', v)
                if 'current_day' in v:
                    v=v.replace('current_day',str(datetime.now().day))
                if 'current_quarter' in v:
                    if k=='startDate':
                        v=v.replace('current_quarter',str((datetime.now().month-1)//3*3+1))
                    else:
                        v=v.replace('current_quarter',str((datetime.now().month-1)//3*3+3))
                if k=='time_unit':
                    if any(word in config['configurable']['question'] for word in ['月初','月初','月末','年末']):
                        x[k]='DAY'
                else:
                    if k=='pre_thinking':
                        continue
                    if len(v.split('-'))==3:
                        year=v.split('-')[0]
                        if len(year)==2:
                            year=f'{str(datetime.now().year)[:2]}{year}'
                        v=f"{year}-{v.split('-')[1]}-{v.split('-')[2]}"
                    x[k]=re.sub(r'\{(.*?)\}', repl, v)
                    if 'last_day_of_month' in v:
                        continue
                    # 处理负数
                    if 'p' in x[k]:
                        # 2025年1月2日过去2个月零2天，2024-10-31，63天
                        delta_day=0
                        # x[k]=2025-p1-p0
                        # 2025,p1,p0
                        year,month,day=x[k].split('-')
                        # 2025,1,1
                        _year,_month,_day=map(lambda x:1 if 'p' in x else int(x),[year,month,day])
                        # 0,1,0
                        year_,month_,day_=map(lambda x:int(x[1:]) if 'p' in x else 0,[year,month,day])
                        if year_>0:
                            raise ValueError(f'系统不支持公元前的日期：{_year}')
                        if day_>0:
                            delta_day+=1
                        if month_>0:
                            delta_day+=31
                        delta_day+=day_
                        for _ in range(month_):
                            _month-=1
                            if _month<=0:
                                _year-=1
                                _month+=12
                            delta_day+=monthrange(_year,_month)[1]
                        
                        date=datetime(int(_year),int(_month),int(_day))-timedelta(days=delta_day)
                        x[k]=date.strftime('%Y-%m-%d')
                        
        except Exception as e:
            raise JsonValidationError(str(e),config['configurable']['json_schema'].schema())
        return x
    _formatter=formatter.with_config(config={'configurable':{'json_schema':MetricTimeRecognizerOutput,'question':x['question']}})
    _logger=RunnablePassthrough(lambda x:logger.info(f"metric_time_recognizer: {x}"))
    _repair_json=repair_json.with_config(config={'configurable':{'question':x['question']}})
    parser=RunnablePick('json')|JsonOutputParser()|check_json|_formatter
    parser=parser.with_config(config={'configurable':{'json_schema':MetricTimeRecognizerOutput,'question':x['question']}})
    parser_with_repair=RunnableLambda(lambda x:{'json':x})|\
        parser.with_fallbacks([_repair_json|_formatter],exceptions_to_handle=(JsonEmptyError,JsonValidationError),exception_key='exception')
    
    zhonghua_process=zhonghua_process.with_config(config={'configurable':{'question':x['question']}})

    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='analytic_time_recognizer_template'),
                         json_schema=lambda x,v=MetricTimeRecognizerOutput.schema():v,
                         )|\
        model_binding|ekcStrOutputParser()|hold_stream|_logger|parser_with_repair|zhonghua_process
    
    return chain



metric_time_recognizer_configs={**metric_model_conifgs,
                                'analytic_time_recognizer_template':prompt_configs['analytic_time_recognizer_template'],
                                'metric_intent_user_prompt':prompt_configs['metric_intent_user_prompt']}
metric_time_recognizer= RunnablePassthrough.assign(**metric_time_recognizer_configs)|\
                        metric_time_recognize
                       
metric_time_recognizer=metric_time_recognizer.with_types(input_type=MetricTimeRecognizerInput,output_type=MetricTimeRecognizerOutput)

def time_convert(startDate,endDate,latest_date):

    def repl(match):
            if 'latest' in match.group(1):
                return '{'+match.group(1)+'}'
            t=eval(match.group(1))
            if len(str(t))==4:
                return f'{t:04d}'
            else:
                return f'{t:02d}'
            
    latest_year=latest_date.year
    latest_month=latest_date.month
    latest_day=latest_date.day
    latest_quarter=latest_date.month//3*3+3
    if not startDate:
        _startDate=None
    elif 'latest' in startDate:
        _startDate=startDate.replace('latest_year',str(latest_year))
        _startDate=_startDate.replace('latest_month',str(latest_month))
        _startDate=_startDate.replace('latest_day',str(latest_day))
        _startDate=_startDate.replace('latest_quarter',str(latest_quarter))
        _startDate=re.sub(r'\{(.*?)\}', repl, _startDate)        
    else:
        _startDate=startDate
    if _startDate and 'last_day_of_month' in _startDate:
        _startDate=_startDate.replace('last_day_of_month',str(monthrange(int(_startDate.split('-')[0]),int(_startDate.split('-')[1]))[1]))
    if not endDate:
        _endDate=None
    elif 'latest' in endDate:
        _endDate=endDate.replace('latest_year',str(latest_year))
        _endDate=_endDate.replace('latest_month',str(latest_month))
        _endDate=_endDate.replace('latest_day',str(latest_day))
        _endDate=_endDate.replace('latest_quarter',str(latest_quarter))
        _endDate=re.sub(r'\{(.*?)\}', repl, _endDate)
    else:
        _endDate=endDate
    if _endDate and 'last_day_of_month' in _endDate:
        _endDate=_endDate.replace('last_day_of_month',str(monthrange(int(_endDate.split('-')[0]),int(_endDate.split('-')[1]))[1]))
    return _startDate,_endDate

class DimensionModel(BaseModel):
    name:str=Field(description='维度名称。')
    value:Optional[str]=Field(description='维度值。')

class AnalyticDimensionRecognition(BaseModel):
    dimensions:List[DimensionModel]
    class Config:
        schema_extra = {
            "description": "请从用户的问题中提取出需要分析的维度。如果用户只提到了维度值，那么请尝试根据维度值推断出维度名称。"
        }

class MetricDimensionRecognizerInput(BaseModel):
    question:str

MetricDimensionRecognizerOutput=AnalyticDimensionRecognition

@chain_decorator
async def analytic_dimension_recognizer(x):
    _logger=RunnablePassthrough(lambda x:logger.info(f"metric_dimension_recognizer: {x}"))
    if x.get('router_json',{}).get('metric'):
        exclude=f"{x.get('router_json',{}).get('metric')}是指标名称，请识别此指标的维度信息。\n"
    else:
        exclude=''
    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='analytic_dimension_recognizer_template'),
                                    json_schema=lambda x,v=AnalyticDimensionRecognition.schema():v,
                                    exclude=lambda x:exclude,
                                    question=RunnablePick('question'))|\
        model_binding|ekcStrOutputParser()|hold_stream|_logger|JsonOutputParser()|RunnablePick('dimensions')
    
    return chain

metric_dimension_recognizer_configs={**metric_model_conifgs,
                                'analytic_dimension_recognizer_template':prompt_configs['analytic_dimension_recognizer_template'],
                                'metric_intent_user_prompt':prompt_configs['metric_intent_user_prompt']}
metric_dimension_recognizer= RunnablePassthrough.assign(**metric_dimension_recognizer_configs)|\
                        RunnablePassthrough.assign(dimensions=analytic_dimension_recognizer)
metric_dimension_recognizer=metric_dimension_recognizer.with_types(input_type=MetricDimensionRecognizerInput,output_type=MetricDimensionRecognizerOutput)

