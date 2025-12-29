import re

def validate_not_empty(value: str) -> bool:
    """Проверяет, что строка не пустая."""
    return bool(value and value.strip())

def validate_email(value: str) -> bool:
    """Простая проверка email через регулярное выражение."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, value))

def validate_zip_code(value: str) -> bool:
    """Проверяет почтовый индекс: 5 или 6 цифр подряд."""
    return bool(re.match(r"^\d{5,6}$", value))

def validate_username(value: str) -> bool:
    """Имя пользователя: только буквы, цифры и подчеркивания, длина 3-30 символов."""
    return bool(re.match(r"^\w{3,30}$", value))

def validate_positive_int(value: str) -> bool:
    """Проверяет, что значение - положительное целое число."""
    return value.isdigit() and int(value) > 0

def validate_url(value: str) -> bool:
    """Простая проверка URL."""
    pattern = r"^(https?://)?([\w\-]+\.)+[\w\-]+(/[\w\-./?%&=]*)?$"
    return bool(re.match(pattern, value))

def validate_password_strength(value: str) -> bool:
    """
    Проверка пароля:
    - минимум 8 символов,
    - есть хотя бы одна цифра,
    - есть хотя бы одна заглавная буква,
    - есть хотя бы одна строчная буква,
    - есть хотя бы один спецсимвол.
    """
    if len(value) < 8:
        return False
    if not re.search(r"\d", value):
        return False
    if not re.search(r"[A-Z]", value):
        return False
    if not re.search(r"[a-z]", value):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        return False
    return True

