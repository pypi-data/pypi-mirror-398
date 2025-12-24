"""
JetTask 系统常量定义

集中管理所有系统级别的常量配置，包括：
- 内部消费者组
- 系统保留关键字
- 默认配置值
- 其他常量
"""


INTERNAL_CONSUMER_PREFIXES = [
    'pg_consumer_',      
    'webui_consumer_',   
    'monitor_',          
    'system_',           
    '_internal_',        
    '__',                
]

INTERNAL_CONSUMER_NAMES = [
    'pg_consumer',       
    'webui_consumer',    
    'system',            
]



def is_internal_consumer(consumer_group: str) -> bool:
    if not consumer_group:
        return False
    
    consumer_group_lower = consumer_group.lower()
    
    for name in INTERNAL_CONSUMER_NAMES:
        if consumer_group_lower == name.lower():
            return True
    
    for prefix in INTERNAL_CONSUMER_PREFIXES:
        if consumer_group_lower.startswith(prefix.lower()):
            return True
    
    internal_keywords = [
        'pg_consumer',      
        'webui_consumer',   
    ]
    
    for keyword in internal_keywords:
        if keyword in consumer_group_lower:
            return True
    
    return False
