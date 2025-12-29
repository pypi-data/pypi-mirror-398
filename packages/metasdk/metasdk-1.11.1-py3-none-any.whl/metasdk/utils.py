"""

Супер мелкие функции, которые нужны от 3 использований

"""
import hashlib
import json
import jwt
import re
from itertools import islice


def chunks_generator(iterable, count_items_in_chunk):
    """
    Очень внимательно! Не дает обходить дважды

    :param iterable:
    :param count_items_in_chunk:
    :return:
    """
    iterator = iter(iterable)
    for first in iterator:  # stops when iterator is depleted
        def chunk():  # construct generator for next chunk
            yield first  # yield element from for loop    # noqa: B023
            for more in islice(iterator, count_items_in_chunk - 1):
                yield more  # yield more elements from the iterator

        yield chunk()  # in outer generator, yield next chunk


def chunks(list_, count_items_in_chunk):
    """
    разбить list (l) на куски по n элементов

    :param list_:
    :param count_items_in_chunk:
    :return:
    """
    for i in range(0, len(list_), count_items_in_chunk):
        yield list_[i:i + count_items_in_chunk]


def pretty_json(obj):
    """
    Представить объект в вище json красиво отформатированной строки
    :param obj:
    :return:
    """
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)


def get_decode_algorithms(token: str | bytes) -> list[str]:
    """
    Получает алгоритмы декодирования токена.

    jwt.decode() требует передачи списка алгоритмов для декодирования.
    Стандратно это 'HS256' и 'RS256'. На случай другого алгоритма, проверяем заголовок токена.
    :param token: токен.
    :return: список алгоритмов.
    """
    default_algorithms = ["HS256", "RS256"]
    headers = jwt.get_unverified_header(token)
    header_alg = headers.get("alg")
    if header_alg and header_alg not in default_algorithms:
        default_algorithms.append(header_alg)
    return default_algorithms


def decode_jwt(input_text, secure_key):
    """
    Раскодирование строки на основе ключа
    :param input_text: исходная строка
    :param secure_key: секретный ключ
    :return:
    """
    if input_text is None:
        return None

    encoded = (input_text.split(":")[1]).encode('utf-8')
    algorithms = get_decode_algorithms(token=encoded)
    decoded = jwt.decode(encoded, secure_key, algorithms=algorithms)
    return decoded['sub']


def file_hash_sum(file_full_path: str) -> str:
    """
    Хэш от содержимого файла
    :param file_full_path: полный путь к файлу
    :return: Хэш строкой
    """
    with open(file_full_path, "rb") as f:
        h = hashlib.sha256()
        while True:
            data = f.read(8192)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def split_text_into_chunks(text: str, max_chunk_size: int, normalize_text: bool = True) -> list[str]:
    """
    Разбивает текст на чанки, не разрывая HTML-теги, если это возможно при заданном максимальном размере.

    :param text: Исходный текст с HTML-тегами
    :param max_chunk_size: Максимальный размер чанка (в символах)
    :return: Список чанков.
    """
    if normalize_text:
        text = text.replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("<br>", "\n").replace("<br/>", "\n")
        text = re.sub(r"<h[1-4]>", "<b>", text)
        text = re.sub(r"</h[1-4]>", "</b>", text)
        text = text.replace("<p>", "").replace("</p>", "")
        text = text.replace("&nbsp;", " ")
        text = text.replace("\n\n", "\n")
        text = text.replace("```html", "")
        text = text.replace("```", "")
        # text = re.sub(r"\n\s*\n", "\n", text)

    # Регулярное выражение для разделения текста на теги и обычный текст
    pattern = re.compile(r"(<[^>]+>)")
    parts = pattern.split(text)

    chunks = []
    current_chunk = ""

    for part in parts:
        part_length = len(part)

        # Проверяем, превышает ли добавление текущей части размер чанка
        if len(current_chunk) + part_length > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Если часть сама по себе длиннее максимального размера
            if part_length > max_chunk_size:
                # Если это не тег, разбиваем текст на более мелкие части
                if not pattern.match(part):
                    start = 0
                    while start < part_length:
                        end = start + max_chunk_size
                        chunks.append(part[start:end])
                        start = end
                else:
                    # Если это тег, помещаем его в отдельный чанк
                    chunks.append(part)
            else:
                current_chunk = part
        else:
            current_chunk += part

    # Добавляем оставшийся текст в чанки
    if current_chunk:
        chunks.append(current_chunk)

    return chunks
