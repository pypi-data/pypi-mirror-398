# cython: annotation_typing = False
from langchain_core.runnables import RunnableSequence
from framebase.docstores import save_to_vs, save_to_minio, save_to_os, save_summary
from .protocol import SaveChainInputModel

inputs = {
        "docs": lambda x: x["docs"],
        'kb_id': lambda x: x["kb_id"],
        'org': lambda x:x.get('org',[-1]),
        'tags': lambda x:x.get('tags',[[-1]]),
        'custom_tags': lambda x:x.get('custom_tags',[[-1]]),
        'doc_id': lambda x:x.get('doc_id'),
        'to_opensearch': lambda x:x.get('to_opensearch',False),
        'loader_result': lambda x:x.get('loader_result',{}),
        'keyinfo':lambda x:x.get('keyinfo',{}),
        'origin_file_name':  lambda x:x.get('origin_file_name', None)
        }

save_with_summary_chain = RunnableSequence(inputs , {'vectorstore':save_to_minio | save_to_vs | save_summary,'opensearch':save_to_os })
save_chain = RunnableSequence(inputs , {'vectorstore':save_to_minio | save_to_vs,'opensearch':save_to_os })
save_chain = save_chain.with_types(input_type=SaveChainInputModel,output_type=None)
