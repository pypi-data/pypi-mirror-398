# cython: annotation_typing = False
import os, uuid
from copy import deepcopy
from langchain_core.runnables import RunnableMap, RunnablePassthrough, chain as chain_decorator, RunnablePick, \
    RunnableParallel, RunnableBranch

from framebase.document_loaders import document_loader
from framebase.splitters import splitter
from .protocol import LoaderSplitterChainInputModel, LoaderSplitterChainOutputModel, SplitterChainInputOutputModel

from utils import logger


def insert_metadata(inputs):
    logger.info("update metadata after splitter.")
    for i, doc in enumerate(inputs['docs']):
        metadata = doc.metadata
        metadata['chunk_id'] = str(uuid.UUID(int=i))
        metadata['groupby_id'] = metadata['chunk_id']
        metadata['data_type'] = inputs.get('data_type') or metadata.get('data_type')
        metadata['ancestors'] = inputs.get('ancestors') or []
        metadata['show_content'] = metadata.get('show_content', "")
        metadata['doc_content_type'] = metadata.get('doc_content_type') or 'text'
        metadata['doc_file_id'] = inputs.get('doc_file_id', '')
        metadata["source"] = inputs.get("origin_file_name") if inputs.get("origin_file_name") else metadata.get(
            "source", [])
        doc.page_content = os.path.splitext(os.path.basename(metadata['source']))[
                               0] + "的内容:" + doc.page_content if inputs.get(
            "request_type") == "mq" else doc.page_content
        metadata['summary'] = ""
        if 'page' in metadata and metadata['page']:
            metadata['page_number'] = metadata['page']
    return inputs['docs']


inputs = RunnableParallel({
    "file_path": lambda x: x.get("file_path"),
    "urls": lambda x: x.get('urls'),
    'doc_file_id': lambda x: x.get('doc_file_id'),
    'origin_file_name': lambda x: x.get('origin_file_name'),
    'data_type': lambda x: x.get('data_type', 'doc-chunk'),
    "ancestors": lambda x: x.get('ancestors') or [],
    "request_type": lambda x: x.get('request_type', 'mq')
})


@chain_decorator
def check_splitter(x, config):
    if config.get('configurable', {}).get('splitter_name'):
        return True
    else:
        return False


splitter_by_loader = RunnableBranch(
    (check_splitter, splitter),
    RunnablePassthrough()
)


@chain_decorator
def loader_result_dispatcher(x, config):
    loader_result = deepcopy(x.get('docs', []))
    docs = splitter_by_loader.with_config(config).invoke(x.get('docs', []))
    x.update(docs)
    return {'loader_result': loader_result, 'origin_file_name': x.get('origin_file_name'), 'docs': insert_metadata(x)}


chain = inputs | \
        RunnablePassthrough.assign(
            docs=document_loader,
            doc_file_id=RunnablePick('doc_file_id'),
            origin_file_name=RunnablePick('origin_file_name')
        ) | \
        loader_result_dispatcher

chain = chain.with_types(input_type=LoaderSplitterChainInputModel, output_type=LoaderSplitterChainOutputModel)
