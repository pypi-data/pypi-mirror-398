-- JetTask 数据库结构验证脚本
-- 用于验证数据库表结构是否正确

-- 检查所有表是否存在
SELECT 
    'namespaces' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'namespaces') as exists
UNION ALL
SELECT 
    'scheduled_tasks' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'scheduled_tasks') as exists
UNION ALL
SELECT 
    'tasks' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') as exists
UNION ALL
SELECT 
    'task_runs' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'task_runs') as exists
UNION ALL
SELECT 
    'stream_backlog_monitor' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'stream_backlog_monitor') as exists
UNION ALL
SELECT 
    'alert_rules' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'alert_rules') as exists
UNION ALL
SELECT 
    'alert_history' as table_name,
    EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'alert_history') as exists;

-- 检查 namespaces 表的关键列
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'namespaces' 
AND column_name IN ('id', 'name', 'redis_config', 'pg_config', 'version', 'is_active')
ORDER BY ordinal_position;

-- 检查索引
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('namespaces', 'scheduled_tasks', 'tasks', 'task_runs', 'alert_rules', 'alert_history')
ORDER BY tablename, indexname;

-- 检查分区表
SELECT 
    parent.relname AS parent_table,
    child.relname AS partition_name,
    pg_get_expr(child.relpartbound, child.oid, true) AS partition_expression
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child ON pg_inherits.inhrelid = child.oid
WHERE parent.relname IN ('tasks', 'task_runs', 'stream_backlog_monitor')
ORDER BY parent.relname, child.relname;

-- 检查触发器
SELECT 
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;