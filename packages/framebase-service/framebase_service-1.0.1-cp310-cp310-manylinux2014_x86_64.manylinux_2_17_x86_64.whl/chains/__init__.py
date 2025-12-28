from .loader_splitter_chain import chain as loader_splitter_chain
from .save_chain import save_chain
from .retriever_chain import multi_kbs_retrieve_chain as retriever_chain
from .conversation_chain import chain as conversation_chain
from .related_questions_chain import chain as related_questions_chain
from .clarify_chain import chain as clarify_chain
from .chat_assistant_chain import chain as chat_assistant_chain
from .model_connect_chain import model_connect_test_chain as model_connect_chain
from .text2metric_chain import chain_without_conversation as text2metric_chain
from .metric_template_analysis_chain import metric_template_recommend_question_chain

chains={
    'loader_splitter_chain':loader_splitter_chain,
    'vectorstore_chain':save_chain,
    'retriever_chain':retriever_chain
}
