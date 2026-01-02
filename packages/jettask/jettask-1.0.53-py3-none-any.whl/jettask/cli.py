#!/usr/bin/env python
"""
JetTask CLI - 命令行接口
"""
import asyncio
import click
import sys
import os
import multiprocessing

    
if __name__ == '__main__':
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from jettask.config.nacos_config import config
from jettask.config.env_loader import EnvLoader
from jettask.core.app_importer import import_app, AppImporter
import functools


def async_command(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


def load_nacos_config(nacos_server=None, nacos_namespace=None, nacos_username=None,
                     nacos_password=None, nacos_group=None, nacos_data_id=None):
    import os

    try:
        nacos_server = nacos_server or os.environ.get('NACOS_SERVER')
        nacos_namespace = nacos_namespace or os.environ.get('NACOS_NAMESPACE')
        nacos_username = nacos_username or os.environ.get('NACOS_USERNAME')
        nacos_password = nacos_password or os.environ.get('NACOS_PASSWORD')
        nacos_group = nacos_group or os.environ.get('NACOS_GROUP', 'DEFAULT_GROUP')
        nacos_data_id = nacos_data_id or os.environ.get('NACOS_DATA_ID')

        if not all([nacos_server, nacos_namespace, nacos_group]):
            missing = []
            if not nacos_server: missing.append("--nacos-server 或 NACOS_SERVER")
            if not nacos_namespace: missing.append("--nacos-namespace 或 NACOS_NAMESPACE")
            if not nacos_group: missing.append("--nacos-group 或 NACOS_GROUP")

            click.echo("Error: Nacos配置不完整，缺少以下配置:", err=True)
            for item in missing:
                click.echo(f"  - {item}", err=True)
            raise click.Abort()

        os.environ['NACOS_SERVER'] = nacos_server
        os.environ['NACOS_NAMESPACE'] = nacos_namespace
        os.environ['NACOS_GROUP'] = nacos_group
        if nacos_data_id:
            os.environ['NACOS_DATA_ID'] = nacos_data_id
        if nacos_username:
            os.environ['NACOS_USERNAME'] = nacos_username
        if nacos_password:
            os.environ['NACOS_PASSWORD'] = nacos_password

        click.echo(f"正在从Nacos加载配置 ({nacos_server}/{nacos_namespace})...")

        nacos_config = {}

        nacos_pg_url = config.config.get('JETTASK_PG_URL')
        if not nacos_pg_url:
            pg_host = config.config.get('PG_DB_HOST', 'localhost')
            pg_port = config.config.get('PG_DB_PORT', 5432)
            pg_user = config.config.get('PG_DB_USERNAME', 'jettask')
            pg_password = config.config.get('PG_DB_PASSWORD', '123456')
            pg_database = config.config.get('PG_DB_DATABASE', 'jettask')
            nacos_pg_url = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}'

        if nacos_pg_url:
            os.environ['JETTASK_PG_URL'] = nacos_pg_url
            nacos_config['pg_url'] = nacos_pg_url

        redis_host = config.config.get('REDIS_HOST', 'localhost')
        redis_port = config.config.get('REDIS_PORT', 6379)
        redis_db = config.config.get('REDIS_DB', 0)
        redis_password = config.config.get('REDIS_PASSWORD')
        if redis_password:
            redis_url = f'redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}'
        else:
            redis_url = f'redis://{redis_host}:{redis_port}/{redis_db}'
        os.environ['JETTASK_REDIS_URL'] = redis_url
        nacos_config['redis_url'] = redis_url

        nacos_api_key = config.config.get('JETTASK_API_KEY') or config.config.get('API_KEY')
        if nacos_api_key:
            os.environ['JETTASK_API_KEY'] = nacos_api_key
            nacos_config['api_key'] = nacos_api_key
            click.echo(f"✓ 从Nacos获取API密钥配置")

        nacos_jwt_secret = config.config.get('JETTASK_JWT_SECRET')
        if nacos_jwt_secret:
            os.environ['JETTASK_JWT_SECRET'] = nacos_jwt_secret
            nacos_config['jwt_secret'] = nacos_jwt_secret
            click.echo(f"✓ 从Nacos获取JWT密钥配置")

        nacos_remote_token_url = config.config.get('JETTASK_REMOTE_TOKEN_VERIFY_URL')
        if nacos_remote_token_url:
            os.environ['JETTASK_REMOTE_TOKEN_VERIFY_URL'] = nacos_remote_token_url
            nacos_config['remote_token_verify_url'] = nacos_remote_token_url
            click.echo(f"✓ 从Nacos获取远程Token验证URL配置")

        for key, value in config.config.items():
            if isinstance(value, (str, int, float, bool)):
                os.environ[key] = str(value)

        click.echo(f"✓ 从Nacos加载配置成功")
        return nacos_config

    except click.Abort:
        raise
    except Exception as e:
        click.echo(f"Error: 从Nacos加载配置失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise click.Abort()


@click.group()
@click.version_option(version='0.1.0', prog_name='JetTask')
@click.option('--env-file', '-e', envvar='JETTASK_ENV_FILE',
              help='环境变量文件路径 (.env 格式)，可通过 JETTASK_ENV_FILE 环境变量指定')
@click.pass_context
def cli(ctx, env_file):
    ctx.ensure_object(dict)

    loader = EnvLoader()

    if env_file:
        try:
            loader.load_env_file(env_file, override=True)
            click.echo(f"✓ 已加载环境变量文件: {env_file}")
        except FileNotFoundError:
            click.echo(f"Error: 环境变量文件不存在: {env_file}", err=True)
            raise click.Abort()
        except Exception as e:
            click.echo(f"Error: 加载环境变量文件失败: {e}", err=True)
            raise click.Abort()
    else:
        loader.auto_load()

    ctx.obj['env_loader'] = loader

@cli.command()
@click.option('--host', default='0.0.0.0', envvar='JETTASK_API_HOST', help='服务器监听地址')
@click.option('--port', default=8001, type=int, envvar='JETTASK_API_PORT', help='服务器监听端口')
@click.option('--redis-url', envvar='JETTASK_REDIS_URL', help='Redis连接URL')
@click.option('--redis-prefix', envvar='JETTASK_REDIS_PREFIX', help='Redis键前缀')
@click.option('--jettask-pg-url', envvar='JETTASK_PG_URL', help='PostgreSQL连接URL')
@click.option('--reload', is_flag=True, envvar='JETTASK_API_RELOAD', help='启用自动重载')
@click.option('--log-level', default='info', envvar='JETTASK_LOG_LEVEL',
              type=click.Choice(['debug', 'info', 'warning', 'error']),
              help='日志级别')
@click.option('--api-key', envvar='JETTASK_API_KEY', help='API密钥（用于后端服务认证）')
@click.option('--jwt-secret', envvar='JETTASK_JWT_SECRET', help='JWT密钥')
@click.option('--remote-token-verify-url', envvar='JETTASK_REMOTE_TOKEN_VERIFY_URL',
              help='企业SSO token验证API地址')
@click.option('--use-nacos', is_flag=True,
              help='从Nacos配置中心读取配置')
@click.option('--nacos-server',
              help='Nacos服务器地址 (如: 127.0.0.1:8848)')
@click.option('--nacos-namespace',
              help='Nacos命名空间')
@click.option('--nacos-username',
              help='Nacos用户名')
@click.option('--nacos-password',
              help='Nacos密码')
@click.option('--nacos-group',
              help='Nacos配置组')
@click.option('--nacos-data-id',
              help='Nacos配置ID')
@click.pass_context
def api(ctx, host, port, redis_url, redis_prefix, jettask_pg_url, reload, log_level,
        api_key, jwt_secret, remote_token_verify_url, use_nacos, nacos_server, nacos_namespace,
        nacos_username, nacos_password, nacos_group, nacos_data_id):


    if use_nacos:
        nacos_config = load_nacos_config(
            nacos_server=nacos_server,
            nacos_namespace=nacos_namespace,
            nacos_username=nacos_username,
            nacos_password=nacos_password,
            nacos_group=nacos_group,
            nacos_data_id=nacos_data_id
        )

        if not jettask_pg_url:
            jettask_pg_url = nacos_config.get('pg_url')
        if not redis_url:
            redis_url = nacos_config.get('redis_url')
        if not api_key:
            api_key = nacos_config.get('api_key')
        if not jwt_secret:
            jwt_secret = nacos_config.get('jwt_secret')
        if not remote_token_verify_url:
            remote_token_verify_url = nacos_config.get('remote_token_verify_url')

    if not jettask_pg_url:
        raise ValueError(
            "必须提供 --jettask-pg-url 或在环境变量中设置 JETTASK_PG_URL\n"
            "或使用 jettask api --use-nacos 从Nacos加载配置"
        )

    if not redis_url:
        raise ValueError(
            "必须提供 --redis-url 或在环境变量中设置 JETTASK_REDIS_URL\n"
            "或使用 jettask api --use-nacos 从Nacos加载配置"
        )

    os.environ['JETTASK_REDIS_URL'] = redis_url
    if redis_prefix:
        os.environ['JETTASK_REDIS_PREFIX'] = redis_prefix
    os.environ['JETTASK_PG_URL'] = jettask_pg_url
    os.environ['USE_NACOS'] = 'true' if use_nacos else 'false'
    if api_key:
        os.environ['JETTASK_API_KEY'] = api_key
    if jwt_secret:
        os.environ['JETTASK_JWT_SECRET'] = jwt_secret
    if remote_token_verify_url:
        os.environ['JETTASK_REMOTE_TOKEN_VERIFY_URL'] = remote_token_verify_url
    
    app_module = "jettask.webui.app:app"
    click.echo(f"Starting JetTask API Server on {host}:{port}")
    
    click.echo("=" * 60)
    click.echo("API Server Configuration")
    click.echo("=" * 60)
    click.echo(f"Host:         {host}")
    click.echo(f"Port:         {port}")
    click.echo(f"Redis URL:    {redis_url}")
    click.echo(f"Redis Prefix: {redis_prefix or 'jettask (default)'}")
    click.echo(f"Database:     {jettask_pg_url}")
    click.echo(f"Auto-reload:  {reload}")
    click.echo(f"Log level:    {log_level}")
    click.echo(f"Nacos:        {'Enabled' if use_nacos else 'Disabled'}")

    click.echo("=" * 60)
    click.echo("Authentication Configuration")
    click.echo("=" * 60)

    if api_key:
        if ctx.params.get('api_key'):
            api_key_source = "命令行参数"
        elif use_nacos and (config.config.get('JETTASK_API_KEY') or config.config.get('API_KEY')):
            api_key_source = "Nacos配置"
        else:
            api_key_source = "环境变量"
        click.echo(f"API Key:      Enabled (后端服务认证, 来源: {api_key_source})")
    else:
        click.echo(f"API Key:      Disabled")

    if jwt_secret:
        if ctx.params.get('jwt_secret'):
            jwt_source = "命令行参数"
        elif use_nacos and config.config.get('JETTASK_JWT_SECRET'):
            jwt_source = "Nacos配置"
        else:
            jwt_source = "环境变量"
        click.echo(f"JWT:          Enabled (前端用户认证, 来源: {jwt_source})")
    else:
        click.echo(f"JWT:          Using default secret (不建议用于生产环境)")

    if remote_token_verify_url:
        if ctx.params.get('remote_token_verify_url'):
            remote_source = "命令行参数"
        elif use_nacos and config.config.get('JETTASK_REMOTE_TOKEN_VERIFY_URL'):
            remote_source = "Nacos配置"
        else:
            remote_source = "环境变量"
        click.echo(f"Remote Token: Enabled (企业SSO集成, 来源: {remote_source})")
        click.echo(f"  验证URL:    {remote_token_verify_url}")
    else:
        click.echo(f"Remote Token: Not configured (企业SSO未配置)")
    click.echo("=" * 60)
    click.echo(f"API Endpoint: http://{host}:{port}/api")
    click.echo(f"WebUI:        http://{host}:{port}/")
    click.echo("=" * 60)
    import uvicorn
    try:
        uvicorn.run(
            app_module,
            host=host,
            port=port,
            log_level=log_level,
            reload=reload
        )
    except KeyboardInterrupt:
        click.echo("\nShutting down API Server...")
    except Exception as e:
        click.echo(f"Error starting API Server: {e}", err=True)
        sys.exit(1)



@cli.command()
@click.option('--app', '-a', 'app_str', envvar='JETTASK_APP',
              help='应用位置 (如: module:app, path/to/file.py:app, 或目录名)')
@click.option('--tasks', '-t', envvar='JETTASK_TASKS', help='任务名称（逗号分隔，如: task1,task2）')
@click.option('--concurrency', '-c', type=int, envvar='JETTASK_CONCURRENCY', help='并发数（默认为CPU核心数的一半）')
@click.option('--prefetch', '-p', type=int, default=100, envvar='JETTASK_PREFETCH', help='预取倍数')
@click.option('--local-concurrency', '-lc', type=int, envvar='JETTASK_LOCAL_CONCURRENCY',
              help='本地并发限制（限制每个 worker 节点的协程并发数，用于 CPU 密集型任务防止资源耗尽）')
def worker(app_str, tasks, concurrency, prefetch, local_concurrency):


    if not tasks:
        click.echo("Error: 必须指定 --tasks 参数或设置 JETTASK_TASKS 环境变量", err=True)
        click.echo("\n示例:", err=True)
        click.echo("  jettask worker --tasks my_task", err=True)
        click.echo("  jettask worker -t task1,task2", err=True)
        click.echo("  export JETTASK_TASKS=my_task && jettask worker", err=True)
        raise click.Abort()

    cpu_count = multiprocessing.cpu_count()
    if concurrency is None:
        concurrency = max(1, cpu_count // 4)
        click.echo(f"Using default concurrency: {concurrency} (1/4 of {cpu_count} CPU cores)")
    if concurrency>cpu_count:
        click.echo(f"Error: Specified concurrency {concurrency} exceeds CPU cores {cpu_count}", err=True)
        raise click.Abort()

    try:
        if app_str:
            click.echo(f"Loading app from: {app_str}")
            app = import_app(app_str)
        else:
            click.echo("Auto-discovering Jettask app...")
            click.echo("Searching in: app.py, main.py, server.py, worker.py")
            app = import_app()  
        
        
        app_info = AppImporter.get_app_info(app)
        click.echo(f"\nFound Jettask app:")
        click.echo(f"  Tasks: {app_info['tasks']} registered")
        
        if app_info.get('task_names') and app_info['tasks'] > 0:
            task_preview = app_info['task_names'][:3]
            click.echo(f"  Names: {', '.join(task_preview)}" + 
                      (f" (+{app_info['tasks'] - 3} more)" if app_info['tasks'] > 3 else ""))
    except ImportError as e:
        import traceback
        click.echo(f"Error: Failed to import app: {e}", err=True)
        
        click.echo("\n" + "=" * 60, err=True)
        click.echo("Full traceback:", err=True)
        click.echo("=" * 60, err=True)
        traceback.print_exc()
        click.echo("=" * 60, err=True)
        
        click.echo("\nTips:", err=True)
        click.echo("  - Check if there are syntax errors in your code", err=True)
        click.echo("  - Verify all imports in your module are available", err=True)
        click.echo("  - Specify app location: jettask worker myapp:app", err=True)
        click.echo("  - Or set environment variable: export JETTASK_APP=myapp:app", err=True)
        click.echo("  - Or ensure app.py or main.py exists in current directory", err=True)
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        click.echo(f"Error loading app: {e}", err=True)
        
        click.echo("\n" + "=" * 60, err=True)
        click.echo("Full traceback:", err=True)
        click.echo("=" * 60, err=True)
        traceback.print_exc()
        click.echo("=" * 60, err=True)
        
        click.echo("\nThis might be a bug in JetTask or your application.", err=True)
        click.echo("Please check the traceback above for details.", err=True)
        sys.exit(1)
    
    task_list = [t.strip() for t in tasks.split(',') if t.strip()]

    redis_url = app.redis_url if hasattr(app, 'redis_url') else 'Not configured'
    redis_prefix = app.redis_prefix if hasattr(app, 'redis_prefix') else 'jettask'

    click.echo("=" * 60)
    click.echo("JetTask Worker Configuration")
    click.echo("=" * 60)
    click.echo(f"App:          {app_str}")
    click.echo(f"Redis URL:    {redis_url}")
    click.echo(f"Redis Prefix: {redis_prefix}")
    click.echo(f"Tasks:        {', '.join(task_list)}")
    click.echo(f"Concurrency:  {concurrency}")
    click.echo(f"Prefetch:     {prefetch}")
    click.echo(f"Local Conc:   {local_concurrency if local_concurrency else 'Unlimited'}")
    click.echo("=" * 60)

    try:
        click.echo(f"Starting worker...")
        app.start(
            tasks=task_list,
            concurrency=concurrency,
            prefetch_multiplier=prefetch,
            local_concurrency=local_concurrency
        )
    except KeyboardInterrupt:
        click.echo("\nShutting down worker...")
    except Exception as e:
        click.echo(f"Error starting worker: {e}", err=True)
        sys.exit(1)

@cli.command('webui-consumer')
@click.option('--task-center', '-tc', envvar='JETTASK_CENTER_URL',
              help='任务中心URL，如: http://localhost:8001 或 http://localhost:8001/api/namespaces/default')
@click.option('--check-interval', type=int, default=30,
              help='命名空间检测间隔（秒），仅多命名空间模式使用，默认30秒')
@click.option('--concurrency', '-c', type=int, default=4,
              help='并发数（每个命名空间的 worker 进程数），默认4')
@click.option('--prefetch', '-p', type=int, default=1000,
              help='预取倍数（控制每次从队列预取的消息数），默认1000')
@click.option('--api-key', envvar='JETTASK_API_KEY', help='API密钥用于请求鉴权（与API服务器保持一致）')
@click.option('--use-nacos', is_flag=True,
              help='从Nacos配置中心读取配置')
@click.option('--nacos-server',
              help='Nacos服务器地址 (如: 127.0.0.1:8848)')
@click.option('--nacos-namespace',
              help='Nacos命名空间')
@click.option('--nacos-username',
              help='Nacos用户名')
@click.option('--nacos-password',
              help='Nacos密码')
@click.option('--nacos-group',
              help='Nacos配置组')
@click.option('--nacos-data-id',
              help='Nacos配置ID')
@click.option('--debug', is_flag=True, help='启用调试模式')
def webui_consumer(task_center, check_interval, concurrency, prefetch, api_key,
                  use_nacos, nacos_server, nacos_namespace, nacos_username, nacos_password,
                  nacos_group, nacos_data_id, debug):
    import asyncio
    import os
    from jettask.persistence.manager import UnifiedConsumerManager

    if use_nacos:
        nacos_config = load_nacos_config(
            nacos_server=nacos_server,
            nacos_namespace=nacos_namespace,
            nacos_username=nacos_username,
            nacos_password=nacos_password,
            nacos_group=nacos_group,
            nacos_data_id=nacos_data_id
        )

        if not api_key:
            api_key = nacos_config.get('api_key')
        if not task_center:
            task_center = os.environ.get('JETTASK_CENTER_URL', 'http://localhost:8001')

    if not task_center:
        raise ValueError(
            "必须提供 --task-center 或在环境变量中设置 JETTASK_CENTER_URL\n"
            "或使用 jettask webui-consumer --use-nacos 从Nacos加载配置"
        )

    if api_key:
        click.echo(f"✓ API密钥已配置（鉴权已启用）")

    async def run_manager():
        manager = UnifiedConsumerManager(
            task_center_url=task_center,
            check_interval=check_interval,
            concurrency=concurrency,
            prefetch_multiplier=prefetch,
            api_key=api_key,
            debug=debug
        )
        await manager.run()

    try:
        asyncio.run(run_manager())
    except KeyboardInterrupt:
        click.echo("\n✓ 消费者已关闭")



@cli.command()
@click.option('--task-center', '-tc', envvar='JETTASK_CENTER_URL',
              help='任务中心URL，如: http://localhost:8001 或 http://localhost:8001/api/namespaces/default')
@click.option('--interval', '-i', type=float, default=5,
              help='调度器扫描间隔（秒），默认5秒')
@click.option('--batch-size', '-b', type=int, default=100,
              help='每批处理的最大任务数，默认100')
@click.option('--check-interval', type=int, default=30,
              help='命名空间检测间隔（秒），仅多命名空间模式使用，默认30秒')
@click.option('--api-key', envvar='JETTASK_API_KEY', help='API密钥用于请求鉴权（与API服务器保持一致）')
@click.option('--use-nacos', is_flag=True,
              help='从Nacos配置中心读取配置')
@click.option('--nacos-server',
              help='Nacos服务器地址 (如: 127.0.0.1:8848)')
@click.option('--nacos-namespace',
              help='Nacos命名空间')
@click.option('--nacos-username',
              help='Nacos用户名')
@click.option('--nacos-password',
              help='Nacos密码')
@click.option('--nacos-group',
              help='Nacos配置组')
@click.option('--nacos-data-id',
              help='Nacos配置ID')
@click.option('--debug', is_flag=True, help='启用调试模式')
def scheduler(task_center, interval, batch_size, check_interval, api_key,
             use_nacos, nacos_server, nacos_namespace, nacos_username, nacos_password,
             nacos_group, nacos_data_id, debug):
    import asyncio
    import os
    from jettask.scheduler.manager import UnifiedSchedulerManager

    if use_nacos:
        nacos_config = load_nacos_config(
            nacos_server=nacos_server,
            nacos_namespace=nacos_namespace,
            nacos_username=nacos_username,
            nacos_password=nacos_password,
            nacos_group=nacos_group,
            nacos_data_id=nacos_data_id
        )

        if not api_key:
            api_key = nacos_config.get('api_key')
        if not task_center:
            task_center = os.environ.get('JETTASK_CENTER_URL', 'http://localhost:8001')

    if not task_center:
        raise ValueError(
            "必须提供 --task-center 或在环境变量中设置 JETTASK_CENTER_URL\n"
            "或使用 jettask scheduler --use-nacos 从Nacos加载配置"
        )

    if api_key:
        click.echo(f"✓ API密钥已配置（鉴权已启用）")

    async def run_manager():
        manager = UnifiedSchedulerManager(
            task_center_url=task_center,
            scan_interval=interval,
            batch_size=batch_size,
            check_interval=check_interval,
            api_key=api_key,
            debug=debug
        )
        await manager.run()

    try:
        asyncio.run(run_manager())
    except KeyboardInterrupt:
        click.echo("\nShutdown complete")


def main():
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()