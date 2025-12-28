# cython: annotation_typing = False
import json
from jsonschema import Draft7Validator
from langchain_community.chat_models import *
from framebase.embeddings import *
from community.models import EKCLLM
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from .protocol import ModelConnectChainInputModel, ModelConnectChainOutputModel
from utils.logger import logger
from utils.langfuse_tools import langfuse_handler
from configs import get_configs
from utils.dbs import hset_redis_data, hdel_redis_data
from framebase.models import reload_config_map
from framebase.models import variables,configurables,mappings,config_map, models, model_option_mapping


def is_python_data_type(value):
    # 定义所有内置数据类型的集合
    python_data_types = {
        "int", "str", "float", "list", "dict", "tuple", "bool", "set",
        "complex", "bytes", "bytearray", "memoryview", "range", "NoneType"
    }
    return value in python_data_types


def json_to_jsonschema(json_data):
    def generate_properties(properties):
        properties_schema = {}
        for prop, details in properties.items():
            if isinstance(details, dict):
                properties_schema[prop] = generate_properties(details)
            else:
                properties_schema[prop] = {"type": "string"}
                if is_python_data_type(details):
                    properties_schema[prop] = {"type": details}
                else:
                    properties_schema[prop] = {"value": details}
        return {"properties": properties_schema}

    def generate_items(items):
        items_schema = {}
        for item in items:
            items_schema[item['provider']] = item
        return items_schema

    if isinstance(json_data, dict):
        return generate_properties(json_data)
    elif isinstance(json_data, list):
        return generate_items(json_data)
    else:
        raise ValueError("Unsupported JSON data type")


def validate_json_schema(json_data, json_schema):
    validator = Draft7Validator(json_schema)
    for error in validator.iter_errors(json_data):
        print("Validation error:", error)


def get_models_params():
    model_register_params = get_configs("llm").get("model_register_params")
    json_data = model_register_params.params.get("parameters")
    json_schema_data = json_to_jsonschema(json_data)
    logger.info("Models that support registration: {}".format(list(json_schema_data.keys())))
    return json_schema_data


def model_connect_test(input_):
    connection_type = input_.get("connection_type")
    model_type = input_.get("model_type")
    model_params = input_.get("model_params")
    if not model_type or not model_params:
        return {"result": 0, "status": "params error"}
    if model_type=='AzureChatOpenAI':
        model_params['deployment_name']=model_params['model_name']
    if model_type=='Xinference' and connection_type=='llm':
        model_params={'model_name':model_params['model_name'],'openai_api_base':model_params['xinference_host'].strip('/')+'/v1','openai_api_key':'pass'}
        model_type='EKCLLM'
    elif model_type=='Xinference' and connection_type=='embedding':
        model_params={'model_name':model_params['model_name'],'openai_api_base':model_params['xinference_host'].strip('/')+'/v1','openai_api_key':'pass'}
        model_type='LocalOpenAIEmbeddings'
    client = eval(model_type)(**model_params)
    try:
        if connection_type == "llm":
            client.max_tokens=1
            result = client.invoke("Introduce yourself, within 20 words")
        elif connection_type == "embedding":
            result = client.embed_documents(["hi"])
        else:
            return {"result": 0, "status": "params error, connection_type only support llm or embedding"}
        logger.info("{} registrated successfully".format(model_type))
        test_result = {"result": 1, "status": "connected"}
    except Exception as e:
        message = str(e)
        if hasattr(e, "body") and isinstance(e.body, dict) and "message" in e.body:
            message = e.body.get("message")
        logger.info("{} registrated failed, error: {}".format(model_type, message))
        test_result = {"result": 0, "status": "connect error: {}".format(message)}
    return test_result


model_connect_test_chain = RunnableLambda(model_connect_test)
model_connect_test_chain = model_connect_test_chain.with_types(input_type=ModelConnectChainInputModel,
                                                           output_type=ModelConnectChainOutputModel)



def embedding_register(embedding_info_params):
    from framebase.embeddings import update_embedding_models_by_redis
    embedding_info_params_dict = {}
    for key, one_embedding_info in embedding_info_params.items():
        embedding_info_params_dict[one_embedding_info["public_params"]["id"]]=one_embedding_info
    update_embedding_models_by_redis(embedding_info_params_dict)

