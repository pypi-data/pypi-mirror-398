"""数据库初始化工具 - 支持分区表和优化索引"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器 - 支持分区表"""

    def __init__(self, pg_config):
        self.pg_config = pg_config
        self.schema_path = Path(__file__).parent / "sql" / "init_database.sql"
        
    async def test_connection(self) -> bool:
        try:
            logger.info(f"正在测试数据库连接: {self.pg_config.host}:{self.pg_config.port}/{self.pg_config.database}")
            conn = await asyncpg.connect(self.pg_config.dsn)
            await conn.close()
            
            logger.info("✓ 数据库连接成功")
            return True
            
        except Exception as e:
            logger.error(f"✗ 数据库连接失败: {e}")
            return False
            
    async def create_database(self) -> bool:
        try:
            admin_dsn = f"postgresql://{self.pg_config.user}:{self.pg_config.password}@{self.pg_config.host}:{self.pg_config.port}/postgres"
            conn = await asyncpg.connect(admin_dsn)
            
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
                self.pg_config.database
            )
            
            if not exists:
                logger.info(f"正在创建数据库: {self.pg_config.database}")
                await conn.execute(f'CREATE DATABASE "{self.pg_config.database}"')
                logger.info("✓ 数据库创建成功")
            else:
                logger.info(f"✓ 数据库已存在: {self.pg_config.database}")
                
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"✗ 创建数据库失败: {e}")
            logger.info("请确保您有创建数据库的权限，或手动创建数据库")
            return False
            
    async def init_schema(self) -> bool:
        try:
            if not self.schema_path.exists():
                logger.error(f"✗ Schema文件不存在: {self.schema_path}")
                return False
                
            logger.info("正在读取schema文件...")
            schema_sql = self.schema_path.read_text()
            
            logger.info("正在初始化数据库表结构...")
            conn = await asyncpg.connect(self.pg_config.dsn)
            
            def split_sql_statements(sql_text):
                statements = []
                current_statement = []
                in_dollar_quote = False
                
                lines = sql_text.split('\n')
                for line in lines:
                    if line.strip().startswith('--') and not in_dollar_quote:
                        continue
                    
                    current_statement.append(line)
                    
                    if '$$' in line:
                        dollar_count = line.count('$$')
                        if dollar_count % 2 == 1:  
                            in_dollar_quote = not in_dollar_quote
                    
                    if not in_dollar_quote and line.rstrip().endswith(';'):
                        statement = '\n'.join(current_statement).strip()
                        if statement and not statement.startswith('--'):
                            statements.append(statement)
                        current_statement = []
                
                if current_statement:
                    statement = '\n'.join(current_statement).strip()
                    if statement and not statement.startswith('--'):
                        statements.append(statement)
                
                return statements
            
            statements = split_sql_statements(schema_sql)
            
            for i, statement in enumerate(statements, 1):
                if not statement:
                    continue
                    
                try:
                    if 'RAISE NOTICE' in statement and not 'CREATE' in statement:
                        logger.info("跳过独立的 RAISE NOTICE 语句")
                        continue
                        
                    await conn.execute(statement)
                    
                    if 'CREATE TABLE' in statement:
                        if 'PARTITION BY' in statement:
                            table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().split(' ')[0]
                            logger.info(f"  ✓ 创建分区表: {table_name}")
                        else:
                            table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip().split(' ')[0]
                            logger.info(f"  ✓ 创建表: {table_name}")
                    elif 'CREATE INDEX' in statement:
                        index_parts = statement.split('CREATE INDEX')[1].split('ON')[0].strip().split(' ')
                        index_name = index_parts[-1] if index_parts else 'unknown'
                        logger.info(f"  ✓ 创建索引: {index_name}")
                    elif 'CREATE' in statement and 'FUNCTION' in statement:
                        func_parts = statement.split('FUNCTION')[1].split('(')[0].strip().split(' ')
                        func_name = func_parts[-1] if func_parts else 'unknown'
                        logger.info(f"  ✓ 创建函数: {func_name}")
                    elif 'SELECT' in statement and 'partition' in statement.lower():
                        logger.info(f"  ✓ 执行分区创建")
                        
                except Exception as e:
                    stmt_preview = statement[:200] if len(statement) > 200 else statement
                    logger.warning(f"  语句 {i} 执行警告: {str(e)[:100]}")
            
            tables = await conn.fetch("""
                SELECT tablename, 
                       CASE 
                           WHEN c.relkind = 'p' THEN 'partitioned'
                           WHEN p.inhrelid IS NOT NULL THEN 'partition'
                           ELSE 'regular'
                       END as table_type
                FROM pg_tables t
                LEFT JOIN pg_class c ON c.relname = t.tablename AND c.relnamespace = 'public'::regnamespace
                LEFT JOIN pg_inherits p ON p.inhrelid = c.oid
                WHERE schemaname = 'public' 
                AND (tablename IN ('tasks', 'task_runs', 'scheduled_tasks', 'namespaces', 
                                   'stream_backlog_monitor', 'alert_rules', 'alert_history')
                     OR tablename LIKE 'tasks_%' 
                     OR tablename LIKE 'task_runs_%'
                     OR tablename LIKE 'stream_backlog_monitor_%')
                ORDER BY tablename
            """)
            
            created_tables = [row['tablename'] for row in tables]
            
            logger.info("")
            logger.info("=" * 50)
            logger.info("✓ 成功创建的表:")
            
            main_tables = []
            partition_tables = []
            
            for table in created_tables:
                if '_2025_' in table or '_2024_' in table or '_2026_' in table:
                    partition_tables.append(table)
                else:
                    main_tables.append(table)
            
            logger.info(f"  主表: {', '.join(main_tables)}")
            if partition_tables:
                logger.info(f"  分区: {', '.join(partition_tables)}")
            
            logger.info("")
            logger.info("表数据统计:")
            for table in main_tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    logger.info(f"  - {table}: {count} 条记录")
                except:
                    pass  
                
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"✗ 初始化schema失败: {e}")
            return False
            
    async def check_permissions(self) -> bool:
        try:
            conn = await asyncpg.connect(self.pg_config.dsn)
            
            test_table = 'scheduled_tasks'  
            
            permissions = await conn.fetch("""
                SELECT has_table_privilege($1, $2, 'SELECT') as can_select,
                       has_table_privilege($1, $2, 'INSERT') as can_insert,
                       has_table_privilege($1, $2, 'UPDATE') as can_update,
                       has_table_privilege($1, $2, 'DELETE') as can_delete
            """, self.pg_config.user, test_table)
            
            if permissions:
                perm = permissions[0]
                logger.info(f"✓ 用户权限检查 (表: {test_table}):")
                logger.info(f"  - SELECT: {'✓' if perm['can_select'] else '✗'}")
                logger.info(f"  - INSERT: {'✓' if perm['can_insert'] else '✗'}")
                logger.info(f"  - UPDATE: {'✓' if perm['can_update'] else '✗'}")
                logger.info(f"  - DELETE: {'✓' if perm['can_delete'] else '✗'}")
                
            await conn.close()
            return True
            
        except Exception as e:
            logger.warning(f"权限检查失败: {e}")
            return True  
            
    async def create_partitions(self) -> bool:
        try:
            logger.info("")
            logger.info("正在创建初始分区...")
            conn = await asyncpg.connect(self.pg_config.dsn)
            
            partition_functions = [
                'create_tasks_partition',
                'create_task_runs_partition',
                'create_stream_backlog_partition'
            ]
            
            for func in partition_functions:
                try:
                    await conn.execute(f"SELECT {func}()")
                    logger.info(f"  ✓ 执行分区函数: {func}")
                except Exception as e:
                    logger.warning(f"  分区函数 {func} 执行警告: {str(e)[:50]}")
            
            partitions = await conn.fetch("""
                SELECT 
                    parent.relname as parent_table,
                    COUNT(*) as partition_count
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname IN ('tasks', 'task_runs', 'stream_backlog_monitor')
                GROUP BY parent.relname
            """)
            
            if partitions:
                logger.info("")
                logger.info("分区创建结果:")
                for row in partitions:
                    logger.info(f"  - {row['parent_table']}: {row['partition_count']} 个分区")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"创建分区失败: {e}")
            return False
    
    async def run(self) -> bool:
        logger.info("=" * 60)
        logger.info("JetTask 数据库初始化 (支持分区表和优化索引)")
        logger.info("=" * 60)
        
        if not await self.create_database():
            return False
            
        if not await self.test_connection():
            return False
            
        if not await self.init_schema():
            return False
            
        await self.create_partitions()
        
        await self.check_permissions()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ 数据库初始化完成！")
        logger.info("=" * 60)
        logger.info("")
        logger.info("特性说明:")
        logger.info("  • tasks 和 task_runs 表已配置为按月分区")
        logger.info("  • 索引已优化，删除冗余索引")
        logger.info("  • 自动分区管理函数已创建")
        logger.info("")
        logger.info("维护建议:")
        logger.info("  • 定期执行: SELECT maintain_tasks_partitions()")
        logger.info("  • 定期执行: SELECT maintain_task_runs_partitions()")
        logger.info("  • 建议配置 cron 任务自动维护分区")
        logger.info("")
        logger.info("您现在可以启动服务:")
        logger.info(f"  python -m jettask.webui.backend.main")
        logger.info("")
        
        return True


async def init_database_async(pg_config: PostgreSQLConfig):
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    initializer = DatabaseInitializer(pg_config)
    success = await initializer.run()
    
    if not success:
        sys.exit(1)

def init_database():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    pg_config = PostgreSQLConfig(
        host=os.getenv('JETTASK_PG_HOST', 'localhost'),
        port=int(os.getenv('JETTASK_PG_PORT', '5432')),
        database=os.getenv('JETTASK_PG_DATABASE', 'jettask'),
        user=os.getenv('JETTASK_PG_USER', 'jettask'),
        password=os.getenv('JETTASK_PG_PASSWORD', '123456'),
    )
    
    asyncio.run(init_database_async(pg_config))

if __name__ == "__main__":
    init_database()