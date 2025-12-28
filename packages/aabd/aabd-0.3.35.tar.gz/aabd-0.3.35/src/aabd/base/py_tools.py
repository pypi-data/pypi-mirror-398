import uuid
import sys
import importlib.util

import sys

# 兼容 Python < 3.8
try:
    from importlib.metadata import distributions
except ImportError:
    from importlib_metadata import distributions

from packaging.requirements import Requirement
from packaging.version import Version
from packaging.specifiers import SpecifierSet

modules = {}


def import_by_path(path, name=None, module_name=None):
    module_name = module_name or f'abc_{uuid.uuid4().hex}'

    package_module = modules.get(module_name, None)
    if package_module is None:
        spec = importlib.util.spec_from_file_location(module_name, path)
        package_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = package_module
        spec.loader.exec_module(package_module)
        modules[module_name] = package_module
    if name is not None:
        return getattr(package_module, name)
    else:
        return package_module


def create_instance_by_classname(module, class_name, *args, **kwargs):
    """从模块中通过类名字符串创建实例"""
    cls = getattr(module, class_name, None)
    if cls is None:
        raise AttributeError(f"Class '{class_name}' not found in module {module.__name__}")
    if not callable(cls):
        raise TypeError(f"{class_name} is not a class")
    return cls(*args, **kwargs)


def call_method_by_name(instance, method_name, *args, **kwargs):
    """通过方法名字符串调用实例方法"""
    method = getattr(instance, method_name, None)
    if method is None:
        raise AttributeError(f"Method '{method_name}' not found in instance")
    return method(*args, **kwargs)


def read_requirements(file_path):
    """读取 requirements.txt，忽略注释和空行"""
    reqs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # 移除可能的行内注释（如 package==1.0 # for xyz）
                line = line.split('#')[0].strip()
                if line:
                    reqs.append(line)
    return reqs


def get_installed_packages():
    """获取当前环境中所有已安装包的名称和版本"""
    installed = {}
    for dist in distributions():
        name = dist.metadata['Name']
        version = dist.version
        if name:
            # Normalize package name (e.g., "Requests" -> "requests")
            normalized = name.lower().replace('_', '-')
            installed[normalized] = Version(version)
    return installed


def check_requirements(requirements_file):
    installed = get_installed_packages()

    if isinstance(requirements_file, str):
        requirements_lines = read_requirements(requirements_file)
    elif isinstance(requirements_file, list):
        requirements_lines = []
        for file_path in requirements_file:
            requirements_lines.extend(read_requirements(file_path))
    else:
        raise ValueError("Invalid requirements file")
    issues = []

    for line in requirements_lines:
        try:
            req = Requirement(line)
            # Normalize requirement name
            req_name = req.name.lower().replace('_', '-')
            spec = req.specifier  # type: SpecifierSet

            if req_name not in installed:
                issues.append(f"❌ Missing package: {line}")
            else:
                installed_version = installed[req_name]
                if not spec.contains(installed_version, prereleases=True):
                    issues.append(
                        f"❌ Version mismatch: {line} "
                        f"(installed: {installed_version})"
                    )
        except Exception as e:
            issues.append(f"⚠️ Invalid requirement: {line} ({e})")

    return not issues, issues


if __name__ == '__main__':
    a = import_by_path('log_setting.py')
    log3 = getattr(a, 'LoggerWriter')('DEBUG')
