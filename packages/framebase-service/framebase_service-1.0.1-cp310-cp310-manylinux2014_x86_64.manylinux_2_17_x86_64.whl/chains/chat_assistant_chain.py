# cython: annotation_typing = False
import base64
from io import BytesIO
import os
from PIL import Image
from langchain_core.runnables import (
    RunnablePassthrough,RunnablePick,
    RunnableBinding,RunnableBranch,
    RunnableSequence,
    RunnableGenerator,
    RunnableLambda,
    RunnableParallel,
    chain as chain_decorator,
)
from langchain.schema import BaseMessage
from langchain.schema.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json,pkg_resources,uuid,traceback,copy,re
from openai._exceptions import OpenAIError, RateLimitError, InternalServerError, APIConnectionError, APITimeoutError

from framebase.models import models,get_model_capability,get_input_len,config_map as models_config_map,update_llm_runnables,cut_text_by_token_len
from framebase.prompts import config_map as prompts_config_map
from framebase import config_map as additionals_config_map,update_enum_names,config_maps
from framebase.values import RunnableValue,RunnablePrompt
from framebase.output_parsers import astreaming_parser,charge
from framebase.prompts import chain as prompt, mappings as prompt_mappings
from framebase.notices import RunnableNotice
from framebase.synonyms import chain as synonym_word_detect_chain
from community.models.stroutput_parser import ekcStrOutputParser

from utils.dbs import download_from_minio, redis_hget,scroll_arcvector,set_thought
from utils import exceptions
from utils.exceptions import LLMCallError, LLMCallTimeoutError, LLMRateLimitError, format_error_response
from utils.logger import logger
from utils.tools import add_time_stamp_start
from utils.langfuse_tools import langfuse_handler
from utils.connections import arcvector_client

from .protocol import ChatAssistantChainInputModel,ConversationChainOutputModel,AttachmentModel,Document
from .conversation_chain import rag_chain,combine_historys,question_refine_binding,format_history,combine_docs,reformat_config
from .retriever_chain import multi_kbs_retrieve_chain
from langchain_core.messages import SystemMessage, HumanMessage

with open(pkg_resources.resource_filename('configs','service/chat_assistant_layout.json'),'r',encoding='utf-8')as f:
    layout_schema=json.load(f)

inputs = {
    'app_id': lambda x: x.get('app_id'),
    "question": lambda x: x["question"],
    'history': lambda x: x['history'],
    'attachments': lambda x: x.get('attachments'),
    'session_id': lambda x: x.get('session_id')
}

redis_data=RunnablePassthrough.assign(app_key=lambda x:f"app:{x['app_id']}") | \
    RunnablePassthrough.assign(**{
        'config':lambda x:redis_hget(x['app_key'],'config',{}),
        'question': synonym_word_detect_chain
})


@chain_decorator
def model_binding(x,config):
    # chain_config is from redis
    chain_config=x.get('configurable',{})
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config 
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])

    return  RunnableBinding(bound=prompt,config={'configurable':chain_config}) | \
                RunnableBinding(bound=models['chat_assistant_llm'],config={'configurable':chain_config})


@chain_decorator
def mllm_model_binding(x, config):
    # chain_config is from redis
    chain_config = x.get('configurable', {})
    chain_config.update(config['configurable'])
    attachments = chain_config.get('attachments', [])
    history = x.get('history', [])
    multi_round_num = int(x.get('multi_round_num', 0))
    history = history[-multi_round_num * 2:] 
    image_attachments = []
    for att in attachments:
        att = att if isinstance(att, AttachmentModel) else AttachmentModel(**att)
        if att.doc_type == 'image':
            image_attachments.append(att)
    if not image_attachments:
        raise ValueError("No image attachment found for image_qa_chain.")

    def encode_image(image_path, max_pixels=2500*2500):
        with Image.open(image_path) as img:
            if img.mode == "RGBA":
                img = img.convert("RGB") 
            orig_width, orig_height = img.width, img.height
            orig_pixels = orig_width * orig_height
            logger.debug(f"[原始尺寸] 宽: {orig_width}, 高: {orig_height}, 像素数: {orig_pixels}")

            if orig_pixels > max_pixels:
                scale_factor = (max_pixels / orig_pixels) ** 0.5
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                new_pixels = new_width * new_height
                logger.debug(f"[调整后尺寸] 宽: {new_width}, 高: {new_height}, 像素数: {new_pixels}")
            else:
                logger.debug(f"[无需调整] 保持原图尺寸")

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=100, optimize=True)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

    messages_list = [SystemMessage(content="你是一个专业的图片分析助手，请仔细查看图片内容并回答用户的问题。")]
    image_contents = []
    
    for idx, h in enumerate(history):
        if type(h)!= dict:
            h=h.dict()
        if h['role']=='file':
            att =list(filter(lambda x:h['content']==x.doc_name,image_attachments))
            att = att[0] if att else None
            minio_doc_name = download_from_minio(att.minio_bucket, att.minio_object, att.doc_name)
            if not minio_doc_name:
                raise ValueError(f"Failed to download doc from minio: {att.doc_name}")

            ext = os.path.splitext(att.doc_name)[1].lower()
            mime_type = "jpeg"
            image_base64 = encode_image(minio_doc_name)

            image_contents.append({
                "type": "text",
                "text": f"以下是名称为 {att.doc_name} 的图片的内容："
            })
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{mime_type};base64,{image_base64}"
                }
            })
        else:
            image_contents.append({"type": "text", "text": h['content']})

    image_contents.append({"type": "text", "text": x["question"]})
    messages_list.append(HumanMessage(content=image_contents))
    
    mllm_prompt = ChatPromptTemplate(messages=messages_list)

    return RunnableBinding(bound=mllm_prompt, config={'configurable': chain_config}) | \
           RunnableBinding(bound=models['chat_assistant_llm'], config={'configurable': chain_config})

@chain_decorator
def audio_model_binding(x, config):
    # chain_config is from redis
    chain_config = x.get('configurable', {})
    chain_config.update(config['configurable'])

    attachments = chain_config.get('attachments', [])
    audio_attachments = []
    for att in attachments:
        att = att if isinstance(att, AttachmentModel) else AttachmentModel(**att)
        if att.doc_type == 'audio':
            audio_attachments.append(att)
    if not audio_attachments:
        raise ValueError("No audio attachment found for audio_qa_chain.")

    def encode_audio(audio_path):
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode("utf-8")

    messages_list = [SystemMessage(content="你是一个音频助手，可以听取音频内容并回答用户的问题。")]
    audio_contents = []

    for idx, att in enumerate(audio_attachments):
        minio_doc_path = download_from_minio(att.minio_bucket, att.minio_object, att.doc_name)
        if not minio_doc_path:
            raise ValueError(f"Failed to download audio file from minio: {att.doc_name}")

        ext = os.path.splitext(att.doc_name)[1].lower().lstrip(".")
        
        audio_base64 = encode_audio(minio_doc_path)

        audio_contents.append({
            "type": "input_audio",
            "input_audio": {
                "data": audio_base64,
                "format": ext,
            }
        })
        
    audio_contents.append({
        "type": "text",
        "text": x["question"]
    })

    messages_list.append(HumanMessage(content=audio_contents))

    mllm_prompt = ChatPromptTemplate(messages=messages_list)

    return RunnableBinding(bound=mllm_prompt, config={'configurable': chain_config}) | \
           RunnableBinding(bound=models['chat_assistant_llm'], config={'configurable': chain_config})



async def filter_out_think(chunks):
    async for chunk in chunks:
        chunk.reasoning_content=''
        yield chunk

model_output_runnable = {
    'response_variables' :charge,
    'model_output' :  model_binding,
}

model_output_no_thinking_runnable = {
    'response_variables' :charge,
    'model_output' :  model_binding|RunnableGenerator(filter_out_think),
}

mllm_model_output_no_thinking_runnable = {
    'response_variables' :charge,
    'model_output' :  mllm_model_binding|RunnableGenerator(filter_out_think),
}

audio_model_output_no_thinking_runnable = {
    'response_variables': charge,
    'model_output': audio_model_binding | RunnableGenerator(filter_out_think),
}


@chain_decorator
def make_attachement_filter(x):
    attachments=x.get('intent_chain',{}).get('attachments',[])

    valid_doc_ids=list(map(lambda n:n.doc_id,filter(lambda m:m.doc_name in attachments,[AttachmentModel(**p) if type(p)==dict else p for p in x['attachments']])))
    attachment_filter={'must':[{'key':'metadata.doc_file_id','match':{'any':valid_doc_ids}}]}
    return attachment_filter

@chain_decorator
def attachment_retrieve(x,config):
    attachment_filter=RunnablePassthrough.assign(
        filter=make_attachement_filter,custom_tags=lambda x:None,
        kb_ids=lambda x: ['app_'+str(x['app_id'])]
        )
    return RunnablePassthrough.assign(recall_nodes= attachment_filter | multi_kbs_retrieve_chain)

response_type=RunnableBranch(
        (lambda x:x.get('recall_nodes',[]),RunnablePassthrough.assign(response_type=lambda x:['ChatDoc'])),
        RunnablePassthrough.assign(response_type=lambda x:['LLM'])
    ) |RunnablePassthrough(lambda x:logger.debug('response type is:'+str(x['response_type'])))

attachment_rag_chain = RunnablePassthrough.assign(
                filter=make_attachement_filter,
                custom_tags=lambda x:None,
                template_name=RunnableValue(value='chat_assistant_attachment_chat_prompt')
            )|\
            attachment_retrieve|RunnablePassthrough.assign(context=combine_docs)|response_type|rag_chain|astreaming_parser

def cut_off_recall_by_model_capability(max_tokens, model_name, docs, reserve_length=2000, keep_length=None):
    capability=get_model_capability(model_name)
    recall_nodes=[]
    other_nodes=[]
    context=''
    # reserve_length for input prompt length
    avaliable_length=capability-max_tokens-reserve_length
    if keep_length is None:
        keep_length=avaliable_length
    elif keep_length == 'max_tokens':
        keep_length=min(max_tokens,avaliable_length)
    elif keep_length:
        keep_length=min(keep_length,avaliable_length)
    else:
        keep_length=avaliable_length
    enough=False
    for doc in docs:
        if get_input_len(model_name,context+doc.page_content)<keep_length and not enough:
            context+=doc.page_content
            recall_nodes.append(doc)
        else:
            enough=True
        if enough:
            other_nodes.append(doc)
    if not recall_nodes:
        if other_nodes:  # Check if other_nodes is not empty
            other_nodes[0].page_content=cut_text_by_token_len(other_nodes[0].page_content,keep_length)
            recall_nodes.append(other_nodes[0])
            del other_nodes[0] 

    return recall_nodes,other_nodes

@chain_decorator
def summary_retrieve(x,config):
    col_name='app_'+str(x['app_id'])

    doc_chunk_num=int(arcvector_client.count(collection_name=col_name,count_filter=x['filter']).count)
    #retrieve first 30 (or 50%) chunk 
    first = int(max(30, 0.5 * doc_chunk_num))
    #retrieve last 5 (or 5%) chunk
    second = int(max(doc_chunk_num - 5, 0.05 * doc_chunk_num, first))
    chunk_ids = [i for i in range(0, first)]+[i for i in range(second+1, doc_chunk_num + 1)] 
    chunk_ids = [str(uuid.UUID(int=int(i))) for i in chunk_ids]
    scroll_filter={'must':[{ "key": 'metadata.chunk_id',"match": {'any':chunk_ids} },
                               { "key": 'metadata.doc_file_id',"match": {'any':[attachment['doc_id'] for attachment in x['attachments']]} }]}
    
    docs=scroll_arcvector(col_name,scroll_filter)
    recall_nodes,remove_nodes=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_llm'],docs)
    
    return recall_nodes        

@chain_decorator
def fulltext_retrieve(x):
    col_name='app_'+str(x['app_id'])
    scroll_filter={'must':[{ "key": 'metadata.doc_file_id',"match": {'any':[attachment['doc_id'] for attachment in x['attachments']]} }]}
    docs=scroll_arcvector(col_name,scroll_filter)
    docs=sorted(docs,key=lambda doc:uuid.UUID(doc.metadata['chunk_id']).int)
    return docs

@chain_decorator
def fulltext_retrieve_from_vectorstore(x):
    col_name='app_'+str(x['app_id'])+'_fulltext'
    scroll_filter={'must':[{ "key": 'metadata.doc_file_id',"match": {'any':[attachment['doc_id'] for attachment in x['attachments']]} }]}
    docs=scroll_arcvector(col_name,scroll_filter)
    docs=sorted(docs,key=lambda doc:uuid.UUID(doc.metadata['chunk_id']).int)
    return docs

@chain_decorator
def loop_fulltext(x):
    async def bypass(chunks):
        has_chunk=False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk=True
                chunk=chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk=True
                chunk=chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output':'\n\n'}

    loop_fulltext_input=lambda m,n=x:n
    fetch,other=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_llm'],x['recall_nodes'],keep_length='max_tokens')
    chain={'chain': loop_fulltext_input | RunnablePassthrough.assign(**{'text':lambda m,n=fetch:"\n".join([d.page_content for d in n]),
                                                                        'template_name':RunnableValue(value='chat_assistant_translate_prompt'),
                                                                        'recall_nodes':lambda m,n=fetch:n})\
           |model_output_runnable,'output':bypass}

    chains=[chain]
    while other:
        fetch,other=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_llm'],other,keep_length='max_tokens')
        chains.append({'chain': loop_fulltext_input | RunnablePassthrough.assign(**{'text':lambda m,n=fetch:"\n".join([d.page_content for d in n]),
                                                                                    'template_name':RunnableValue(value='chat_assistant_translate_prompt'),
                                                                                    'recall_nodes':lambda m,n=fetch:n})\
           |model_output_no_thinking_runnable,'output':bypass})
        
    return RunnableSequence(*chains,bypass)

@chain_decorator
def attachment_translate_chain(x,config):
    chains=[]
    for attachment in x.get('attachments'):
        attachment=attachment if type(attachment) == dict else attachment.dict()
        attachment_filter=RunnablePassthrough.assign(attachments=lambda x,v=attachment:[v])|RunnablePassthrough.assign(filter=make_attachement_filter,custom_tags=lambda x:None)
        retrieve=attachment_filter|RunnablePassthrough.assign(recall_nodes=fulltext_retrieve_from_vectorstore)

        chain=retrieve|response_type|loop_fulltext
        chains.append(chain)

    async def bypass(chunks):
        has_chunk=False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk=True
                chunk=chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk=True
                chunk=chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output':'\n\n'}
    attachment_translate_chain_input=lambda m,n=x:n
    chain=chains[0]
    if len(chains)>1:
        multi_chains=[]
        for i in range(len(chains)):
            multi_chains.append({'chain': attachment_translate_chain_input |chains[i],'output':bypass})
        chain=RunnableSequence(*multi_chains,bypass)
       
    return RunnableSequence(chain,astreaming_parser)

@chain_decorator
def summary_model_binding(x,config):
    # chain_config is from redis
    chain_config=x.get('configurable',{})
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])

    return  RunnableBinding(bound=prompt,config={'configurable':chain_config}) | \
                RunnableBinding(bound=models['chat_assistant_summary_llm'],config={'configurable':chain_config})

summary_model_output_runnable = {
    'response_variables' :charge,
    'model_output' :  summary_model_binding,
}
summary_model_output_no_thinking_runnable = {
    'response_variables' :charge,
    'model_output' :  summary_model_binding|RunnableGenerator(filter_out_think),
}

@chain_decorator
def loop_fulltext_summary(x):
    async def bypass(chunks):
        has_chunk=False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk=True
                chunk=chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk=True
                chunk=chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output':'\n\n'}

    loop_fulltext_input=lambda m,n=x:n
    fetch,other=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_summary_llm'],x['recall_nodes'],keep_length=None)
    chain={'chain': loop_fulltext_input | RunnablePassthrough.assign(**{'text':lambda m,n=fetch:"\n".join([d.page_content for d in n]),
                                                                        'template_name':RunnableValue(value='chat_assistant_summary_prompt'),
                                                                        'recall_nodes':lambda m,n=fetch:n})\
           |summary_model_output_runnable,'output':bypass}

    chains=[chain]
    while other:
        fetch,other=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_summary_llm'],other,keep_length=None)
        chains.append({'chain': loop_fulltext_input | RunnablePassthrough.assign(**{'text':lambda m,n=fetch:"\n".join([d.page_content for d in n]),
                                                                                    'template_name':RunnableValue(value='chat_assistant_summary_prompt'),
                                                                                    'recall_nodes':lambda m,n=fetch:n})\
           |summary_model_output_no_thinking_runnable,'output':bypass})

    return RunnableSequence(*chains,bypass)

@chain_decorator
def attachment_summary_chain(x,config):
    chains=[]
    for attachment in x.get('attachments'):
        attachment=attachment if type(attachment) == dict else attachment.dict()
        attachment_filter=RunnablePassthrough.assign(attachments=lambda x,v=attachment:[v])|RunnablePassthrough.assign(filter=make_attachement_filter,custom_tags=lambda x:None)
        retrieve=attachment_filter|RunnablePassthrough.assign(recall_nodes=fulltext_retrieve)
        chain=retrieve|response_type|loop_fulltext_summary
        chains.append(chain)

    async def bypass(chunks):
        has_chunk=False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk=True
                chunk=chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk=True
                chunk=chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output':'\n\n'}
    attachment_summary_chain_input=lambda m,n=x:n
    chain=chains[0]
    if len(chains)>1:
        multi_chains=[]
        for i in range(len(chains)):
            multi_chains.append({'chain': attachment_summary_chain_input |chains[i],'output':bypass})
        chain=RunnableSequence(*multi_chains,bypass)
       
    return RunnableSequence(chain,astreaming_parser)

@chain_decorator
def loop_rewrite_fulltext(x,config):

    def check_rewrite_stop(x):
        if config['metadata'].get('rewrite_stop'):
            return True
        if config['metadata'].get('rewrite_counter') and config['metadata']['rewrite_counter']>5:
            return True
        return False

    def get_previous_output(x,config):
        if config['metadata'].get('history_prompt'):
            return config['metadata']['history_prompt'][-1]['content']
        return ''
    
    def get_question(x,config):
        if config['metadata'].get('question'):
            return config['metadata']['question']
        return ''

    @chain_decorator
    async def collect_prompt(x):
        config['metadata']['history_prompt']=[{'role':'human','content':msg.content} for msg in x.messages]
        return x
    
    async def collect_output(chunks):
        llm_output=''
        async for chunk in chunks:
            yield chunk
            if isinstance(chunk,BaseMessage):
                llm_output+=chunk.content
        if not llm_output.strip():
            logger.warning('No output in continue rewrite. Stopped.')
            config['metadata']['rewrite_stop']=True
        if config['metadata'].get('rewrite_counter'):
            config['metadata']['rewrite_counter']+=1
        else:
            config['metadata']['rewrite_counter']=1
        if config['metadata']['rewrite_counter']>5:
            logger.warning('Reach max num of rewrite. Stopped.')
            config['metadata']['rewrite_stop']=True
        if config['metadata'].get('history_prompt'):
            config['metadata']['history_prompt'].append({"role":"assistant","content":llm_output})
        else:
            config['metadata']['history_prompt']=[{"role":"assistant","content":llm_output}]
    
    async def bypass(chunks):
        has_chunk = False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk = True
                chunk = chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk = True
                chunk = chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output': '\n\n'}
    attachment_rewrite_chain_input = lambda m, n=x: n
    fetch, other = cut_off_recall_by_model_capability(x['max_tokens'], x['chat_assistant_llm'], x['recall_nodes'],keep_length='max_tokens')
    chain = {'chain': 
                RunnablePassthrough.assign(text=lambda m, n=fetch: "\n".join([d.page_content for d in n]))|\
                RunnablePassthrough.assign(template_name=RunnableValue(value='chat_assistant_rewrite_prompt')) |
                prompt|collect_prompt|{'model_output':models['chat_assistant_llm']|RunnableGenerator(collect_output)}, 
            'output': bypass}
    try:
        chains = [chain]
        while other:
            fetch, other = cut_off_recall_by_model_capability(x['max_tokens'], x['chat_assistant_llm'], other,
                                                            keep_length='max_tokens')
            _chain=RunnableParallel({'chain': RunnableBranch((
                                                check_rewrite_stop,
                                                    RunnablePassthrough.assign(template_name=RunnableValue(value='chat_assistant_continue_rewrite_prompt'),
                                                                previous_output=get_previous_output,
                                                                question=get_question,
                                                                text=lambda m, n=fetch: "\n".join([d.page_content for d in n]))|
                                                    prompt|{'model_output':models['chat_assistant_llm']|RunnableGenerator(collect_output)}|RunnableGenerator(filter_out_think)),
                                                RunnablePassthrough()), 
                        'output': bypass})
            chains.append(_chain)
        chains.append({'chain':{'response_variables':attachment_rewrite_chain_input|charge},'output':bypass})
        return RunnableSequence(*chains, bypass)
    except ValueError as e:
        return RunnablePassthrough()

@chain_decorator
def attachment_rewrite_chain(x,config):
    chains=[]
    for attachment in x.get('attachments'):
        attachment=attachment if type(attachment) == dict else attachment.dict()
        attachment_filter=RunnablePassthrough.assign(attachments=lambda x,v=attachment:[v])|RunnablePassthrough.assign(filter=make_attachement_filter,custom_tags=lambda x:None)
        retrieve=attachment_filter|RunnablePassthrough.assign(recall_nodes=fulltext_retrieve)

        chain=retrieve|response_type|loop_rewrite_fulltext
        chains.append(chain)

    async def bypass(chunks):
        has_chunk = False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk = True
                chunk = chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk = True
                chunk = chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output': '\n\n'}

    attachment_rewrite_chain_input = lambda m, n=x: n
    chain = chains[0]
    if len(chains) > 1:
        multi_chains = []
        for i in range(len(chains)):
            multi_chains.append({'chain': attachment_rewrite_chain_input | chains[i], 'output': bypass})
        chain = RunnableSequence(*multi_chains, bypass)

    return RunnableSequence(chain, astreaming_parser)

@chain_decorator
def loop_generate_fulltext(x):
    async def bypass(chunks):
        has_chunk=False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk=True
                chunk=chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk=True
                chunk=chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output':'\n\n'}

    loop_fulltext_input=lambda m,n=x:n
    fetch,other=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_summary_llm'],x['recall_nodes'],keep_length=None)
    chain={'chain': loop_fulltext_input | RunnablePassthrough.assign(**{'text':lambda m,n=fetch:"\n".join([d.page_content for d in n]),
                                                                        'template_name':RunnableValue(value='chat_assistant_generate_prompt'),
                                                                        'recall_nodes':lambda m,n=fetch:n})\
           |summary_model_output_runnable,'output':bypass}

    chains=[chain]
    #while other:
    #    fetch,other=cut_off_recall_by_model_capability(x['max_tokens'],x['chat_assistant_summary_llm'],other,keep_length=None)
    #    chains.append({'chain': loop_fulltext_input | RunnablePassthrough.assign(**{'text':lambda m,n=fetch:"\n".join([d.page_content for d in n]),
    #                                                                                'template_name':RunnableValue(value='chat_assistant_generate_prompt'),
    #                                                                                'recall_nodes':lambda m,n=fetch:n})\
    #       |summary_model_output_no_thinking_runnable,'output':bypass})

    return RunnableSequence(*chains,bypass)

@chain_decorator
def attachment_generate_chain(x,config):
    chains=[]
    for attachment in x.get('attachments'):
        attachment=attachment if type(attachment) == dict else attachment.dict()
        attachment_filter=RunnablePassthrough.assign(attachments=lambda x,v=attachment:[v])|RunnablePassthrough.assign(filter=make_attachement_filter,custom_tags=lambda x:None)
        retrieve=attachment_filter|RunnablePassthrough.assign(recall_nodes=fulltext_retrieve)

        chain=retrieve|response_type|loop_generate_fulltext
        chains.append(chain)

    async def bypass(chunks):
        has_chunk = False
        async for chunk in chunks:
            if chunk.get('output'):
                has_chunk = True
                chunk = chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
            if chunk.get('chain'):
                has_chunk = True
                chunk = chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
        if has_chunk:
            yield {'model_output': '\n\n'}

    attachment_generate_chain_input = lambda m, n=x: n
    chain = chains[0]
    if len(chains) > 1:
        multi_chains = []
        for i in range(len(chains)):
            multi_chains.append({'chain': attachment_generate_chain_input | chains[i], 'output': bypass})
        chain = RunnableSequence(*multi_chains, bypass)

    return RunnableSequence(chain, astreaming_parser)

@chain_decorator
def attachment_compare_chain(x,config):
    chains=[]
    for attachment in x.get('attachments'):
        attachment=attachment if type(attachment) == dict else attachment.dict()
        attachment_filter=RunnablePassthrough.assign(attachments=lambda x,v=attachment:[v])|RunnablePassthrough.assign(filter=make_attachement_filter,custom_tags=lambda x:None)
        retrieve=attachment_filter|RunnablePassthrough.assign(recall_nodes=summary_retrieve) | \
            RunnablePassthrough.assign(**{'text':lambda m:"\n".join([d.page_content for d in m['recall_nodes']])})
        chain=RunnablePassthrough.assign(origin_question=RunnableValue(value=f"请总结{attachment['doc_name']}"),template_name=RunnableValue(value='chat_assistant_summary_prompt'))|\
            retrieve|response_type|rag_chain
        chains.append(chain)

    async def bypass(chunks):
        response_context=''
        async for chunk in chunks:
            if chunk.get('chain'):
                chunk=chunk['chain']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
                    model_output = chunk["model_output"]
                    if not isinstance(model_output, dict):
                        if isinstance(model_output,BaseMessage):
                            response_context += model_output.content
                        elif type(model_output)==str:
                            response_context += model_output
                        elif type(model_output)==ChatPromptTemplate:
                            for msg in model_output.messages:
                                response_context+=msg.content

            if chunk.get('output'):
                chunk=chunk['output']
                if "response_variables" in chunk and chunk['response_variables']:
                    yield chunk
                if "model_output" in chunk and chunk['model_output']:
                    yield chunk
                    model_output = chunk["model_output"]
                    if not isinstance(model_output, dict):
                        if isinstance(model_output,BaseMessage):
                            response_context += model_output.content
                        elif type(model_output)==str:
                            response_context += model_output
                        elif type(model_output)==ChatPromptTemplate:
                            for msg in model_output.messages:
                                response_context+=msg.content
        yield {'model_output':'\n\n'}
        yield {'response_context':response_context}
        

    attachment_compare_chain_input=lambda m,n=x:n
    chain=chains[0]
    if len(chains)>1:
        multi_chains=[]
        for i in range(len(chains)):
            multi_chains.append({'chain': attachment_compare_chain_input |chains[i],'output':bypass})
        chain=RunnableSequence(*multi_chains,{'output':bypass})
    
    compare_output={'chain':RunnablePassthrough.assign(
            question=RunnableValue(value=x['question']),
            attachment_summary=lambda x:x['output']['response_context'],
            template_name=RunnableValue(value='chat_assistant_compare_prompt')
        )|{'model_output':model_binding},
        'output':bypass}


    return RunnableSequence(chain,compare_output,bypass,astreaming_parser)

@chain_decorator
def attachment_generic_chat_chain(x,config):
    context = ""
    col_name='app_'+str(x['app_id'])+'_fulltext'
    index = 0
    recall_nodes = []
    doc_content = ''
    doc_name = ''
    for attachment in x.get('used_attachments'):
        p=attachment if type(attachment) == dict else attachment.dict()
        doc_id = p['doc_id']
        doc_name = p['doc_name']
        scroll_filter={'must':[{'key':'metadata.doc_file_id','match':{'any':[doc_id]}}]}
        docs=scroll_arcvector(col_name,scroll_filter)
        docs=sorted(docs,key=lambda doc:uuid.UUID(doc.metadata['chunk_id']).int)
        doc_content = "\n".join([d.page_content for d in docs])
        context += f"<文件{index+1}>\n<name>{doc_name}</name>\n<content>\n{doc_content}</content>\n</文件{index+1}>\n\n"
        if len(docs)>0: recall_nodes.append(docs[0])
        index += 1
    capability=get_model_capability(x['chat_assistant_summary_llm'])
    max_tokens=x['max_tokens']
    logger.debug(f'attachment chat: len(context)={len(context)}, llm_capability={capability}, llm_max_tokens={max_tokens}')
    if len(context) <= capability: #tokenizer property
        response_type = ['ChatDoc'] if len(recall_nodes) > 0 else ['LLM']
        chain= RunnablePassthrough.assign(template_name=RunnableValue(value='chat_assistant_attachment_generic_chat_prompt'),
                                     context=lambda x: context,
                                     recall_nodes = lambda x: recall_nodes,
                                     history_context = combine_historys) | \
                RunnablePassthrough.assign(response_type=lambda x:response_type) | summary_model_output_runnable | astreaming_parser
    elif len(recall_nodes) == 1: #only one file
        #To fix ExceedModelCapabilityError bug
        used_docs,_=cut_off_recall_by_model_capability('chat_assistant_summary_llm',x['chat_assistant_summary_llm'],docs,reserve_length=800,keep_length=None)
        used_doc_content = "\n".join([d.page_content for d in used_docs])
        context =  f"<文件>\n<name>{doc_name}</name>\n<content>\n{used_doc_content}</content>\n</文件>\n\n" +\
                f"<输出要求>回答的第一句话必须为：文档超出字数限制，我只阅读了前{int(len(used_doc_content)*100/len(doc_content))}%。然后输出两个换行符，开始用户问题的回答。</输出要求>\n"
        chain= RunnablePassthrough.assign(template_name=RunnableValue(value='chat_assistant_attachment_generic_chat_prompt'),
                                     context=lambda x: context,
                                     recall_nodes = lambda x: recall_nodes,
                                     history_context = combine_historys) | \
                RunnablePassthrough.assign(response_type=lambda x:['ChatDoc']) | summary_model_output_runnable | astreaming_parser
    else: #more than 1 file and words count exceeds
        chain = {
            'response_variables' : lambda x: {
                "response_type": ['LLM'],
                "feedback": [],
                "confidence":0,
                "relevance":0,
                "sources_documents": [],
                "LLM": [x['chat_assistant_summary_llm']],
                "external_service": {},
                "data_source_query": {},
                "session_id": x['session_id']
            },
            'model_output' : lambda x: AIMessage(content=f"只能阅读这些文档的{int((capability-max_tokens)*100/len(context))}%，请删减文档")
        } | astreaming_parser

    return chain


@chain_decorator
def attachment_intent_chain(x,config):
    x['attachments']=[AttachmentModel(**att) if type(att)!=AttachmentModel else att for att in x['attachments']]
    attachments = x['attachments']
    
    has_audio = any(att.doc_type == 'audio' for att in attachments)
    if has_audio:
        return [{'intent':'audio','attachments':[]}]
    
    has_image = any(att.doc_type == 'image' for att in attachments)
    if has_image:
        return [{'intent':'images','attachments':[]}]
    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='attachment_intent_prompt'),
                                     attachments=lambda x:[att.doc_name for att in x['attachments']],
                                     chat_history=lambda x: format_history(x["history"],int(x["multi_round_num"]))) | \
            prompt|models['chat_assistant_llm'] |ekcStrOutputParser()| \
            RunnablePassthrough(lambda x: logger.debug("attachment_intent_chain output: "+str(x)))  |\
            RunnableLambda(lambda x: JsonOutputParser().invoke(x))
    return chain

def duplicate_attachments(x):
    attachments_dict={}
    if x.get('intent_chain',{}).get('attachments'):
        attachments=[file for file in x['attachments'] if file.doc_name in x['intent_chain']['attachments'] ]
    else:
        attachments=x['attachments']
    for file in attachments:
        if type(file)==AttachmentModel:
           attachments_dict[file.doc_name]=file
        else:
            attachments_dict[file.get('doc_name')]=file
    return list(attachments_dict.values())

@chain_decorator
def free_talk_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='free_prompt'),
                                    context=RunnableValue(value=''),
                                    history_context = combine_historys,
                                    response_type=RunnableValue(values=['LLM'])) | \
            model_output_runnable  | astreaming_parser
    return RunnableBinding(bound=chain,config={'configurable':chain_config})

@chain_decorator
def attachment_image_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='chat_assistant_image_template'),
                                    context=RunnableValue(value=''),
                                    history_context = combine_historys,
                                    response_type=RunnableValue(values=['ChatDoc'])) | \
            mllm_model_output_no_thinking_runnable  | astreaming_parser
    return RunnableBinding(bound=chain,config={'configurable':chain_config})

@chain_decorator
def attachment_audio_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain=RunnablePassthrough.assign(template_name=RunnableValue(value='chat_assistant_audio_template'),
                                    context=RunnableValue(value=''),
                                    history_context = combine_historys,
                                    response_type=RunnableValue(values=['ChatDoc'])) | \
            audio_model_output_no_thinking_runnable  | astreaming_parser
    return RunnableBinding(bound=chain,config={'configurable':chain_config})

#Note: we might also need following attachments-check for other intents, except generate.
attachment_generate_dispatch_chain = RunnableBranch(
    (lambda x:x.get('intent_chain',{}).get('attachments'), attachment_generate_chain),
    free_talk_chain
    )


@chain_decorator
def find_used_attachments(x, config):
    attachments_dict={}
    attachments=[]
    for intent in x.get('intents_chain',[]):
        attachments.extend([file for file in x['attachments'] if file.doc_name in intent['attachments'] ])
    for file in attachments:
        if type(file)==AttachmentModel:
           attachments_dict[file.doc_name]=file
        else:
            attachments_dict[file.get('doc_name')]=file
    return list(attachments_dict.values())

@chain_decorator
def attachment_talk_chain(x,config):
    return RunnablePassthrough.assign(intents_chain=attachment_intent_chain) | \
    RunnablePassthrough(lambda x:logger.debug(x.get('intents_chain'))) |\
    RunnableBranch(
        (lambda x: len(x['intents_chain']) ==1 and x['intents_chain'][0]['intent'] != 'compare' and \
                (len(x['intents_chain'][0]['attachments'])==0 or len(x['intents_chain'][0]['attachments'])==1),
            RunnablePassthrough.assign(intent_chain=lambda x:x['intents_chain'][0]) |\
            RunnablePassthrough.assign(attachments=duplicate_attachments)|\
            RunnableBranch(
               (lambda x:x.get('intent_chain',{}).get('intent')=='summary',attachment_summary_chain),
               #(lambda x:x.get('intent_chain',{}).get('intent')=='compare',attachment_compare_chain),
               (lambda x:x.get('intent_chain',{}).get('intent')=='retrieve',attachment_rag_chain),
               (lambda x:x.get('intent_chain',{}).get('intent')=='translate',attachment_translate_chain),
               (lambda x:x.get('intent_chain',{}).get('intent')=='generate',attachment_generate_dispatch_chain),
               (lambda x:x.get('intent_chain',{}).get('intent')=='rewrite',attachment_rewrite_chain),
               (lambda x:x.get('intent_chain',{}).get('intent')=='images',attachment_image_chain),
               (lambda x:x.get('intent_chain',{}).get('intent')=='audio',attachment_audio_chain),
               attachment_rag_chain)),
        RunnablePassthrough.assign(used_attachments=find_used_attachments) |\
        RunnableBranch(
            (lambda x:x.get('used_attachments'), attachment_generic_chat_chain),
            free_talk_chain
        ))

@chain_decorator
def chat_chain(x,config):
    chain_config=x['configurable']
    chain_config.update(config['configurable'])
    chain= RunnableBranch(
        # has fiile
        (lambda x: x.get('attachments'), attachment_talk_chain),  # chat_chain_with_retrive
        # no file
        free_talk_chain
    )

    return RunnableBinding(bound=chain,config={'configurable':chain_config})

redis_dispatcher= RunnableBranch(
    # has klg_app_id 
    (lambda x:x.get('app_id'), redis_data | reformat_config | question_refine_binding| chat_chain),
    # no klg_app_id
    reformat_config| chat_chain
)

@chain_decorator
async def throw_exception(inputs):
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
                    if 'At most 1 image(s) may be provided in one request.' in exception.message:
                        message = '当前模型只支持一次对话上传一张图片。'
                    elif 'This model\'s maximum context length is' in exception.message:
                        message = '当前内容超过模型上下文长度。'
                    else:
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



exception_handler=throw_exception|astreaming_parser

chain = add_time_stamp_start |\
        RunnablePassthrough.assign(model_name=RunnableValue(value='chat_assistant_llm'),
                                   **config_maps,
                                   **inputs,) |\
        redis_dispatcher

chain = chain.with_fallbacks([exception_handler],exceptions_to_handle=exceptions.errors,exception_key='exception')
chain = chain.with_config(config={'configurable':{'free_mode':'on'}})
chain = chain.with_types(input_type=ChatAssistantChainInputModel, output_type=ConversationChainOutputModel)
