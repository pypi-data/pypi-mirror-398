"""
Redis Stream积压监控模块
用于监控任务队列的积压情况
"""

import asyncio
import redis.asyncio as redis
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

logger = logging.getLogger(__name__)


class StreamBacklogMonitor:
    """Stream积压监控器"""
    
    def __init__(self, redis_url: str = None, pg_url: str = None, redis_prefix: str = "JETTASK"):
        self.redis_url = redis_url or os.getenv('JETTASK_REDIS_URL', 'redis://localhost:6379/0')
        self.pg_url = pg_url or os.getenv('JETTASK_PG_URL', 'postgresql+asyncpg://jettask:123456@localhost:5432/jettask')
        self.redis_prefix = redis_prefix
        
        self.redis_client = None
        self.engine = None
        self.AsyncSessionLocal = None
        
    async def initialize(self):
        from jettask.db.connector import get_async_redis_client

        self.redis_client = get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=True
        )

        self.engine = create_async_engine(self.pg_url, echo=False)
        self.AsyncSessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
        if self.engine:
            await self.engine.dispose()
    
    async def update_delivered_offset(self, stream_name: str, group_name: str, messages: List[Tuple]):
        if not messages:
            return
            
        try:
            max_offset = 0
            for _, msg_list in messages:
                for msg_id, msg_data in msg_list:
                    if b'offset' in msg_data:
                        offset = int(msg_data[b'offset'])
                        max_offset = max(max_offset, offset)
            
            if max_offset > 0:
                key = f"{self.redis_prefix}:GROUP:{stream_name}:{group_name}:last_delivered_offset"
                
                lua_script = """
                local current = redis.call('GET', KEYS[1])
                if not current or tonumber(ARGV[1]) > tonumber(current) then
                    redis.call('SET', KEYS[1], ARGV[1])
                end
                return redis.call('GET', KEYS[1])
                """
                
                await self.redis_client.eval(lua_script, 1, key, str(max_offset))
                logger.debug(f"Updated delivered offset for {stream_name}:{group_name} to {max_offset}")
                
        except Exception as e:
            logger.error(f"Failed to update delivered offset: {e}")
    
    async def update_acked_offset(self, stream_name: str, group_name: str, acked_messages: List):
        if not acked_messages:
            return
            
        try:
            max_offset = 0
            for msg in acked_messages:
                if 'offset' in msg:
                    offset = int(msg['offset'])
                    max_offset = max(max_offset, offset)
            
            if max_offset > 0:
                key = f"{self.redis_prefix}:GROUP:{stream_name}:{group_name}:last_acked_offset"
                
                lua_script = """
                local current = redis.call('GET', KEYS[1])
                if not current or tonumber(ARGV[1]) > tonumber(current) then
                    redis.call('SET', KEYS[1], ARGV[1])
                end
                return redis.call('GET', KEYS[1])
                """
                
                await self.redis_client.eval(lua_script, 1, key, str(max_offset))
                logger.debug(f"Updated acked offset for {stream_name}:{group_name} to {max_offset}")
                
        except Exception as e:
            logger.error(f"Failed to update acked offset: {e}")
    
    async def collect_metrics(self, namespace: str = "default", stream_names: List[str] = None) -> Dict:
        metrics = {}
        
        try:
            queue_offsets_key = f"{namespace}:QUEUE_OFFSETS"
            queue_offsets = await self.redis_client.hgetall(queue_offsets_key)
            
            task_offsets_key = f"{namespace}:TASK_OFFSETS"
            task_offsets = await self.redis_client.hgetall(task_offsets_key)
            
            if not stream_names:
                stream_names = list(queue_offsets.keys())
            
            for stream_name in stream_names:
                stream_key = f"{self.redis_prefix.lower()}:QUEUE:{stream_name}"
                
                last_published_offset = int(queue_offsets.get(stream_name, 0))
                
                try:
                    stream_info = await self.redis_client.xinfo_stream(stream_key)
                except:
                    continue
                
                try:
                    groups = await self.redis_client.xinfo_groups(stream_key)
                except:
                    groups = []
                
                stream_metrics = {
                    'namespace': namespace,
                    'stream_name': stream_name,
                    'last_published_offset': last_published_offset,
                    'groups': {}
                }
                
                for group in groups:
                    group_name = group['name']
                    pending_count = group['pending']  

                    task_name = group_name.split(':')[-1]
                    task_offset_key = f"{stream_name}:{task_name}"
                    last_acked_offset = int(task_offsets.get(task_offset_key, 0))
                    total_backlog = max(0, last_published_offset - last_acked_offset)
                    
                    backlog_undelivered = max(0, total_backlog - pending_count)
                    
                    backlog_delivered_unacked = pending_count
                    
                    last_delivered_offset = last_acked_offset + pending_count
                    
                    stream_metrics['groups'][group_name] = {
                        'last_delivered_offset': last_delivered_offset,  
                        'last_acked_offset': last_acked_offset,          
                        'pending_count': pending_count,                  
                        'backlog_undelivered': backlog_undelivered,      
                        'backlog_delivered_unacked': backlog_delivered_unacked,  
                        'backlog_unprocessed': total_backlog            
                    }
                
                if not stream_metrics['groups'] and last_published_offset > 0:
                    stream_metrics['groups']['_total'] = {
                        'last_delivered_offset': 0,
                        'last_acked_offset': 0,
                        'pending_count': 0,
                        'backlog_undelivered': last_published_offset,
                        'backlog_unprocessed': last_published_offset
                    }
                
                metrics[stream_name] = stream_metrics
                
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            import traceback
            traceback.print_exc()
            
        return metrics
    
    async def save_metrics(self, metrics: Dict):
        if not metrics:
            return
            
        try:
            async with self.AsyncSessionLocal() as session:
                records = []
                timestamp = datetime.now(timezone.utc)
                
                for stream_name, stream_data in metrics.items():
                    for group_name, group_data in stream_data.get('groups', {}).items():
                        record = {
                            'namespace': stream_data['namespace'],
                            'stream_name': stream_name,
                            'consumer_group': group_name,
                            'last_published_offset': stream_data['last_published_offset'],
                            'last_delivered_offset': group_data['last_delivered_offset'],
                            'last_acked_offset': group_data['last_acked_offset'],
                            'pending_count': group_data['pending_count'],
                            'backlog_undelivered': group_data['backlog_undelivered'],
                            'backlog_unprocessed': group_data['backlog_unprocessed'],
                            'backlog_delivered_unacked': group_data.get('backlog_delivered_unacked', group_data['pending_count']),
                            'created_at': timestamp
                        }
                        records.append(record)
                    
                    if not stream_data.get('groups'):
                        record = {
                            'namespace': stream_data['namespace'],
                            'stream_name': stream_name,
                            'consumer_group': None,
                            'last_published_offset': stream_data['last_published_offset'],
                            'last_delivered_offset': 0,
                            'last_acked_offset': 0,
                            'pending_count': 0,
                            'backlog_undelivered': stream_data['last_published_offset'],
                            'backlog_unprocessed': stream_data['last_published_offset'],
                            'created_at': timestamp
                        }
                        records.append(record)
                
                if records:
                    insert_sql = text("""
                        INSERT INTO stream_backlog_monitor 
                        (namespace, stream_name, consumer_group, last_published_offset, 
                         last_delivered_offset, last_acked_offset, pending_count,
                         backlog_undelivered, backlog_unprocessed, created_at)
                        VALUES 
                        (:namespace, :stream_name, :consumer_group, :last_published_offset,
                         :last_delivered_offset, :last_acked_offset, :pending_count,
                         :backlog_undelivered, :backlog_unprocessed, :created_at)
                    """)
                    
                    await session.execute(insert_sql, records)
                    await session.commit()
                    logger.info(f"Saved {len(records)} monitoring records")
                    
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def run_collector(self, interval: int = 60):
        await self.initialize()
        
        logger.info(f"Starting backlog monitor collector with {interval}s interval")
        
        try:
            while True:
                try:
                    metrics = await self.collect_metrics()
                    
                    await self.save_metrics(metrics)
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Collector error: {e}")
                    await asyncio.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("Stopping collector...")
        finally:
            await self.close()

async def report_delivered_offset(redis_client, redis_prefix: str, queue: str, group_name: str, messages: List):
    pass  

async def report_queue_offset(redis_client, redis_prefix: str, queue: str, offset: int):
    pass  

if __name__ == "__main__":
    monitor = StreamBacklogMonitor()
    asyncio.run(monitor.run_collector(interval=30))