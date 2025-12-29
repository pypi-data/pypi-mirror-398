import re

def validate_date_iso(value: str) -> bool:
    """Проверка формата даты ISO 8601 YYYY-MM-DD."""
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    return bool(re.match(pattern, value))

def validate_date_flexible(value: str) -> bool:
    """
    Проверяет дату, где допустимы разделители '.', '-', ' '.

    Форматы, которые валидирует:
    - YYYY-MM-DD
    - DD-MM-YYYY
    - YYYY.MM.DD
    - DD.MM.YYYY
    - YYYY MM DD
    - DD MM YYYY

    Возвращает True, если строка соответствует одному из вариантов.
    НЕ проверяет корректность даты (например, 31.02.2023 пройдет).
    """
    # Общий паттерн для триада чисел с разделителем однотипным по всей строке
    pattern = r"""
        ^                 # начало строки
        (?P<part1>\d{2,4})
        (?P<sep>[-. ])     # разделитель: - или . или пробел
        (?P<part2>\d{1,2})
        (?P=sep)           # тот же разделитель
        (?P<part3>\d{1,4})
        $                 # конец строки
    """

    match = re.match(pattern, value, re.VERBOSE)
    if not match:
        return False

    part1 = match.group("part1")
    part2 = match.group("part2")
    part3 = match.group("part3")

    # Определяем, какой формат — если первый или третий часть длиной 4 — год вероятно там
    # Поддерживаем форматы YYYY-MM-DD и DD-MM-YYYY, где год — 4 цифры, день/месяц — 1-2
    if len(part1) == 4 and len(part3) in (1, 2):
        year = part1
        month = part2
        day = part3
    elif len(part3) == 4 and len(part1) in (1, 2):
        day = part1
        month = part2
        year = part3
    else:
        # не удалось определить порядок с годом
        return False

    # Дополнительная базовая проверка чисел и диапазонов (упрощённо)
    try:
        y = int(year)
        m = int(month)
        d = int(day)
        if not (1 <= m <= 12):
            return False
        if not (1 <= d <= 31):
            return False
        if y < 1000 or y > 9999:
            return False
    except ValueError:
        return False

    return True