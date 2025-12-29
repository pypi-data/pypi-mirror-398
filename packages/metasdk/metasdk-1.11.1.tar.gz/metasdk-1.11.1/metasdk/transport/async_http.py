import asyncio
import json
from typing import Any, Callable, Optional

import httpx

from metasdk.exceptions import ServerError
from metasdk.logger.logger import Logger
from metasdk.services import process_meta_api_error_code


class AsyncNativeApiTransport:
    """
    Независимый от MetaApp асинхронный транспорт для вызова native API.

    Использует httpx.AsyncClient для выполнения HTTP-запросов с поддержкой
    повторных попыток при сетевых ошибках и ошибках сервера.
    """

    def __init__(
        self,
        meta_url: str,
        default_headers: dict[str, str],
        logger: Logger,
        auth_user_id_supplier: Optional[Callable[[], Optional[int]]] = None,
        *,
        max_attempts: int = 10,
        retry_sleep_sec: int = 15,
    ) -> None:
        """
        Инициализирует асинхронный транспорт.

        :param meta_url: Базовый URL META API (например, https://apimeta.devision.io).
        :param default_headers: Словарь заголовков по умолчанию для всех запросов.
        :param logger: Экземпляр логгера для записи предупреждений и ошибок.
        :param auth_user_id_supplier: Опциональный callable,
            возвращающий ID пользователя для заголовка X-META-AuthUserID.
        :param max_attempts: Максимальное количество попыток при ошибках (по умолчанию 10).
        :param retry_sleep_sec: Время ожидания между попытками в секундах (по умолчанию 15).

        :return: None.
        """
        self._meta_url = meta_url.rstrip("/")
        self._default_headers = dict(default_headers or {})
        self._log = logger
        self._auth_user_id_supplier = auth_user_id_supplier
        self._max_attempts = max_attempts
        self._retry_sleep_sec = retry_sleep_sec
        self._client = httpx.AsyncClient()

    async def aclose(self) -> None:
        """
        Закрывает HTTP-клиент и освобождает ресурсы.

        Обязательно вызывайте этот метод по завершении работы с транспортом,
        чтобы корректно закрыть все TCP-соединения.

        :return: None.
        """
        await self._client.aclose()

    async def call(
        self,
        service: str,
        method: str,
        data: Optional[dict[str, Any]],
        options: Optional[dict[str, Any]],
        multipart_form: bool = False,
        multipart_form_data: Optional[dict[str, Any]] = None,
        stream: bool = False,
        http_path: str = "/api/meta/v1/",
        http_method: str = "POST",
        get_params: Optional[dict[str, Any]] = None,
        connect_timeout_sec: int = 60,
        request_timeout_sec: int = 1800,
    ) -> httpx.Response:
        """
        Выполняет асинхронный HTTP-запрос к META API.

        :param service: Название сервиса (например, "db", "metaql").
        :param method: Метод сервиса (например, "query", "update").
        :param data: Данные запроса (тело).
        :param options: Дополнительные опции, которые будут добавлены в тело запроса.
        :param multipart_form: Флаг отправки данных в формате multipart/form-data.
        :param multipart_form_data: Файлы для multipart-запроса.
        :param stream: Флаг потоковой передачи ответа.
        :param http_path: HTTP-путь к API (по умолчанию "/api/meta/v1/").
        :param http_method: HTTP-метод (по умолчанию "POST").
        :param get_params: GET-параметры запроса.
        :param connect_timeout_sec: Таймаут подключения в секундах (по умолчанию 60).
        :param request_timeout_sec: Таймаут запроса в секундах (по умолчанию 1800).
        :return: httpx.Response с ответом сервера.
        :raises ServerError: При исчерпании попыток из-за ошибок сервера.
        :raises RequestError: При ошибках клиента (4xx).
        :raises AuthError: При ошибке авторизации (401).
        """
        payload: dict[str, Any] = dict(data or {})
        if "self" in payload:
            payload.pop("self")
        if options:
            payload.update(options)

        params = dict(get_params or {})
        headers = self._build_headers()
        url = self._compose_url(http_path, service, method)

        request_context = {
            "url": url,
            "method": http_method,
            "headers": headers,
            "params": params,
            "timeout": (connect_timeout_sec, request_timeout_sec),
            "stream": stream,
        }

        body_kwargs: dict[str, Any]
        if multipart_form:
            headers.pop("content-type", None)
            body_kwargs = {"data": payload}
            if multipart_form_data:
                body_kwargs["files"] = multipart_form_data
        else:
            body_kwargs = {"content": json.dumps(payload)}

        timeout = httpx.Timeout(request_timeout_sec, connect=connect_timeout_sec)
        last_exception: Exception = ServerError(request_context)

        for _ in range(self._max_attempts):
            try:
                request = self._client.build_request(
                    http_method,
                    url,
                    headers=dict(headers),
                    params=params,
                    **body_kwargs,
                )
                request.extensions["timeout"] = timeout.as_dict()
                response = await self._client.send(request, stream=stream)
                self._log.set_entity("request_id", response.headers.get("request_id"))
                if response.status_code == 200:
                    return response

                await response.aread()
                process_meta_api_error_code(response.status_code, request_context, response.text)
            except (httpx.TransportError, ConnectionError, TimeoutError) as exc:
                self._log.warning("META API Connection Error. Sleep...", {"e": exc})
                await asyncio.sleep(self._retry_sleep_sec)
            except ServerError as exc:
                last_exception = exc
                self._log.warning("META Server Error. Sleep...", {"e": exc})
                await asyncio.sleep(self._retry_sleep_sec)
            except Exception as exc:
                if "Служба частично или полностью недоступна" in str(exc):
                    self._log.warning("META API Service Temporarily Unavailable. Sleep...", {"e": exc})
                    await asyncio.sleep(self._retry_sleep_sec)
                else:
                    raise
            finally:
                self._log.set_entity("request_id", None)

        raise last_exception

    def _build_headers(self) -> dict[str, str]:
        """
        Формирует заголовки для запроса.

        Добавляет X-META-AuthUserID, если задан auth_user_id_supplier.

        :return: Словарь заголовков.
        """
        headers = dict(self._default_headers)
        auth_user_id = self._auth_user_id_supplier() if self._auth_user_id_supplier else None
        if auth_user_id:
            headers["X-META-AuthUserID"] = str(auth_user_id)
        return headers

    def _compose_url(self, http_path: str, service: str, method: str) -> str:
        """
        Собирает полный URL для запроса.

        :param http_path: Базовый путь API.
        :param service: Название сервиса.
        :param method: Метод сервиса.
        :return: Полный URL.
        """
        path = http_path or "/"
        if not path.endswith("/"):
            path += "/"
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._meta_url}{path}{service}/{method}"
