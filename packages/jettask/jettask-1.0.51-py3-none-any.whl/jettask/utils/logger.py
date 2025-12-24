"""
任务日志工具
"""
import logging


def get_task_logger(name: str = None) -> logging.Logger:
    if name is None:
        name = 'jettask.task'
    elif not name.startswith('jettask.'):
        name = f'jettask.task.{name}'
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger