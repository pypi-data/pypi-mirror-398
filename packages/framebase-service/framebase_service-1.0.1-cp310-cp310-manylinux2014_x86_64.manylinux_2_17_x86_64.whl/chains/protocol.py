# cython: annotation_typing = False
from typing import Any, Dict, List, Union, Optional, Literal
from pydantic import BaseModel, Field
from langchain.schema.messages import HumanMessage, AIMessage
from langserve import CustomUserType
from langchain.schema.document import Document
from framebase.protocol import StreamingOutputModel, UsageModel, SearchToolModel, ConversationHistory


# ---------For conversation------------------------------------


class AttachmentModel(BaseModel):
    doc_name: str
    doc_id: str
    doc_type: Optional[str] = None
    minio_bucket: Optional[str] = None
    minio_object: Optional[str] = None
    
class ChatAssistantChainInputModel(BaseModel):
    """Input for the conversation chain."""
    history: List[ConversationHistory]
    agent_id: Optional[str]
    app_id: Optional[int]
    attachments: Optional[List[AttachmentModel]]
    question: str
    session_id: Optional[str]

ConversationChainOutputModel=StreamingOutputModel

class SplitterChainInputOutputModel(BaseModel):
    docs: Document

class LoaderSplitterChainInputModel(BaseModel):
    """Input for the file parser"""
    file_path: str
    doc_file_id: int
    data_type: str
    origin_file_name: str
    ancestors: str
    urls: List[str]

class LoaderSplitterChainOutputModel(BaseModel):
    docs: Document

class  SaveChainInputModel(BaseModel):
    docs: List[Document]
    kb_id: str
    org: Optional[List[int]]
    tags: Optional[List[List[int]]]
    doc_id: Optional[str]
    to_opensearch: Optional[bool]
    custom_tags: Optional[List[List[int]]]
    loader_result: Optional[List[Document]]
    keyinfo:Optional[dict]

class MultiRetrieverChainInputModel(BaseModel):
    history: List[ConversationHistory]
    tags: List[List[int]]
    org: List[int]
    allow: List[str]=[]
    deny: List[str]=[]
    kb_ids: List[str]
    multi_src_kb_ids: Optional[List[str]]
    question: str
    user_dict: Optional[str] = None
    custom_tags: Optional[List[List[int]]]
    session_id: Optional[str]
    retriever_doc_kvs: Optional[dict]
    doc_file_ids: Optional[List[str]] = None

class RemoteRetrieverChainInputModel(BaseModel):
    history: List[ConversationHistory]
    tags: List[List[int]]
    org: List[int]
    allow: List[str]=[]
    deny: List[str]=[]
    app_id: int
    question: str
    custom_tags: Optional[List[List[int]]]
    session_id: Optional[str]

class RetrieverChainInputModel(BaseModel):
    history: List[ConversationHistory]
    tags: List[List[int]]
    org: List[int]
    kb_id: str
    allow: List[str]=[]
    deny: List[str]=[]
    question: str

class RetrieverChainOutputModel(BaseModel):
    docs: Document

class RelatedQuestionsChainInputModel(BaseModel):
    history: List[ConversationHistory] #current chat history, at least 2 msg: human, ai
    tags: List[List[int]]
    org: List[int]
    allow: List[str]=[]
    deny: List[str]=[]
    agent_id: Optional[str]
    app_id: Optional[int]
    app_type: Optional[str]
    kb_ids: Optional[List[int]]=None
    metric_base_ids: Optional[List[int]]=None

class ClarifyChainInputModel(BaseModel):
    question: str
    session_id: Optional[str]
    candidates: List[str]
    history: List[ConversationHistory]
    tags: List[List[int]]
    org: List[int]
    allow: List[str]=[]
    deny: List[str]=[]
    agent_id: Optional[str]
    app_id: Optional[int]
    app_type: Optional[str]
    kb_ids: Optional[List[int]]=None
    metric_base_ids: Optional[List[int]]=None

class ClarifyChainOutputModel(BaseModel):
    clarify_choices: List[str]
    usage: Optional[UsageModel]

class RelatedQuestionsChainOutputModel(BaseModel):
    related_questions: List[Optional[str]]  #List of related questions
    usage: Optional[UsageModel]


class ModelConnectChainInputModel(BaseModel):
    connection_type: str
    model_type: str
    model_params: dict


class ModelConnectChainOutputModel(BaseModel):
    result: int  # 1 for connected and 0 for not work
    status: str  # success or error message

class MetricRequestModel(BaseModel):
    type: str = 'metric_query'
    metricIdList: List[str]
    windowDate: str
    time_interval: str
    startDate: str
    endDate: str
    aggregation: str
    dimensionFilters: dict | None
    dimensionHolds: List[str] | None
    offset: int
    metricValueFilters: dict|None
    sorting: list|None
    limit: int
    comparisons: dict|None
    request_index: str
    is_accumulative: bool|None

class SortByModel(BaseModel):
    field: Literal['contribution']
    order: Literal['ASC', 'DESC']
class MetricDimensionRequestModel(BaseModel):
    type:str = 'dimension'
    metricName: str
    metricId: str
    metricType: str
    sourceDate: str
    targetDate: str
    dimensionHolds: List[str] | None
    dimensionFilters: dict | None
    request_index: str
    sortBy: SortByModel | None

class DimensionDrillDownModel(BaseModel):
    dimensionName: str
    dimensionValue: str
    growthValue: float

class MetricDimensionDrillDownRequestModel(BaseModel):
    type:str = 'dimension-drill-down'
    metricId: str
    sourceDate: str
    targetDate: str
    dimensionHolds: List[str] | None
    analysisDimensionsDrillDown: List[DimensionDrillDownModel]
    sortBy: SortByModel | None

class MetricLinkRequestModel(BaseModel):
    type:str = 'metric-link-analysis'
    metricId: str
    metricType: str
    sourceDate: str
    targetDate: str
    metricName: str
    request_index: str

class MetriclineageRequestModel(BaseModel):
    type:str = 'lineage-analysis'
    metricId: str
    metricType: str
    sourceDate: str
    targetDate: str
    metricName: str
    targetTableId: str
    request_index: str

class OutlineWriterModel(BaseModel):
    type: str = 'outline_writer'
    kbs: List[Dict]
    output: str
    title: Optional[str]
    outline: str
    articleType: Optional[str]
    styleKbs: Optional[List[int or str]]
    
class RefineWriterModel(BaseModel):
    type: Optional[str] = None
    details: Optional[str] = None

class MetricTemplateAnalysisSubRequestModel(BaseModel):
    top1_template_id: int

class SubRequestModel(BaseModel):
    text2metric_chain: List[Union[MetricRequestModel,MetricDimensionDrillDownRequestModel,MetriclineageRequestModel,MetricDimensionRequestModel,MetricLinkRequestModel]]|None
    metric_template_analysis_chain: MetricTemplateAnalysisSubRequestModel | None
    # TODO support other sub chains
    #text2kb_chain: List[Union[]]
    #text2api_chain: List[Union[]]
    #text2sql_chain: List[Union[]]

class Text2MetricChainInputModel(BaseModel):
    history: List[ConversationHistory] #might be empty list
    tags: List[List[int]]  #permission tags
    org: List[int]
    app_id: int  #required, no support for chat_assistant app
    question: str
    metric_base_ids: List[str]=["-1"]
    sub_requests: List[Union[MetricRequestModel,MetricDimensionRequestModel,MetricDimensionDrillDownRequestModel,MetricLinkRequestModel]]|None
    client_id: Optional[str] #required, tenant ID
    session_id: Optional[str] #required, from EKC
    agent_id: Optional[str]
    custom_tags: Optional[List[List[int]]]  #custom tags

class MetricIntentChainOutputModel(BaseModel):
    intent_branches:Dict
    raw_metric_info:List
    router_json:Dict
    
class ToolIdModel(BaseModel):
    api_ids:List[str]

class ConversationChainInputModel(BaseModel):
    """Input for the conversation chain."""
    history: List[ConversationHistory]
    sub_requests: Optional[List[SubRequestModel]]=[]
    tags: List[List[int]|None]=[]
    org: List[int]=[1]
    allow: List[str]=[]
    deny: List[str]=[]
    agent_id: Optional[str]
    client_id: Optional[str]
    app_id: Optional[int]
    question: str
    session_id: Optional[str]
    custom_tags: Optional[List[List[int]]]=[]
    custom_items: Optional[Dict]
    metric_base_ids: Optional[List[int]]=None
    metric_template_base_ids: Optional[List[int]]=None
    kb_ids: Optional[List[int]]=None
    table_src_ids: Optional[List[str]]=None
    multi_src_kb_ids: Optional[List[str]]=None
    data_src_ids: Optional[List[int]]=None
    tool_ids: Optional[ToolIdModel]=None
    synonym_ids: Optional[List[str]] = None
    search_tools: Optional[List[SearchToolModel]] = None

class DocFulltextChainInputModel(BaseModel):
    target_doc_id: str
    target_collection_name: str

class DocFulltextChainOutputModel(BaseModel):
    target_doc_fulltext: str

class Text2sqlChainInputModel(BaseModel):
    question: str
    data_src_ids: List[str]
    session_id: str

class Text2sqlChainOutputModel(BaseModel):
    response_variables:Dict[str,Any]

class Text2cypherChainInputModel(BaseModel):
    question: str
    data_src_ids: List[str]
