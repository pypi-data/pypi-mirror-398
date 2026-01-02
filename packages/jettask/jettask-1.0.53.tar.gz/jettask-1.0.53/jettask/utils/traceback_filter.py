"""
过滤框架层堆栈信息的工具函数
"""
import traceback
import sys
from typing import Optional


def filter_framework_traceback(exc_type=None, exc_value=None, exc_traceback=None) -> str:
    if exc_type is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
    
    if exc_traceback is None:
        return "No traceback available"
    
    framework_paths = [
        '/jettask/executors/',
        '/jettask/core/',
        '/jettask/monitoring/',
        '/jettask/utils/',
        'asyncio/',
        'concurrent/',
        'multiprocessing/',
    ]
    
    tb_frames = []
    tb = exc_traceback
    
    business_frames = []
    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        
        is_framework = any(path in filename for path in framework_paths)
        
        if not is_framework:
            business_frames.append(tb)
        
        tb = tb.tb_next
    
    if business_frames:
        lines = []
        for tb in business_frames:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            lineno = tb.tb_lineno
            name = frame.f_code.co_name
            
            lines.append(f'  File "{filename}", line {lineno}, in {name}\n')
            
            try:
                import linecache
                line = linecache.getline(filename, lineno, frame.f_globals)
                if line:
                    lines.append(f'    {line.strip()}\n')
            except:
                pass
        
        if lines:
            result = "Traceback (most recent call last):\n"
            result += "".join(lines)
            result += f"{exc_type.__name__}: {exc_value}"
            return result
    
    return f"{exc_type.__name__}: {exc_value}"


def get_clean_exception_message() -> str:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    if exc_type is None:
        return "No exception"
    
    if exc_value:
        return f"{exc_type.__name__}: {exc_value}"
    
    return f"{exc_type.__name__}"