import json
from typing import Any, TYPE_CHECKING

from requests import Response


if TYPE_CHECKING:
    from metasdk import MetaApp


class MediaService:
    def __init__(self, app: "MetaApp") -> None:
        """
        Инициализирует сервис для работы с медиафайлами.

        :param app: Объект MetaApp.
        :return: None.
        """
        self.__app = app
        self.__options: dict[str, Any] = {}

    def persist_one(
        self,
        file_base64_content: str,
        filename: str,
        extension: str,
        mime: str,
        is_private: bool = True,
    ) -> dict[str, Any]:
        """
        Загружает файл в облако.

        :param file_base64_content: Содержимое файла в формате base64.
        :param filename: Имя файла.
        :param extension: Расширение файла.
        :param mime: MIME-тип файла.
        :param is_private: Флаг, указывающий, является ли файл приватным.
        :return: Словарь с ответом от сервера.
        """
        return self.__app.api_call("MediaService", "persist_one", locals(), {})

    def upload(self, file_descriptor: str, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Загружает файл в облако.

        :param file_descriptor: Открытый дескриптор.
        :param settings: Настройки загрузки.
        :return: Словарь с ответом от сервера.
        """
        multipart_form_data = {"file": file_descriptor}
        params = {"settings": json.dumps(settings)}
        dr = self.__app.native_api_call(
            service="media",
            method="upload",
            data=params,
            options=self.__options,
            multipart_form=True,
            multipart_form_data=multipart_form_data,
            stream=False,
            http_path="/api/meta/v1/",
            http_method="POST",
            connect_timeout_sec=60 * 10,
        )
        return json.loads(dr.text)

    def download(self, media_id: str, as_stream: bool = False) -> Response:
        """
        Скачивает указанный файл.

        :param media_id: Идентификатор медиафайла.
        :param as_stream: Флаг необходимости потокового скачивания.
        :return: Ответ от сервера (объект Response библиотеки requests).
        """
        response = self.__app.native_api_call(
            service="media",
            method="d/" + media_id,
            data={},
            options=self.__options,
            multipart_form=False,
            multipart_form_data=None,
            stream=as_stream,
            http_path="/api/meta/v1/",
            http_method="GET",
        )
        return response

    def info(self, media_id: str) -> dict[str, Any]:
        """
        Возвращает информацию по файлу.

        :param media_id: Идентификатор медиафайла.
        :return: Словарь с информацией о файле.
        """
        dr = self.__app.native_api_call(
            service="media",
            method="i/" + media_id,
            data={},
            options=self.__options,
            multipart_form=False,
            multipart_form_data=None,
            stream=False,
            http_path="/api/meta/v1/",
            http_method="GET",
        )
        return json.loads(dr.text)
