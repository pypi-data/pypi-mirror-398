
import re
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

def name(value: str) -> bool:
    """Проверяет, что имя содержит только буквы и дефис, длина 1-50 символов."""
    if not isinstance(value, str):
        return False
    if not (1 <= len(value) <= 50):
        return False
    return bool(re.match(r"^[A-Za-zА-Яа-яЁё\-]+$", value))

def phone_ru(value: str) -> bool:
    """Проверяет формат телефона +7XXXXXXXXXX или 8XXXXXXXXXX."""
    if not isinstance(value, str):
        return False
    pattern = r"^(?:\+7|8)\d{10}$"
    return bool(re.match(pattern, value))

def age(value: str) -> bool:
    """Возраст должен быть числом от 0 до 120."""
    if not value.isdigit():
        return False
    age = int(value)
    return 0 <= age <= 120

def height(value: str) -> bool:
    """Рост в сантиметрах: от 30 до 300."""
    try:
        h = float(value)
        return 30 <= h <= 300
    except ValueError:
        return False

def weight(value: str) -> bool:
    """Вес в кг: от 2 до 500."""
    try:
        w = float(value)
        return 2 <= w <= 500
    except ValueError:
        return False

def gender(value: str) -> bool:
    """
    Валидатор пола с поддержкой русского и английского языков.

    Допустимые варианты (регистр не важен):
    - Русские: "мужской", "м", "женский", "ж", "не указан", "другое", "не скажу"
    - Английские: "male", "m", "female", "f", "other", "not specified", "prefer not to say"

    Возвращает True, если значение совпадает с одним из допустимых, иначе False.
    """
    if not isinstance(value, str):
        return False

    value_normalized = value.strip().lower()

    valid_genders = {
        # Русские варианты
        "мужской", "м","Мужской","Муж"
        "женский", "ж","Женский","Жен",
        "не указан", "другое", "не скажу",
        # Английские варианты
        "male", "m",
        "female", "f",
        "other", "not specified", "prefer not to say"
    }

    return value_normalized in valid_genders


def phone(value: str, region: str = None) -> bool:
    """
    Универсальная валидация телефонного номера для любых стран.

    Аргументы:
        value: строка, номер телефона в любом формате, включая международный (+...).
        region: код страны ISO alpha-2 (например, 'RU', 'US'), если номер без кода страны,
                для правильной обработки регионального формата.

    Возвращает:
        True, если номер валиден, иначе False.
    """
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        # Разбор номера, учитывая регион, если он указан
        phone_number = phonenumbers.parse(value, region)
        # Проверка валидности номера
        return phonenumbers.is_valid_number(phone_number)
    except NumberParseException:
        return False
