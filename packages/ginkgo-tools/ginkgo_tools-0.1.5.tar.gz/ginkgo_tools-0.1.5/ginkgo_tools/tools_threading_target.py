"""
多线程任务处理模块
负责生成所有异步操作对象的实例化，提供线程任务管理和队列控制功能
"""
import threading
import time
import os
from typing import Any, Dict, Optional
from .tools_log import console_log_debug


class Base_Operation_Threading_Target(threading.Thread):
    """
    异步任务对象基类
    
    负责生成所有异步操作对象的实例化，非常重要，
    原则上只会被线程管理器调用生成实例对象
    """
    
    def __init__(self, the_target: Any, operation_dict: Dict[str, Any]) -> None:
        """
        初始化异步任务对象
        
        Args:
            the_target: 任务目标对象
            operation_dict (Dict[str, Any]): 操作参数字典
        """
        threading.Thread.__init__(self)  # 异步对象较为特殊，必须在构造函数中声明Thread初始化
        self.id = operation_dict.get("operation_hash", "")
        self.the_target = the_target
        self.operation_type = operation_dict.get("operation_type", "")
        self.operation_dict = operation_dict
        self.queue_manage: Optional[Any] = False  # 队列管理对象
        console_log_debug("完成异步操作对象实例化，待触发，初始化参数：", self.operation_type, self.operation_dict)

    def queue_taskdone(self) -> None:
        """
        队列计数减法
        
        无论run成功与否，执行该函数(自带queue检测，直接运行即可)
        """
        if self.queue_manage:  # 如果这个函数是有队列控制的话，执行计数减法和队列删除
            # 队列计数减法
            self.queue_manage.task_done()  # 将任务队列的任务完成计数-1，为0时，queue.join才会放通，如果不写，会一直卡死
            # 队列取出操作要加超时参数，不然的话如果队列为空，这里也会挂住
            try:
                self.queue_manage.get(timeout=0)
            except Exception:
                # 队列为空时的异常处理
                pass

    def queue_reloadin(self) -> None:
        """
        队列重录
        
        当该任务不满足运行条件的时候，可以调用此函数重新排队
        （但是必须保证队列计数要处理！）
        """
        src_operation_dict = self.operation_dict.copy()  # 创建副本避免修改原字典
        src_operation_dict.pop("operation_hash", None)  # 消费者获取任务时，会增加hash作为key，这里删掉，恢复成初始operation_dict
        # thread_queue_manage_producer.producer_convention_operation_queue(src_operation_dict)