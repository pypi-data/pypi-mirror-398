-- JetTask PostgreSQL Schema
-- 用于存储任务队列信息和执行结果

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(255) PRIMARY KEY,  -- Redis Stream的事件ID
    queue_name VARCHAR(255) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    task_data JSONB,  -- 任务的原始数据
    priority INTEGER DEFAULT 0,
    delay DOUBLE PRECISION DEFAULT 0,  -- 任务延迟执行时间（秒）
    retry_count INTEGER DEFAULT 0,
    max_retry INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, success, failed, timeout
    result JSONB,  -- 执行结果
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    worker_id VARCHAR(255),
    execution_time DOUBLE PRECISION,  -- 任务执行时间（秒）
    duration DOUBLE PRECISION,  -- 任务总持续时间（秒）
    metadata JSONB  -- 额外的元数据
);

-- 创建优化索引
CREATE INDEX IF NOT EXISTS idx_tasks_queue_name ON tasks(queue_name);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
-- 组合索引：优化按队列和状态查询
CREATE INDEX IF NOT EXISTS idx_tasks_queue_status ON tasks(queue_name, status);
-- 时间索引：优化时间范围查询
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
-- Worker索引：优化查询特定worker的任务（部分索引，只为非空值创建）
CREATE INDEX IF NOT EXISTS idx_tasks_worker_id ON tasks(worker_id) WHERE worker_id IS NOT NULL;

-- 升级脚本：为现有表添加新字段（如果不存在）
DO $$
BEGIN
    -- 添加延迟字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'tasks' AND column_name = 'delay') THEN
        ALTER TABLE tasks ADD COLUMN delay DOUBLE PRECISION DEFAULT 0;
    END IF;

    -- 添加执行时间字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'tasks' AND column_name = 'execution_time') THEN
        ALTER TABLE tasks ADD COLUMN execution_time DOUBLE PRECISION;
    END IF;

    -- 添加持续时间字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'tasks' AND column_name = 'duration') THEN
        ALTER TABLE tasks ADD COLUMN duration DOUBLE PRECISION;
    END IF;
    
    -- 删除不再使用的字段
    -- 删除 next_sync_time（如果存在）
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'tasks' AND column_name = 'next_sync_time') THEN
        ALTER TABLE tasks DROP COLUMN next_sync_time;
    END IF;
    
    -- 删除 sync_check_count（如果存在）
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'tasks' AND column_name = 'sync_check_count') THEN
        ALTER TABLE tasks DROP COLUMN sync_check_count;
    END IF;
    
    -- 删除 last_checked_at（如果存在）
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'tasks' AND column_name = 'last_checked_at') THEN
        ALTER TABLE tasks DROP COLUMN last_checked_at;
    END IF;
    
    -- 删除 sync_node_id（如果存在）
    IF EXISTS (SELECT 1 FROM information_schema.columns 
              WHERE table_name = 'tasks' AND column_name = 'sync_node_id') THEN
        ALTER TABLE tasks DROP COLUMN sync_node_id;
    END IF;
END$$;

-- 删除旧的不再需要的索引
DROP INDEX IF EXISTS idx_tasks_status_last_checked;
DROP INDEX IF EXISTS idx_tasks_status_created;
DROP INDEX IF EXISTS idx_tasks_hash_partition;
DROP INDEX IF EXISTS idx_tasks_status_next_sync;
DROP INDEX IF EXISTS idx_tasks_new_tasks;
DROP INDEX IF EXISTS idx_tasks_id_partition;
DROP INDEX IF EXISTS idx_tasks_covering_sync;

-- 确保新索引存在（如果表已存在但索引不存在，则创建）
DO $$
BEGIN
    -- 检查并创建组合索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                  WHERE tablename = 'tasks' AND indexname = 'idx_tasks_queue_status') THEN
        CREATE INDEX idx_tasks_queue_status ON tasks(queue_name, status);
    END IF;
    
    -- 检查并创建时间索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                  WHERE tablename = 'tasks' AND indexname = 'idx_tasks_created_at') THEN
        CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
    END IF;
    
    -- 检查并创建worker索引
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                  WHERE tablename = 'tasks' AND indexname = 'idx_tasks_worker_id') THEN
        CREATE INDEX idx_tasks_worker_id ON tasks(worker_id) WHERE worker_id IS NOT NULL;
    END IF;
END$$;

-- queue_stats 和 workers 表已废弃，不再创建