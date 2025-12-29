json_fields = ["form_data", "result"]


def convert_dot_notation_to_pg_jsonpath_format(json_string: str) -> str:
    """
    Преобразует строку с точечной нотацией в формат JSONPath для PostgreSQL.

    Пример:
    'amount.1.rub' -> "'{amount, 1, rub}'"

    :param json_string: str - строка в точечной нотации, представляющая путь к элементу JSON.
    :return: str - строка в формате JSONPath для PostgreSQL.
    """
    return "'{" + ", ".join(json_string.split(".")) + "}'"


def get_bind_params(**kwargs) -> tuple[str, dict[str, str]]:
    """
    Генерирует строку параметров и соответствующие значения для использования в SQL-запросах.

    Эта функция принимает произвольные именованные аргументы, представляющие родительские ключи и их значения.
    Она создает плейсхолдеры для SQL-запроса и собирает значения в словарь.

    :param kwargs: произвольное количество именованных аргументов, где ключи - это родительские параметры, 
                   а значения - это словари с подлежащими значениями.

    :return: tuple[str, dict[str, str]] - кортеж, содержащий строку плейсхолдеров и словарь значений.

    Пример использования:

    >>> placeholders, values = get_bind_params(amount={"1": 100, "2": 200}, currency={"1": "RUB"})
    >>> print(placeholders)
    AND replace((amount #> string_to_array(:amount_key_0::text, '.'))::text, '\"', '') = :amount_value_0::text
    AND replace((amount #> string_to_array(:amount_key_1::text, '.'))::text, '\"', '') = :amount_value_1::text
    AND replace((currency #> string_to_array(:currency_key_0::text, '.'))::text, '\"', '') = :currency_value_0::text
    >>> print(values)
    {'amount_key_0': '1', 'amount_value_0': '100', 'amount_key_1': '2', 'amount_value_1': '200', 'currency_key_0': '1', 'currency_value_0': 'RUB'}
    """
    placeholders = ""
    values = {}

    for i, parent in enumerate(json_fields):
        path_values = kwargs.get(parent)
        if not path_values:
            continue

        for path, value in path_values.items():
            placeholder_key = f"{parent}_key_{i}"
            placeholder_value = f"{parent}_value_{i}"
            placeholders += f"AND replace(({parent} #> string_to_array(:{placeholder_key}::text, '.'))::text, '\"', '') = :{placeholder_value}::text\n"
            values |= {
                placeholder_key: path,
                placeholder_value: value
            }

    return placeholders, values
