import os
import importlib
import inspect
import pkgutil
import brief_survey.validators  # ваш подпакет с валидаторами

def find_validator_by_name(name: str):
    # Получаем путь к пакету validators
    package = brief_survey.validators
    package_path = package.__path__  # список путей, обычно один

    for _, module_name, is_pkg in pkgutil.iter_modules(package_path):
        if not is_pkg:
            full_module_name = f"{package.__name__}.{module_name}"
            module = importlib.import_module(full_module_name)
            for func_name, func in inspect.getmembers(module, inspect.isfunction):
                if func_name == name:
                    return func
    return None

