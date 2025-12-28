# cython: annotation_typing = False
import json

from langchain_core.runnables import (
    RunnablePassthrough, RunnableBranch, RunnableLambda
)
from langchain_core.output_parsers import JsonOutputParser
from framebase.models import models
from community.models.stroutput_parser import ekcStrOutputParser
from framebase.prompts import chain as prompt
from framebase.values import RunnableValue
from utils.logger import logger

api_analysis_model = models['api_analysis_llm'].with_config(config={'configurable':{'temperature':0.01}})

inputs = {
    "api_schema": lambda x: json.dumps(x["api_schema"], indent=4, ensure_ascii=False)
}

step1_prompt = RunnablePassthrough.assign(template_name=RunnableValue(value='api_analysis_step1_template')) | prompt
step2_prompt = RunnablePassthrough.assign(template_name=RunnableValue(value='api_analysis_step2_template')) | prompt

show_type_branch = RunnableBranch(
    (lambda x: json.loads(x['step1_params'])['show_type'] == "table",
     lambda x: RunnablePassthrough.assign(step2_params=step2_prompt | api_analysis_model | ekcStrOutputParser()) |
               RunnablePassthrough.assign(step2_params=lambda x: clean_model_output_to_json_str(x["step2_params"]))),
    lambda x: x
)


def final_response(x):
    try:
        step1_params = json.loads(x['step1_params'])
        show_type = step1_params["show_type"] if step1_params.get("show_type") else ""
        page_param = step1_params['page_param'] if step1_params.get("page_param") else {}
        page_size_param = step1_params['page_size_param'] if step1_params.get("page_size_param") else {}

        if x.get('step2_params'):
            step2_params = json.loads(x['step2_params'])
            full_data_request_data = step2_params['full_data_request_data'] if step2_params.get(
                "full_data_request_data") else {}
            response_table_data = step2_params['response_table_data'] if step2_params.get("response_table_data") else ""
        else:
            full_data_request_data = {}
            response_table_data = ""

        response = {"show_type": show_type,
                    "page_param": page_param,
                    "page_size_param": page_size_param,
                    "full_data_request_data": full_data_request_data,
                    "response_table_data": response_table_data}
        logger.info(f"api analysis result: {response}")
    except:
        response = {"show_type": "",
                    "page_param": {},
                    "page_size_param": {},
                    "full_data_request_data": {},
                    "response_table_data": ""}
    return response


def clean_model_output_to_json_str(input_str):
    try:
        # 移除注释并重新组合字符串
        lines = input_str.split('\n')
        clean_lines = []
        for line in lines:
            clean_line = line.split('#')[0].rstrip()  # 截取"//"之前的内容并去除行尾空白
            if clean_line:  # 避免添加空行
                clean_lines.append(clean_line)
        clean_json_str = '\n'.join(clean_lines)
        chain=JsonOutputParser()
    
        return json.dumps(chain.invoke(clean_json_str))
    except:
            return '{}'


final_response_runnable = RunnablePassthrough.assign(response=RunnableLambda(final_response))

chain = RunnablePassthrough.assign(**inputs) | \
        RunnablePassthrough.assign(step1_params=step1_prompt | api_analysis_model | ekcStrOutputParser()) | \
        RunnablePassthrough.assign(step1_params=lambda x: clean_model_output_to_json_str(x["step1_params"])) | \
        show_type_branch | \
        final_response_runnable

if __name__ == '__main__':
    from test_cases.unit_tests.chains.unit_test_data import API_DOC_EXAMPLE
    import time

    time1 = time.time()
    response = chain.invoke({"api_schema": API_DOC_EXAMPLE})
    time2 = time.time()
    print("time cost:{}".format(time2 - time1))
    print(response["response"])
