-- 重命名 scheduled_until 为 next_trigger_time
-- 这个字段现在表示"下次触发时间"，而不是"已调度到的时间"

-- 1. 重命名列
ALTER TABLE scheduled_tasks RENAME COLUMN scheduled_until TO next_trigger_time;

-- 2. 更新列注释
COMMENT ON COLUMN scheduled_tasks.next_trigger_time IS '下次触发时间（调度器应该发送任务的时间，可能提前于next_run_time）';

-- 3. 更新 next_run_time 的注释
COMMENT ON COLUMN scheduled_tasks.next_run_time IS '下次执行时间（任务真正应该执行的时间）';

-- 4. 清空现有的 next_trigger_time 值（之前的 scheduled_until 逻辑不同）
-- 这些值会在任务下次被调度时重新计算
UPDATE scheduled_tasks SET next_trigger_time = NULL WHERE next_trigger_time IS NOT NULL;
