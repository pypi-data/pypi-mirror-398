import asyncio
import json
from typing import Any, BinaryIO, Mapping, Optional, Sequence, TYPE_CHECKING


if TYPE_CHECKING:
    from metasdk import MetaApp
    from metasdk.transport import AsyncNativeApiTransport


class AsyncDbQueryService:
    """Асинхронный клиент для работы с БД."""

    def __init__(
        self,
        app: "MetaApp",
        options: Mapping[str, Any],
        transport: Optional["AsyncNativeApiTransport"] = None,
        owns_transport: bool = False,
    ) -> None:
        """
        Инициализирует асинхронный сервис работы с БД.

        :param app: Экземпляр MetaApp.
        :param options: Опции подключения (dbAlias, shardKey и др.).
        :param transport: Опциональный транспорт. Если не передан — берём у app.
        :param owns_transport: Закрывать ли транспорт при выходе из контекста.
        :return: None.
        """
        self.__app = app
        self.__options = options
        self.__transport = transport
        self.__owns_transport = owns_transport

    async def __aenter__(self) -> "AsyncDbQueryService":
        self._ensure_transport()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.__owns_transport and self.__transport:
            await self.__transport.aclose()
            self.__transport = None

    def _ensure_transport(self) -> "AsyncNativeApiTransport":
        if self.__transport:
            return self.__transport

        # Берём кешированный транспорт из MetaApp.
        if self.__app:
            self.__transport = self.__app.ensure_async_transport()
            return self.__transport

        raise ValueError("Async transport is not configured")

    async def schema_data(self, configuration: Mapping[str, Any]) -> dict:
        """
        Получает схему данных по конфигурации.

        :param configuration: Конфигурация запроса схемы.
        :return: Словарь с данными схемы.
        """
        params = {"configuration": json.dumps(configuration)}
        transport = self._ensure_transport()
        response = await transport.call("db", "schema-data", params, self.__options, multipart_form=True)
        return await self._json_response(response)

    async def upload_data(self, file_descriptor: BinaryIO, configuration: Mapping[str, Any]) -> dict:

        raise NotImplementedError("upload_data is temporarily disabled for async client")

    async def download_data(self, configuration: Mapping[str, Any], output_file: str) -> None:
        raise NotImplementedError("download_data is temporarily disabled for async client")

    async def batch_update(self, command: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """
        Массовая вставка/обновление записей (рекомендуется для 1-5к записей за вызов).

        :param command: SQL-команда INSERT или UPDATE.
        :param rows: Список словарей с данными строк.
        :return: Словарь с результатом операции.
        """
        request = {
            "database": {
                "alias": self.__options["dbAlias"]
            },
            "batchUpdate": {
                "command": command,
                "rows": rows,
                "shardKey": self.__options.get("shardKey"),
            }
        }
        transport = self._ensure_transport()
        response = await transport.call("db", "batch-update", request, self.__options, multipart_form=False)
        return await self._json_response(response)

    async def update(self, command: str, params: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        """
        Выполняет запросы INSERT, UPDATE, DELETE и пр., не возвращающие результата.
        Исключение — запросы с RETURNING для PostgreSQL.

        :param command: SQL-запрос.
        :param params: Параметры для prepared statements.
        :return: Словарь с результатом операции (DataResult).
        """
        request = {
            "database": {
                "alias": self.__options["dbAlias"]
            },
            "dbQuery": {
                "command": command,
                "parameters": params,
                "shardKey": self.__options.get("shardKey"),
            }
        }
        transport = self._ensure_transport()
        response = await transport.call("db", "update", request, self.__options, multipart_form=False)
        return await self._json_response(response)

    async def query(self, command: str, params: Optional[Mapping[str, Any]] = None, max_rows: int = 0) -> dict[str, Any]:
        """
        Выполняет запрос, который ОБЯЗАТЕЛЬНО должен вернуть результат.
        Для INSERT, UPDATE, DELETE используйте метод update
        или возвращайте результат через конструкцию RETURNING (недоступно в MySQL).

        Пример:
            await db.query('SELECT * FROM users WHERE id=:id', {"id": MY_USER_ID})

        :param command: SQL-запрос.
        :param params: Параметры для prepared statements.
        :param max_rows: Максимальное кол-во строк. Если запрос вернёт больше — ошибка.
                         При 0 действуют стандартные ограничения (50000).
        :return: Словарь с результатом (DataResult).
        """
        request = {
            "database": {
                "alias": self.__options["dbAlias"]
            },
            "dbQuery": {
                "maxRows": max_rows,
                "command": command,
                "parameters": params,
                "shardKey": self.__options.get("shardKey"),
            }
        }
        transport = self._ensure_transport()
        response = await transport.call("db", "query", request, self.__options, multipart_form=False)
        return await self._json_response(response)

    async def one(self, command: str, params: Optional[Mapping[str, Any]] = None) -> Optional[dict[str, Any]]:
        """
        Возвращает первую строку ответа, полученного через query.

        Пример:
            await db.one('SELECT * FROM users WHERE id=:id', {"id": MY_USER_ID})

        :param command: SQL-запрос.
        :param params: Параметры для prepared statements.
        :return: Словарь с данными первой строки или None, если результат пуст.
        """
        data = await self.query(command, params)
        rows = data.get("rows", [])
        return rows[0] if rows else None

    async def all(self, command: str, params: Optional[Mapping[str, Any]] = None) -> list[dict[str, Any]]:  # noqa: A003
        """
        Возвращает все строки ответа, полученного через query.

        Пример:
            await db.all('SELECT * FROM users WHERE id=:id', {"id": MY_USER_ID})

        :param command: SQL-запрос.
        :param params: Параметры для prepared statements.
        :return: Список словарей с данными строк.
        """
        data = await self.query(command, params)
        return data.get("rows", [])

    async def _json_response(self, response) -> dict[str, Any]:
        """
        Читает тело ответа и декодирует JSON.

        :param response: HTTP-ответ (httpx.Response).
        :return: Словарь с декодированными данными.
        """
        try:
            body = await response.aread()
            text = body.decode(response.encoding or "utf-8")
            return json.loads(text)
        finally:
            await response.aclose()

    async def _write_stream_to_file(self, response, output_file: str) -> None:
        """
        Записывает потоковый ответ в файл.

        :param response: HTTP-ответ (httpx.Response) в режиме stream.
        :param output_file: Путь к файлу для записи.
        """
        loop = asyncio.get_running_loop()
        with open(output_file, "wb") as out_file:
            async for chunk in response.aiter_bytes():
                if not chunk:
                    continue
                await loop.run_in_executor(None, out_file.write, chunk)
