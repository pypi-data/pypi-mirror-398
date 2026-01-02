"""
日志处理工具模块
提供统一的日志输出功能，便于调试和问题追踪
"""
import inspect
import traceback
import datetime
import logging
import uuid
from typing import Any


def console_log_debug(*args: Any, onException: bool = False) -> None:
    """
    标准的打印函数，输出时间、内容、调用的文件和函数
    
    Args:
        *args: 要打印的消息内容，可以是多个参数
        onException (bool): 是否在异常处理流程中调用，默认为False
        
    Example:
        >>> console_log_debug("这是一条调试信息", "变量值:", variable)
        >>> try:
        ...     # 一些可能出错的代码
        ...     pass
        ... except Exception:
        ...     console_log_debug("发生异常", onException=True)
    """
    # 获取调用者信息
    caller = inspect.currentframe().f_back
    caller_name = caller.f_code.co_name
    caller_filename = caller.f_code.co_filename
    caller_lineno = caller.f_lineno  # 获取调用的行号
    
    # 格式化当前时间
    log_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    # 生成一段uuid用于追踪日志
    log_uuid = uuid.uuid4()
    
    # 格式化消息内容
    show_message = "\n".join([f"【{log_uuid}】-{index}：{message_item}" for index, message_item in enumerate(args,start=1)])

    # 输出日志信息
    print(f'【{log_uuid}】{log_time} - {caller_filename} - {caller_name} - line:{caller_lineno}')
    print(show_message)
    
    # 如果是在异常处理流程中，则打印堆栈信息
    if onException:
        print("捕获异常上下文，以下是堆栈信息：")
        traceback.print_exc()
        
    print("")