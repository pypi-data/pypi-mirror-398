"""
Validation module for Scrapy spiders before deployment
"""

import ast
import os
import re
import sys
import importlib.util

from .exceptions import DeploymentError
from .utils import print_warning


class SpiderValidator:
    """Validates Scrapy spiders for syntax and structure before deployment"""

    def __init__(self, target_dir='.'):
        self.target_dir = target_dir
        self.errors = []
        self.warnings = []

    def validate_project(self):
        """
        Validate the entire Scrapy project before deployment

        Returns:
            bool: True if validation passes

        Raises:
            DeploymentError: If validation fails with details of all errors
        """
        project_module = self._get_project_module()
        if not project_module:
            raise DeploymentError("Could not determine project module from scrapy.cfg")

        module_dir = os.path.join(self.target_dir, project_module)
        if not os.path.exists(module_dir):
            raise DeploymentError(f"Project module directory '{project_module}' not found")

        python_files = self._find_python_files(module_dir)
        if not python_files:
            raise DeploymentError("No Python files found in project module")

        for python_file in python_files:
            self._validate_python_file(python_file)

        spider_files = self._find_spider_files(module_dir)
        if not spider_files:
            self.warnings.append("No spider files found in 'spiders' directory")

        if not self.errors:
            self._validate_imports(python_files)

        if self.warnings:
            for warning in self.warnings:
                print_warning(f"Warning: {warning}")

        if self.errors:
            error_message = "Validation failed with the following errors:\n"
            for error in self.errors:
                error_message += f"  - {error}\n"
            raise DeploymentError(error_message)

        return True

    def _get_project_module(self):
        """Extract the project module name from scrapy.cfg"""
        scrapy_cfg = os.path.join(self.target_dir, 'scrapy.cfg')
        if not os.path.exists(scrapy_cfg):
            return None

        try:
            with open(scrapy_cfg) as f:
                for line in f:
                    if line.strip().startswith('project ='):
                        return line.strip().split('=')[1].strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _find_python_files(directory):
        """Find all Python files in the directory recursively"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache', 'pab_build']]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        return python_files

    @staticmethod
    def _find_spider_files(module_dir):
        """Find spider files in the spiders directory"""
        spiders_dir = os.path.join(module_dir, 'spiders')
        if not os.path.exists(spiders_dir):
            return []

        spider_files = []
        for file in os.listdir(spiders_dir):
            if file.endswith('.py') and file != '__init__.py':
                spider_files.append(os.path.join(spiders_dir, file))

        return spider_files

    def _validate_imports(self, python_files):
        """
        Validate that all imports in Python files can be resolved
        
        Args:
            python_files (list): List of Python file paths to validate
        """
        project_root = os.path.abspath(self.target_dir)
        original_path = sys.path.copy()
        
        try:
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            for python_file in python_files:
                if os.sep + 'scripts' + os.sep in python_file or python_file.endswith(os.sep + 'scripts'):
                    continue
                self._try_import_module(python_file)
                
        finally:
            sys.path = original_path

    def _try_import_module(self, file_path):
        """
        Try to import a Python module to check for import errors
        
        Args:
            file_path (str): Path to the Python file
        """
        rel_path = os.path.relpath(file_path, self.target_dir)
        
        try:
            module_path = os.path.relpath(file_path, self.target_dir)
            module_path = module_path.replace(os.sep, '.')
            
            if module_path.endswith('.py'):
                module_path = module_path[:-3]
            
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_path] = module
                
                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    if module_path in sys.modules:
                        del sys.modules[module_path]
                    
                    error_msg = self._format_import_error(e, rel_path)
                    if error_msg:
                        self.errors.append(error_msg)
                        
        except Exception as e:
            error_msg = f"{rel_path}: Error during import validation - {str(e)}"
            self.errors.append(error_msg)

    @staticmethod
    def _format_import_error(exception, rel_path):
        """
        Format import error message to be user-friendly
        
        Args:
            exception (Exception): The exception that occurred
            rel_path (str): Relative path for error messages
            
        Returns:
            str: Formatted error message or None if should be ignored
        """
        error_str = str(exception)
        
        if isinstance(exception, (ImportError, ModuleNotFoundError)):
            if "cannot import name" in error_str:
                match = re.search(r"cannot import name ['\"]([^'\"]+)['\"]", error_str)
                if match:
                    imported_name = match.group(1)
                    from_match = re.search(r"from ['\"]([^'\"]+)['\"]", error_str)
                    if from_match:
                        source_module = from_match.group(1)
                        return f"{rel_path}: ImportError - cannot import name '{imported_name}' from '{source_module}'"
                    else:
                        return f"{rel_path}: ImportError - cannot import name '{imported_name}'"
            
            if "No module named" in error_str:
                match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_str)
                if match:
                    module_name = match.group(1)
                    return f"{rel_path}: ImportError - No module named '{module_name}'"
            
            return f"{rel_path}: ImportError - {error_str}"
        
        elif isinstance(exception, AttributeError):
            return f"{rel_path}: AttributeError during import - {error_str}"
        
        elif isinstance(exception, NameError):
            return f"{rel_path}: NameError during import - {error_str}"
        
        else:
            non_import_exceptions = (
                'KeyError', 'ValueError', 'TypeError', 'IndexError',
                'ConnectionError', 'TimeoutError', 'OSError', 'IOError',
                'HTTPError', 'RequestException', 'BadRequest',
                'RuntimeError', 'ZeroDivisionError', 'FileNotFoundError'
            )
            
            exception_name = exception.__class__.__name__
            if exception_name in non_import_exceptions:
                return None
            
            return f"{rel_path}: {exception_name} during import - {error_str}"

    def _validate_python_file(self, file_path):
        """
        Validate a single Python file for syntax errors

        Args:
            file_path (str): Path to the Python file
        """
        rel_path = os.path.relpath(file_path, self.target_dir)

        try:
            with open(file_path, encoding='utf-8') as f:
                source_code = f.read()

            try:
                compile(source_code, file_path, 'exec')
            except SyntaxError as e:
                error_msg = f"{rel_path}: Syntax error at line {e.lineno}"
                if e.msg:
                    error_msg += f" - {e.msg}"
                if e.text:
                    error_msg += f"\n    {e.text.strip()}"
                self.errors.append(error_msg)
                return

            if 'spiders' in file_path and not file_path.endswith('__init__.py'):
                self._validate_spider_structure(file_path, source_code, rel_path)

        except UnicodeDecodeError:
            self.errors.append(f"{rel_path}: File encoding error - unable to read file")
        except Exception as e:
            self.errors.append(f"{rel_path}: Error reading file - {str(e)}")

    def _validate_spider_structure(self, file_path, source_code, rel_path):
        """
        Validate Scrapy spider structure

        Args:
            file_path (str): Path to the spider file
            source_code (str): Source code of the spider file
            rel_path (str): Relative path for error messages
        """
        try:
            tree = ast.parse(source_code, filename=file_path)

            has_class = False
            has_spider_class = False
            spider_has_name = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    has_class = True

                    for base in node.bases:
                        base_name = self._get_base_name(base)
                        if 'Spider' in base_name or 'CrawlSpider' in base_name:
                            has_spider_class = True

                            for item in node.body:
                                if isinstance(item, ast.Assign):
                                    for target in item.targets:
                                        if isinstance(target, ast.Name) and target.id == 'name':
                                            spider_has_name = True

            if has_class and not has_spider_class:
                self.warnings.append(f"{rel_path}: File contains classes but no Scrapy Spider class detected")
            elif has_spider_class and not spider_has_name:
                self.warnings.append(f"{rel_path}: Spider class missing 'name' attribute")

        except Exception:
            pass

    @staticmethod
    def _get_base_name(base_node):
        """Extract base class name from AST node"""
        if isinstance(base_node, ast.Name):
            return base_node.id
        elif isinstance(base_node, ast.Attribute):
            return base_node.attr
        return ''
