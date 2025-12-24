#!/usr/bin/env python3
"""
Stream积压监控采集服务
可以作为独立服务运行，定期采集Redis Stream的积压情况
"""

import asyncio
import argparse
import logging
import signal
import sys
from .stream_backlog import StreamBacklogMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(args):
    monitor = StreamBacklogMonitor(
        redis_url=args.redis_url,
        pg_url=args.pg_url,
        redis_prefix=args.redis_prefix
    )
    
    def signal_handler(sig, frame):
        logger.info("Received stop signal, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Starting backlog collector service...")
    logger.info(f"  Redis URL: {args.redis_url}")
    logger.info(f"  PostgreSQL URL: {args.pg_url}")
    logger.info(f"  Redis Prefix: {args.redis_prefix}")
    logger.info(f"  Collection Interval: {args.interval} seconds")
    
    try:
        await monitor.run_collector(interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")
    except Exception as e:
        logger.error(f"Collector failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redis Stream Backlog Monitor Collector")
    
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/0",
        help="Redis connection URL (default: redis://localhost:6379/0)"
    )
    
    parser.add_argument(
        "--pg-url",
        default="postgresql+asyncpg://jettask:123456@localhost:5432/jettask",
        help="PostgreSQL connection URL"
    )
    
    parser.add_argument(
        "--redis-prefix",
        default="JETTASK",
        help="Redis key prefix (default: JETTASK)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Collection interval in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    asyncio.run(main(args))