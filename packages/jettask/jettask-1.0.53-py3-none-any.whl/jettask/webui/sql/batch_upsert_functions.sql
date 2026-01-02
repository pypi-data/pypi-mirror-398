-- 批量UPSERT函数，用于高效处理分区表的批量插入/更新

-- ========================================
-- 1. 创建临时表类型（用于批量数据传递）
-- ========================================

-- task_runs批量UPSERT函数
CREATE OR REPLACE FUNCTION batch_upsert_task_runs(
    p_records jsonb
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_record jsonb;
BEGIN
    -- 遍历每条记录
    FOR v_record IN SELECT * FROM jsonb_array_elements(p_records)
    LOOP
        -- 先尝试UPDATE
        UPDATE task_runs SET
            consumer_name = COALESCE((v_record->>'consumer_name')::TEXT, consumer_name),
            status = CASE 
                WHEN (v_record->>'status')::TEXT IS NULL THEN status
                WHEN status = 'pending' THEN COALESCE((v_record->>'status')::TEXT, status)
                WHEN status = 'running' AND (v_record->>'status')::TEXT IN ('success', 'failed', 'timeout', 'skipped') THEN (v_record->>'status')::TEXT
                WHEN status IN ('success', 'failed', 'timeout', 'skipped') THEN status
                ELSE COALESCE((v_record->>'status')::TEXT, status)
            END,
            result = CASE
                WHEN status IN ('success', 'failed', 'timeout', 'skipped') AND (v_record->>'status')::TEXT NOT IN ('success', 'failed', 'timeout', 'skipped') THEN result
                ELSE COALESCE((v_record->>'result')::jsonb, result)
            END,
            error_message = CASE
                WHEN status IN ('success', 'failed', 'timeout', 'skipped') AND (v_record->>'status')::TEXT NOT IN ('success', 'failed', 'timeout', 'skipped') THEN error_message
                ELSE COALESCE((v_record->>'error_message')::TEXT, error_message)
            END,
            start_time = COALESCE((v_record->>'started_at')::TIMESTAMPTZ, start_time),
            end_time = CASE
                WHEN status IN ('success', 'failed', 'timeout', 'skipped') AND (v_record->>'status')::TEXT NOT IN ('success', 'failed', 'timeout', 'skipped') THEN end_time
                ELSE COALESCE((v_record->>'completed_at')::TIMESTAMPTZ, end_time)
            END,
            worker_id = COALESCE((v_record->>'worker_id')::TEXT, worker_id),
            duration = COALESCE((v_record->>'duration')::DOUBLE PRECISION, duration),
            execution_time = COALESCE((v_record->>'execution_time')::DOUBLE PRECISION, execution_time),
            updated_at = CURRENT_TIMESTAMP
        WHERE stream_id = (v_record->>'stream_id')::TEXT 
          AND consumer_group = (v_record->>'consumer_group')::TEXT;
        
        -- 如果没有更新到任何行，则INSERT
        IF NOT FOUND THEN
            INSERT INTO task_runs (
                stream_id, task_name, consumer_group, consumer_name, status, result, error_message, 
                start_time, end_time, worker_id, duration, execution_time,
                created_at, updated_at
            ) VALUES (
                (v_record->>'stream_id')::TEXT,
                (v_record->>'task_name')::TEXT,
                (v_record->>'consumer_group')::TEXT,
                (v_record->>'consumer_name')::TEXT,
                COALESCE((v_record->>'status')::TEXT, 'pending'),
                (v_record->>'result')::jsonb,
                (v_record->>'error_message')::TEXT,
                (v_record->>'started_at')::TIMESTAMPTZ,
                (v_record->>'completed_at')::TIMESTAMPTZ,
                (v_record->>'worker_id')::TEXT,
                (v_record->>'duration')::DOUBLE PRECISION,
                (v_record->>'execution_time')::DOUBLE PRECISION,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
        END IF;
        
        v_count := v_count + 1;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 2. 批量插入tasks的优化函数
-- ========================================

CREATE OR REPLACE FUNCTION batch_insert_tasks(
    p_records jsonb
) RETURNS INTEGER AS $$
DECLARE
    v_inserted INTEGER;
BEGIN
    -- 使用单个INSERT语句批量插入，忽略冲突
    WITH data AS (
        SELECT 
            (value->>'stream_id')::TEXT as stream_id,
            (value->>'queue')::TEXT as queue,
            (value->>'namespace')::TEXT as namespace,
            (value->>'scheduled_task_id')::TEXT as scheduled_task_id,
            (value->>'payload')::jsonb as payload,
            (value->>'priority')::INTEGER as priority,
            (value->>'created_at')::TIMESTAMPTZ as created_at,
            (value->>'source')::TEXT as source,
            (value->>'metadata')::jsonb as metadata
        FROM jsonb_array_elements(p_records)
    )
    INSERT INTO tasks (stream_id, queue, namespace, scheduled_task_id, payload, priority, created_at, source, metadata)
    SELECT * FROM data
    ON CONFLICT DO NOTHING;
    
    GET DIAGNOSTICS v_inserted = ROW_COUNT;
    RETURN v_inserted;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 3. 创建索引以加速批量操作
-- ========================================

-- 为task_runs的UPSERT操作创建覆盖索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_task_runs_upsert 
ON task_runs (stream_id, consumer_group) 
INCLUDE (status, updated_at);

-- ========================================
-- 4. 优化的批量清理函数
-- ========================================

CREATE OR REPLACE FUNCTION cleanup_completed_tasks(
    p_stream_ids TEXT[]
) RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    -- 批量删除已完成的任务
    DELETE FROM task_runs 
    WHERE stream_id = ANY(p_stream_ids)
      AND status IN ('success', 'failed', 'timeout', 'skipped', 'cancelled');
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 使用示例
-- ========================================

/*
-- Python中使用示例：

# 批量UPSERT task_runs
records = [
    {
        'stream_id': '123-0',
        'task_name': 'my_task',
        'consumer_group': 'group1',
        'status': 'success',
        ...
    },
    ...
]

query = text("SELECT batch_upsert_task_runs(:records)")
result = await session.execute(query, {'records': json.dumps(records)})
count = result.scalar()

# 批量插入tasks
tasks = [
    {
        'stream_id': '123-0',
        'queue': 'default',
        'namespace': 'default',
        ...
    },
    ...
]

query = text("SELECT batch_insert_tasks(:tasks)")
result = await session.execute(query, {'tasks': json.dumps(tasks)})
inserted = result.scalar()
*/