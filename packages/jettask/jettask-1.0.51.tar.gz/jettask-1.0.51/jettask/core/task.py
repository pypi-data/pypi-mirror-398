from ..utils.serializer import dumps_str, loads_str
import inspect
from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING, get_type_hints, Union

if TYPE_CHECKING:
    from .app import Jettask

from .context import TaskContext


@dataclass
class ExecuteResponse:
    delay: Optional[float] = None 
    urgent_retry: bool = False 
    reject: bool = False
    retry_time: Optional[float] = None


class Request:
    id: str = None
    name: str = None
    app: "Jettask" = None

    def __init__(self, *args, **kwargs) -> None:
        self._update(*args, **kwargs)

    def _update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)


class Task:
    _app: "Jettask" = None
    name: str = None
    queue: str = None
    trigger_time: float = None
    retry_config: Optional[dict] = None  

    def __call__(self, event_id: str, trigger_time: float, queue: str,
                 group_name: Optional[str] = None,
                 scheduled_task_id: Optional[int] = None,
                 metadata: Optional[dict] = None,
                 *args: Any, **kwds: Any) -> Any:
        injected_args, injected_kwargs = self._inject_dependencies(
            event_id, trigger_time, queue, group_name, scheduled_task_id, metadata, args, kwds
        )
        return self.run(*injected_args, **injected_kwargs)

    def _inject_dependencies(self, event_id: str, trigger_time: float, queue: str,
                            group_name: Optional[str], scheduled_task_id: Optional[int],
                            metadata: Optional[dict],
                            args: tuple, kwargs: dict) -> tuple:
        import logging
        logger = logging.getLogger(__name__)

        try:
            sig = inspect.signature(self.run)
            type_hints = get_type_hints(self.run)
            logger.debug(f"[TaskContext注入] 任务 {self.name} - 签名: {sig}, 类型提示: {type_hints}")
        except (ValueError, TypeError, NameError) as e:
            logger.warning(f"[TaskContext注入] 任务 {self.name} - 获取签名失败: {e}")
            return args, kwargs
        
        context = TaskContext(
            event_id=event_id,
            name=self.name,
            trigger_time=trigger_time,
            app=self._app,
            queue=queue,  
            scheduled_task_id=scheduled_task_id,  
            group_name=group_name,  
            metadata=metadata or {},  
        )
        
        params_list = list(sig.parameters.items())
        final_args = []
        final_kwargs = dict(kwargs)  
        args_list = list(args)
        args_consumed = 0  
        
        for idx, (param_name, param) in enumerate(params_list):
            if param_name == 'self':
                continue
            
            param_type = type_hints.get(param_name)
            
            if param.kind == param.KEYWORD_ONLY:
                if param_type is TaskContext and param_name not in final_kwargs:
                    final_kwargs[param_name] = context
                continue
            
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                if param_type is TaskContext:
                    final_args.append(context)
                elif param_name in final_kwargs:
                    continue
                elif args_consumed < len(args_list):
                    final_args.append(args_list[args_consumed])
                    args_consumed += 1
                else:
                    break
        
        if args_consumed < len(args_list):
            final_args.extend(args_list[args_consumed:])

        logger.debug(f"[TaskContext注入] 任务 {self.name} - 注入后参数: args={final_args}, kwargs={list(final_kwargs.keys())}")

        return tuple(final_args), final_kwargs

    def run(self, *args, **kwargs):
        raise NotImplementedError("Tasks must define the run method.")

    @classmethod
    def bind_app(cls, app):
        cls._app = app

    @property
    def is_wildcard_queue(self) -> bool:
        from ..utils.queue_matcher import is_wildcard_pattern

        if not self.queue:
            return False

        return is_wildcard_pattern(self.queue)


    def on_before(self, event_id, pedding_count, args, kwargs) -> ExecuteResponse:
        return ExecuteResponse()

    def on_end(self, event_id, pedding_count, args, kwargs, result) -> ExecuteResponse:
        return ExecuteResponse()

    def on_success(self, event_id, args, kwargs, result) -> ExecuteResponse:
        return ExecuteResponse()

    def read_pending(
        self,
        queue: str = None,
        asyncio: bool = False,
    ):
        queue = queue or self.queue
        if asyncio:
            return self._get_pending(queue)
        return self._app.ep.read_pending(queue, queue)

    async def _get_pending(self, queue: str):
        return await self._app.ep.read_pending(queue, queue, asyncio=True)

