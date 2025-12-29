"""Данный модуль добавляет общие кастомные валидаторы."""

import re
from datetime import date, datetime
from functools import wraps
from typing import Callable, Optional

__all__ = [
    'skip_if_none',
    'check_not_empty',
    'check_length',
    'check_only_symbols',
    'check_only_symbols_and_spaces',
    'check_russian_phone_number',
    'check_email_pattern',
    'check_no_html_scripts',
    'check_has_timezone',
    'check_integer',
    'check_positive_num',
    'check_no_double_spaces',
    'check_symbols_numeric_spaces_special_char',
    'check_hidden_or_spaces',
    'parse_year_month_strict',
]


def skip_if_none(func: Callable[..., str]) -> Callable[..., Optional[str]]:
    """Декоратор для строковых валидаторов: если value is None — вернуть None.

    Args:
        func: Функция-валидатор, принимающая строку и
            возвращающая проверенную строку

    Returns:
        Обёрнутый валидатор, который:
            - возвращает None, если вход — None;
            - иначе вызывает исходную функцию
    """

    @wraps(func)
    def wrapper(
        value: Optional[str],
        *args: object,
        **kwargs: object,
    ) -> Optional[str]:
        if value is None:
            return None
        return func(value=value, *args, **kwargs)

    return wrapper


@skip_if_none
def check_not_empty(value: str) -> str:
    """Проверяет строку на непустоту и возвращает обрезанную строку.

    Args:
        value: Проверяемая строка

    Returns:
        str: Обрезанная (strip) и валидная строка

    Raises:
        ValueError: Если строка пустая после trim
    """
    if not value or value.strip() == '':
        raise ValueError('Поле не может быть пустым')
    return value.strip()


@skip_if_none
def check_length(
    value: str,
    min_length: int = 1,
    max_length: int = 255,
) -> str:
    """Проверяет строку на соответствие минимальной и максимальной длине.

    Args:
        value: Проверяемая строка
        min_length: Минимально допустимая длина (по умолчанию 1)
        max_length: Максимально допустимая длина (по умолчанию 255)

    Returns:
        str: Очищенная строка, прошедшая валидацию

    Raises:
        ValueError: Если строка не соответствует ограничениям
    """
    value = value.strip()
    length = len(value)

    if length < min_length:
        raise ValueError(
            f'Длина поля должна быть не менее {min_length} символов',
        )
    if length > max_length:
        raise ValueError(
            f'Длина поля не должна превышать {max_length} символов',
        )

    return value


@skip_if_none
def check_only_symbols(value: str) -> str:
    """Проверяет поле на наличие только символов (латиница/кириллица).

    Args:
        value: Проверяемая строка

    Returns:
        str: Исходная строка при успешной валидации

    Raises:
        ValueError: Если присутствуют любые символы, кроме букв
    """
    pattern = r'^[a-zA-Zа-яА-ЯёЁ]+$'
    if value and not re.fullmatch(pattern=pattern, string=value):
        raise ValueError(
            'Поле может состоять только из букв (латиница/кириллица)',
        )
    return value


@skip_if_none
def check_only_symbols_and_spaces(value: str) -> str:
    """Проверяет поле на наличие символов (латиница/кириллица) и пробелов.

    Args:
        value: Проверяемые данные

    Returns:
        value: Данные, прошедшие валидацию

    Raises:
        ValueError: Ошибка в случае непрохождения валидации
    """
    pattern = r'^[a-zA-Zа-яА-ЯёЁ\s]+$'
    if value and not re.fullmatch(pattern=pattern, string=value):
        raise ValueError(
            'Поле может состоять только из букв '
            '(латиница/кириллица) и пробелов',
        )
    return value.strip()


@skip_if_none
def check_email_pattern(value: str) -> str:
    """Проверяет email на соответствие шаблону электронной почты.

    Args:
        value: Проверяемые данные

    Returns:
        value: Данные, прошедшие валидацию

    Raises:
        ValueError: Ошибка в случае непрохождения валидации
    """
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern=pattern, string=value):
        raise ValueError('Неверный формат email')
    return value


@skip_if_none
def check_russian_phone_number(value: str) -> str:
    """Проверяет номер телефона на соответствие телефона РФ.

    Args:
        value: Проверяемые данные

    Returns:
        value: Данные, прошедшие валидацию

    Raises:
        ValueError: Ошибка в случае непрохождения валидации
    """
    if value:
        pattern = r'^\+7([\d]{10})$'
        if not re.fullmatch(pattern=pattern, string=value):
            raise ValueError(
                'Неверный формат номера телефона. Формат: +7XXXXXXXXXX',
            )
    return value


@skip_if_none
def check_no_html_scripts(value: str) -> str:
    """Проверяет наличие html скриптов.

    Args:
        value: Проверяемые данные

    Returns:
        text: Данные, прошедшие валидацию

    Raises:
        ValueError: Ошибка в случае непрохождения валидации
    """
    html_pattern = re.compile(
        pattern=r'<\s*[a-z][\s\S]*>|</\s*[a-z][\s\S]*>',
        flags=re.IGNORECASE,
    )
    if value and html_pattern.search(string=value):
        raise ValueError('Текст должен быть без HTML/скриптов')
    return value.strip()


def check_has_timezone(value: datetime) -> datetime:
    """Проверяет, что значение datetime содержит информацию о таймзоне.

    Args:
        value: Дата и время

    Returns:
        datetime: То же значение, если проверка пройдена

    Raises:
        ValueError: Если отсутствует tzinfo
    """
    if value and value.tzinfo is None:
        raise ValueError('Дата и время должны содержать таймзону (tzinfo)')
    return value


def check_integer(value: int) -> int:
    """Проверяет, что значение является целым числом.

    Args:
        value: Проверяемое значение

    Returns:
        int: то же число

    Raises:
        ValueError: Значение должно целым числом
    """
    if not isinstance(value, int):
        raise ValueError('Значение должно быть целым числом')
    return value


def check_positive_num(value: int | float) -> int | float:
    """Проверяет, что значение является положительным числом.

    Args:
        value: Проверяемое значение

    Returns:
        int | float: то же число

    Raises:
        ValueError: Если значение не число или не положительное
    """
    if not isinstance(value, (int, float)):
        raise ValueError('Значение должно быть числом')
    if value <= 0:
        raise ValueError('Значение должно быть больше нуля')
    return value


@skip_if_none
def check_no_double_spaces(value: str) -> str:
    """Проверяет, что в строке нет двух и более пробелов подряд.

    Args:
        value: Проверяемая строка.

    Returns:
        str: Обрезанная и валидная строка

    Raises:
        ValueError: Если найдены два и более пробела подряд
    """
    value = value.strip()
    if '  ' in value:
        raise ValueError(
            'Строка не может содержать более одного пробела подряд'
        )
    return value


@skip_if_none
def check_symbols_numeric_spaces_special_char(value: str) -> str:
    """Проверяет строку на допустимые символы.

    Args:
        value: Проверяемая строка.

    Returns:
        str: Обрезанная и валидная строка

    Raises:
        ValueError: Если встречены недопустимые символы
    """
    pattern = r'^[a-zA-Zа-яА-ЯёЁ0-9\s.,/\-\(\)№:]+$'
    if value and not re.fullmatch(pattern=pattern, string=value):
        raise ValueError(
            'Поле может содержать только буквы (латиница/кириллица), '
            'цифры, пробелы и спецсимволы: [. , / - ( ) № :]',
        )
    return value.strip()


def check_hidden_or_spaces(string: str) -> bool:
    """Проверяет наличие пробельных или скрытых символов в строке.

    Args:
        string: Проверяемая строка

    Returns:
        bool: True, если найден хотя бы один пробельный символ, иначе False
    """
    return any(ch.isspace() for ch in string)


def parse_year_month_strict(value: str) -> date:
    """Парсит 'YYYY-MM' в date(YYYY, MM, 1) с жёсткой валидацией.

    Args:
        value: Строка формата YYYY-MM (строго)

    Returns:
        date: Дата с днём, выставленным в 1 число месяца

    Raises:
        ValueError: При несоответствии формату или недопустимых значениях
    """
    year_month_re = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')

    if check_hidden_or_spaces(value):
        raise ValueError(
            'Дата не должна содержать пробелы или скрытые символы',
        )

    if len(value) != 7 or not year_month_re.fullmatch(value):
        raise ValueError('Неверный формат даты: ожидается строго YYYY-MM')

    year_s, month_s = value.split('-')
    year = int(year_s)
    month = int(month_s)

    if year < 1900:
        raise ValueError('Год должен быть не меньше 1900')

    today = date.today()
    if (year, month) > (today.year, today.month):
        raise ValueError(
            'Дата не может быть в будущем (позже текущего месяца)',
        )

    return date(
        year=year,
        month=month,
        day=1,
    )
