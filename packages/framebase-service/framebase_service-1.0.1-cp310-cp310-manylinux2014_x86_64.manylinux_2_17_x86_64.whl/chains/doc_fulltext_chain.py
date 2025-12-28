# cython: annotation_typing = False
import uuid
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBranch,
    chain as chain_decorator,
    RunnableLambda,
    RunnablePick
)

from utils.logger import logger
from utils.dbs import get_doc_fulltext_opensearch, scroll_arcvector

from .protocol import DocFulltextChainInputModel, DocFulltextChainOutputModel

inputs = {
    "target_doc_id": lambda x: x['target_doc_id'],
    "target_collection_name": lambda x: x['target_collection_name']
}

@chain_decorator
def make_summary_filter(x):
    my_filter={'must':[{'key':'metadata.doc_file_id','match':{'any':[x['target_doc_id']]}}]}
    return my_filter

@chain_decorator
def fulltext_retrieve(x):
    col_name= x['target_collection_name']
    scroll_filter={'must':[{ "key": 'metadata.doc_file_id',"match": {'any':[x['target_doc_id']]} }]}
    docs=scroll_arcvector(col_name,scroll_filter)
    docs=sorted(docs,key=lambda doc:uuid.UUID(doc.metadata['chunk_id']).int)
    return docs

def get_fulltext_by_recall_nodes(x):
    return "\n".join([d.page_content for d in x['recall_nodes']])

get_doc_fulltext_vectordb_chain = RunnablePassthrough.assign(filter=make_summary_filter,custom_tags=lambda x:None) | \
        RunnablePassthrough.assign(recall_nodes=fulltext_retrieve) | \
        RunnableLambda(get_fulltext_by_recall_nodes)

chain = RunnablePassthrough.assign(**inputs) | \
        RunnablePassthrough.assign(target_doc_fulltext = lambda x: get_doc_fulltext_opensearch(x['target_doc_id'])) | \
        RunnablePassthrough(lambda x: logger.info('input before get doc fulltext: doc_file_id='+ x['target_doc_id'] )) | \
        RunnableBranch(
                (lambda x:(x.get('target_doc_fulltext') is None),  RunnablePassthrough(lambda x: logger.info('opensearch failed. fetch fulltext from vectordb.')) | \
                      RunnablePassthrough.assign(target_doc_fulltext=get_doc_fulltext_vectordb_chain)),
                RunnablePassthrough()) |\
        {'target_doc_fulltext':RunnablePick('target_doc_fulltext')}
chain = chain.with_types(input_type=DocFulltextChainInputModel, output_type=DocFulltextChainOutputModel)

if __name__ == '__main__':
    response = chain.invoke({"target_doc_id": "641b3fc8-2738-4a21-b1a0-870e5a3dff2b",  "target_collection_name": "662"})
    print(response['target_doc_fulltext'][:1000])
