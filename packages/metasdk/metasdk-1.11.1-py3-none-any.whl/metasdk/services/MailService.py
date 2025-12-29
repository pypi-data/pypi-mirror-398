import json

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Mapping, Optional, TYPE_CHECKING
from uuid import UUID


if TYPE_CHECKING:
    from metasdk.MetaApp import MetaApp  # type: ignore


class Message(ABC):
    """Абстрактный класс сообщения"""
    messenger_id = "abstract"

    @abstractmethod
    def generate_unique_id(self) -> str:
        """
        Генерирует уникальный идентификатор сообщения по его атрибутам.

        Абстрактный метод. В наследниках необходимо переопределить.
        :return: Уникальный идентификатор сообщения.
        """
        pass

    def __init__(
        self,
        user_id: str,
        body: str,
        template: str = "",
        unique_id: Optional[str] = None,
        author_user_id: Optional[int] = None,
        sender_id: Optional[str] = None,
        message_extra: Optional[Mapping[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Инициализирует экземпляр класса.

        :param user_id: Идентификатор пользователя-адресата.
        :param body: Строка с телом отправляемого сообщения.
        :param template: Идентификатор шаблона сообщения.
        :param unique_id: Уникальный идентификатор сообщения.
        :param author_user_id: Идентификатор автора сообщения.
        :param sender_id: Идентификатор отправителя.
        :param message_extra: Дополнительные параметры сообщения.
        :param kwargs: Опциональные параметры, актуальные для отдельных каналов отправки сообщений.
        :return: None.
        """
        self._messenger = self.messenger_id
        self._user_id = user_id
        self._body = body
        self._template = template
        self._custom_unique_id = unique_id
        self._author_user_id = author_user_id
        self._sender_id = sender_id
        self._message_extra = message_extra
        self._kwargs = kwargs

    def to_dict(self) -> dict[str, str | int | None]:
        """
        Возвращает словарь с данными сообщения.

        :return: Словарь с данными сообщения. Удобно передавать методам DbQueryService.
        """
        sender_info = {}
        if self._sender_id:
            sender_info["id"] = self._sender_id

        if self._message_extra:
            message_extra = self._message_extra
        else:
            message_extra = {}

        return {
            "messenger": self._messenger,
            "user_id": self._user_id,
            "body": self._body,
            "template": self._template,
            "unique_id": self._custom_unique_id or self.generate_unique_id(),
            "author_user_id": self._author_user_id,
            "sender_info": json.dumps(sender_info),
            "message_extra": json.dumps(message_extra),
        }


class WebhookMessage(Message):
    """Класс сообщения, отправляемого вебхуком"""
    messenger_id = "webhook"

    def generate_unique_id(self) -> str:
        """
        Генерирует уникальный идентификатор сообщения по его атрибутам.

        В kwargs экземпляра можно передать параметр "uniqualizer",
        и он будет добавлен в начало unique_id. Так, скажем, можно проверять,
        был ли уже отправлен вебхук по конкретной записи из meta.object_log. 
        :return: Уникальный идентификатор сообщения.
        """
        unique_id_head = "webhook"
        if uniqualizer := self._kwargs.get("uniqualizer"):
            unique_id_head += f"_{uniqualizer}"       
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        return f"{unique_id_head}_{self._user_id}_{timestamp}"


class TelegramMessage(Message):
    """Класс сообщения, отправляемого через Telegram"""
    messenger_id = "telegram"

    def __init__(
        self, 
        user_id: str, 
        body: str, 
        sender_id: str = "80a5b860-683e-4afd-9733-572826bbac1e",  # https://t.me/Garpun_bot
        template: str = "", 
        unique_id: Optional[str] = None, 
        author_user_id: Optional[int] = None, 
        **kwargs: Any,
    ) -> None:
        """
        Инициализирует экземпляр класса.

        :param user_id: Идентификатор пользователя-адресата.
        :param body: Строка с телом отправляемого сообщения.
        :param sender_id: Идентификатор отправителя (бота в таблице bot.telegram_bot).
        :param template: Идентификатор шаблона сообщения.
        :param unique_id: Уникальный идентификатор сообщения.
        :param author_user_id: Идентификатор автора сообщения.
        :param message_extra: Дополнительные параметры сообщения. Примеры таких параметров для Telegram:
            - "inline_buttons" (list) — список кнопок для встраивания в сообщение;
            - "keep_formatting" (bool) — если True, форматирование сообщения будет сохранено в неизменном виде;
            - "ignore_queue" (bool) — если True, сообщение не будет добавлено в очередь на отправку.
            - "parse_mode" (str) — режим парсинга сообщения на стороне Telegram (по умолчанию "HTML").
            - "image_url" (str) — URL изображения для встраивания в сообщение.
            - "sticker_id" (str) — ID стикера для встраивания в сообщение. Если передан, будет отправлен только стикер,
                так как, в отличие от изображений, к стикеру нельзя прикрепить текст.
        :param kwargs: Опциональные параметры, актуальные для отдельных каналов отправки сообщений.
        :return: None.
        """
        try:
            UUID(sender_id)
        except ValueError:
            raise ValueError("Invalid sender_id")
        super().__init__(user_id, body, template, unique_id, author_user_id, sender_id, **kwargs)

    def generate_unique_id(self) -> str:
        """
        Генерирует уникальный идентификатор сообщения по его атрибутам.

        :return: Уникальный идентификатор сообщения.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        return f"custom_message_{self._user_id}_{timestamp}_{self._sender_id}"


class MailService:
    def __init__(self, app: "MetaApp") -> None:
        """
        Инициализирует экземпляр класса MailService.

        :param app: Экземпляр приложения MetaApp.
        :return: None.
        """
        self.__app = app
        self.__options: dict[str, Any] = {}
        self.__data_get_cache: dict[str, Any] = {}
        self.__metadb = app.db("meta")
        self.log = app.log

    def submit_mail(
        self,
        send_from: str,
        send_to: str,
        subject: str,
        body: str,
        unique_id: Optional[str] = None,
    ) -> None:
        """
        Добавляет письмо в очередь на отправку (фактически — запись в таблицу meta.mail).

        :param send_from: Отправитель.
        :param send_to: Получатель.
        :param subject: Тема письма.
        :param body: Тело письма. Можно с HTML.
        :param unique_id: Уникальный идентификатор письма.
            Лучше всего подойдет md5 + человекочитаемый префикс.
            Письмо с существующим unique_id не будут добавлено.
        :return: None.
        """
        self.__metadb.update(
            """
                INSERT INTO meta.mail(
                    "template",
                    "from",
                    "to",
                    "subject",
                    "body",
                    "attachments",
                    "unique_id"
                )
                VALUES ('meta', :send_from, :send_to, :subject, :body, null, :unique_id)
                ON CONFLICT (unique_id) DO NOTHING
            """,
            {
                "send_from": send_from,
                "send_to": send_to,
                "subject": subject,
                "body": body,
                "unique_id": unique_id,
            },
        )

    def submit_message(self, message: Message) -> str | None:
        """
        Добавляет сообщение в очередь на отправку (фактически — запись в таблицу meta.messenger).

        :param message: Экземпляр класса сообщения (наследника Message).
        :return: id записи в таблице meta.messenger или None, если не удалось добавить запись.
        """
        insert_query_result = self.__metadb.one(
            """
                INSERT INTO meta.messenger(
                    messenger,
                    user_id,
                    body,
                    unique_id,
                    author_user_id, 
                    sender_info,
                    message_extra
                )
                VALUES (
                    :messenger::text,
                    :user_id::text,
                    :body::text,
                    :unique_id::text,
                    COALESCE(:author_user_id, valera_user_id())::bigint,
                    :sender_info::jsonb,
                    :message_extra::jsonb
                )
                ON CONFLICT (unique_id) DO NOTHING
                RETURNING id
            """,
            message.to_dict(),
        )
        return insert_query_result.get("id") if insert_query_result else None


class TelegramUtils:
    """Класс вспомогательных методов для работы с Telegram"""
    def __init__(self, app: "MetaApp") -> None:
        """
        Инициализирует экземпляр класса.

        :param app: Экземпляр приложения MetaApp.
        :return: None.
        """
        self.__app = app
        self.__metadb = self.__app.db("meta")
        self.__log = self.__app.log

    def get_bot_token(self, bot_id: str) -> str | None:
        """
        Получает токен бота по его идентификатору.

        :param bot_id: Идентификатор бота.
        :return: Токен бота либо None, если бот не найден.
        """
        token_query_result = self.__metadb.one(
            """
            SELECT token
            FROM bot.telegram_bot
            WHERE id = :bot_id::uuid
            LIMIT 1
            """,
            {"bot_id": bot_id},
        )
        return token_query_result.get("token") if token_query_result else None

    def submit_message_deprecated(self, user_id: int, msg: str) -> bool:
        """
        Отправляет уведомление пользователю в Telegram от @RealwebIntranetBot.

        С отключением сервиса бота функция потеряет актуальность и будет удалена.
        Не рекомендуется использовать в новых службах и сервисах.
        :param user_id: ID пользователя в META.
        :param msg: Сообщение для отправки.
        :return: True, если сообщение отправлено успешно, иначе False.
        """
        notification_result = self.__metadb.one(
            """
            SELECT *
            FROM api.telegram_bot_rw_request(
                'message/send',
                json_build_object(
                    'userId', (SELECT intranet_id FROM public.users WHERE id=:user_id::bigint LIMIT 1),
                    'messages', json_build_array(json_build_object('text', :msg))
                )
            )
            """,
            {"user_id": user_id, "msg": msg},
        )

        if "DATA_ERROR" in str(notification_result):
            self.__log.warning(
                "При отправке сообщения произошла ошибка",
                {"user_id": user_id, "result": notification_result},
            )
            return False
        else:
            self.__log.info(
                "Сообщение от RealwebIntranetBot отправлено",
                {"user_id": user_id, "result": notification_result},
            )
            return True

    def fetch_user_telegram_id(
        self,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        strict: bool = False,
    ) -> int | None:
        """
        Получает Telegram ID пользователя по его ID в META или e-mail.

        :param user_id: ID пользователя в META (В первую очередь поиск идет по нему).
        :param user_email: E-mail пользователя (Вторая очередь поиска, только по юзерам с company_id = 1).
        :param strict: Флаг, определяющий режим поиска (По умолчанию False).
            Если True и переданы оба параметра, проверка будет производиться на соответствие обоим.
            Если False и переданы оба параметра, будет возвращен первый найденный Telegram ID.
        :return: Telegram ID пользователя либо None, если пользователь не найден.
        """
        if user_id is None and user_email is None:
            raise ValueError("Необходимо передать хотя бы один из параметров: user_id или user_email")
        target_telegram_id = None

        if user_id is not None:
            user_by_id_query = self.__metadb.one(
                """
                SELECT
                    pu.id AS meta_id,
                    pu.telegram_id AS telegram_id,
                    pu.email AS meta_email,
                    CONCAT(pu.info->'intranet'->>'domain_id', '@realweb.ru') AS domain_email
                FROM public.users pu
                WHERE id = :user_id::bigint
                """,
                {"user_id": user_id},
            )
            target_telegram_id = user_by_id_query.get("telegram_id") if user_by_id_query else None
            if target_telegram_id and not strict:
                return target_telegram_id

        # Сюда мы попадаем, если user_id не передан или по нему не найден Telegram ID либо при строгом поиске
        if user_email is not None:
            users_by_email_query = self.__metadb.all(
                """
                SELECT
                    pu.id AS meta_id,
                    pu.telegram_id AS telegram_id,
                    pu.email AS meta_email,
                    CONCAT(pu.info->'intranet'->>'domain_id', '@realweb.ru') AS domain_email
                FROM public.users pu
                WHERE
                    (
                        CONCAT(pu.info->'intranet'->>'domain_id', '@realweb.ru') = :user_email::text
                        OR pu.email = :user_email::text
                    )
                    AND pu.company_id = 1
                """,
                {"user_email": user_email},
            )
            if strict and target_telegram_id:
                if target_telegram_id in [user["telegram_id"] for user in users_by_email_query]:
                    return target_telegram_id
                else:
                    return None
            elif not strict:
                results_with_telegram_id = [result for result in users_by_email_query if result.get("telegram_id")]
                if results_with_telegram_id:
                    return results_with_telegram_id[0].get("telegram_id")
                else:
                    return None
        # Если вообще ничего не найдено, возвращаем None
        return None

    def is_bot_subscriber(self, bot_id: str, telegram_id: int) -> bool:
        """
        Проверяет, подписан ли пользователь на бота.

        Актуально только для ботов бот-платформы, для которых собирается информация о подписчиках.
        :param bot_id: Идентификатор бота.
        :param telegram_id: Telegram ID пользователя.
        :return: True, если пользователь подписан на бота, иначе False.
        """
        is_subscriber_query_result = self.__metadb.one(
            """
            SELECT
                EXISTS (
                    SELECT 1
                    FROM bot.subscriber
                    WHERE
                        bot_id = :bot_id::uuid
                        AND status = 'active'
                        AND remote_id=:telegram_id::bigint
                ) AS is_bot_subscriber
            """,
            {"telegram_id": telegram_id, "bot_id": bot_id},
        )
        return is_subscriber_query_result.get("is_bot_subscriber", False) if is_subscriber_query_result else False
