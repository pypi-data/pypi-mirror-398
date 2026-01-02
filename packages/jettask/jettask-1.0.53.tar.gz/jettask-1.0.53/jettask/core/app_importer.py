"""
App importer module inspired by Uvicorn's import logic.
支持多种方式导入 Jettask 应用实例。
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, Any
import inspect


class AppImporter:
    """应用导入器，支持多种导入方式"""
    
    DEFAULT_APP_NAMES = ['app', 'application', 'jettask_app']
    
    DEFAULT_FILES = ['app.py', 'main.py', 'server.py', 'worker.py']
    
    @classmethod
    def import_from_string(cls, import_str: str) -> Any:
        if ':' in import_str:
            module_str, app_name = import_str.rsplit(':', 1)
        else:
            module_str = import_str
            app_name = None
        
        if '/' in module_str or module_str.endswith('.py') or os.path.isdir(module_str):
            module = cls._import_from_file(module_str)
        else:
            module = cls._import_from_module(module_str)
        
        if app_name:
            if '.' in app_name or '(' in app_name:
                app = cls._evaluate_app_expression(module, app_name)
            else:
                app = getattr(module, app_name)
        else:
            app = cls._find_app_in_module(module)
            if not app:
                raise ImportError(
                    f"Cannot find Jettask app in {module_str}. "
                    f"Tried names: {', '.join(cls.DEFAULT_APP_NAMES)}"
                )
        
        return app
    
    @classmethod
    def _import_from_file(cls, file_path: str):
        path = Path(file_path)
        
        if not path.is_absolute():
            path = Path.cwd() / path
        
        if path.is_dir():
            init_file = path / '__init__.py'
            if not init_file.exists():
                raise ImportError(
                    f"Directory {path} does not contain __init__.py. "
                    f"Cannot import as a Python package."
                )
            py_file = init_file
            module_name = path.name
            parent_dir = path.parent
        else:
            if path.suffix == '.py':
                path = path.with_suffix('')
            
            py_file = path.with_suffix('.py')
            if not py_file.exists():
                raise ImportError(f"File not found: {py_file}")
            
            module_name = path.name
            parent_dir = path.parent
        
        sys.path.insert(0, str(parent_dir))
        
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, 
                str(py_file)
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                try:
                    spec.loader.exec_module(module)
                    return module
                except Exception as e:
                    import traceback
                    tb_lines = traceback.format_exc().splitlines()
                    
                    user_error_lines = [line for line in tb_lines 
                                       if str(py_file) in line or module_name in line]
                    
                    raise ImportError(
                        f"Failed to load module from {py_file}.\n"
                        f"Error in user code: {str(e)}\n"
                        f"Check the file for syntax errors or missing dependencies."
                    ) from e
            else:
                raise ImportError(f"Cannot create module spec for {py_file}")
        finally:
            if str(parent_dir) in sys.path:
                sys.path.remove(str(parent_dir))
    
    @classmethod
    def _import_from_module(cls, module_str: str):
        try:
            return importlib.import_module(module_str)
        except ImportError as e:
            original_error = str(e)
            
            if '.' not in sys.path:
                sys.path.insert(0, '.')
                try:
                    return importlib.import_module(module_str)
                except ImportError as retry_error:
                    import traceback
                    tb_str = traceback.format_exc()
                    
                    if f"No module named '{module_str}'" in str(retry_error):
                        raise ImportError(
                            f"Module '{module_str}' not found. "
                            f"Make sure the module exists and is in the Python path."
                        ) from retry_error
                    else:
                        raise ImportError(
                            f"Failed to import module '{module_str}'. "
                            f"The module was found but contains errors:\n{original_error}"
                        ) from retry_error
            raise
    
    @classmethod
    def _find_app_in_module(cls, module) -> Optional[Any]:
        from ..core.app import Jettask
        
        for name in cls.DEFAULT_APP_NAMES:
            if hasattr(module, name):
                obj = getattr(module, name)
                if isinstance(obj, Jettask):
                    return obj
        
        for name in dir(module):
            if not name.startswith('_'):
                obj = getattr(module, name, None)
                if isinstance(obj, Jettask):
                    return obj
        
        return None
    
    @classmethod
    def _evaluate_app_expression(cls, module, expression: str):
        namespace = {'__builtins__': {}}
        namespace.update(vars(module))
        
        try:
            return eval(expression, namespace)
        except Exception as e:
            raise ImportError(f"Cannot evaluate expression '{expression}': {e}")
    
    @classmethod
    def auto_discover(cls) -> Optional[Any]:
        from ..core.app import Jettask
        
        env_app = os.getenv('JETTASK_APP')
        if env_app:
            try:
                return cls.import_from_string(env_app)
            except Exception:
                pass
        
        for filename in cls.DEFAULT_FILES:
            file_path = Path.cwd() / filename
            if file_path.exists():
                try:
                    module = cls._import_from_file(str(file_path))
                    app = cls._find_app_in_module(module)
                    if app:
                        return app
                except Exception:
                    continue
        
        for py_file in Path.cwd().glob('*.py'):
            if py_file.name.startswith('_'):
                continue
            try:
                module = cls._import_from_file(str(py_file))
                app = cls._find_app_in_module(module)
                if app:
                    return app
            except Exception:
                continue
        
        return None
    
    @classmethod
    def get_app_info(cls, app) -> dict:
        from ..core.app import Jettask
        
        if not isinstance(app, Jettask):
            return {'error': 'Not a Jettask instance'}
        
        info = {
            'type': 'Jettask',
            'redis_url': getattr(app, 'redis_url', 'Not configured'),
            'redis_prefix': getattr(app, 'redis_prefix', 'jettask'),
            'tasks': len(getattr(app, '_tasks', {})),
        }
        
        if hasattr(app, '_tasks'):
            info['task_names'] = list(app._tasks.keys())
        
        return info


def import_app(import_str: Optional[str] = None) -> Any:
    if import_str:
        return AppImporter.import_from_string(import_str)
    else:
        app = AppImporter.auto_discover()
        if not app:
            raise ImportError(
                "Cannot auto-discover Jettask app. "
                "Please specify app location (e.g., 'module:app') "
                "or set JETTASK_APP environment variable."
            )
        return app