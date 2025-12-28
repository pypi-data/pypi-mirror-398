"""
chains 模块的公共工具函数
"""
import traceback
from utils import logger, exceptions
from framebase.notices import RunnableNotice
from langchain_core.runnables import chain as chain_decorator
from openai._exceptions import OpenAIError, RateLimitError, InternalServerError, APIConnectionError, APITimeoutError
from utils.exceptions import LLMCallError, LLMCallTimeoutError, LLMRateLimitError, format_error_response
from utils.dbs import set_thought


@chain_decorator
async def throw_exception(inputs, config):
    """
    公共异常处理函数
    处理各种类型的异常并转换为统一的错误响应格式
    """
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
