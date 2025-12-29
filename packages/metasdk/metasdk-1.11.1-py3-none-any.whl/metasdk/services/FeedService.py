import functools
import json
import re
from tempfile import NamedTemporaryFile

import sqlparse

from metasdk.exceptions import BadParametersError, ForbiddenError
from metasdk.services.AuthService import AuthUserInfo


SOURCE_FORMAT_EXTENSION = {
    "CSV": ".csv",
    "TSV": ".tsv",
    "JSON_NEWLINE": ".json",
}


def auth_required(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        auth_info = self.auth_service.verify_access_token(self.token, self.required_scopes)
        user_info = auth_info["author_info"]
        self.auth_user_info = user_info

        if kwargs.get("feed_id"):
            self.check_feed_permissions(feed_id=kwargs["feed_id"], auth_user_info=user_info)
        if kwargs.get("task_id"):
            self.check_task_permissions(task_id=kwargs["task_id"], auth_user_info=user_info)
        return func(self, *args, **kwargs)
    return wrapper


class FeedService:
    def __init__(self, app, token: str = ""):
        """
        :type app: metasdk.MetaApp
        """
        self.__app = app
        self.__options = {}
        self.__data_get_cache = {}
        self.__data_get_flatten_cache = {}
        self.__metadb = app.db("meta")
        self.__media = app.MediaService
        self.__starter = app.StarterService
        self.auth_service = app.AuthService
        self.token = token
        self.required_scopes = ["datahub"]
        self.auth_user_info = None

    def _generate_feed_permissions_check_query(self) -> str:
        """
        Генерирует SQL запрос для проверки прав на фид.

        Пользователь может получить доступ, если:
        - он автор фида
        - есть доступ по billing_client_id
        - с ним поделились фидом

        "fd" - это алиас таблицы meta.feed_datasource
        :return: SQL запрос.
        """
        check_author_id = "fd.author_user_id = :auth_user_id::int8"
        check_billing_client_id = """
         fd.billing_client_id IN (
            SELECT client_id 
            FROM get_user_clients(:auth_user_id::int8)
        )
        """
        check_feed_sharings = """
        fd.id::text IN (
            SELECT object_id 
            FROM meta.object_share 
            WHERE 
                active 
                AND entity_id = '2770' 
                AND user_id = :auth_user_id::int8
        )
        """
        query = f"({check_author_id} OR {check_billing_client_id} OR {check_feed_sharings})"
        return sqlparse.format(query, reindent=True)

    def check_feed_permissions(self, feed_id: str, auth_user_info: AuthUserInfo) -> bool:
        """
        Проверяет права доступа к фиду.

        Если пользователь админ, то проверяется принадлежность фида к его компании.
        Если без прав админа, то пользователб должен быть автором фида.

        Если feed_id не существует, также вызываем исключение ForbiddenError.
        :param feed_id: ID фида.
        :param auth_user_info: данные о пользователе, предоставившем валидный токен.
        :return: True, если есть доступ к фиду, иначе - исключение ForbiddenError.
        """
        query_params = {"feed_id": feed_id, "auth_user_id": auth_user_info["auth_user_id"]}

        permission_check_query = self._generate_feed_permissions_check_query()
        query = f"""
        SELECT
            fd.id AS feed_id
        FROM meta.feed_datasource fd
        LEFT JOIN public.users us ON fd.author_user_id =us.id
        WHERE 
            fd.id = :feed_id::uuid
            AND {permission_check_query}
        """
        result = self.__metadb.one(query, query_params)
        if result and result["feed_id"]:
            return True
        else:
            raise ForbiddenError("Do not have permissions to access this feed")

    def check_task_permissions(self, task_id: str, auth_user_info: AuthUserInfo) -> bool:
        """
        Проверяет права доступа к таску.

        Таск запускается в рамках фида, поэтому проверяем права доступа к фиду.
        :param task_id: ID таска.
        :param auth_user_info: данные о пользователе, предоставившем валидный токен.
        :return: True, если есть доступ к фиду, иначе - исключение ForbiddenError.
        """
        query = "SELECT data ->> 'ds_id' AS feed_id FROM job.task WHERE id = :task_id::uuid"
        result = self.__metadb.one(query, params={"task_id": task_id})
        if result:
            feed_id = result["feed_id"]
            return self.check_feed_permissions(feed_id, auth_user_info)
        else:
            raise ForbiddenError("Do not have permissions to access this feed")

    def get_feed(self, datasource_id: str):
        """
        Получение настроек для фида
        :param datasource_id: идентификатор фида
        :return: FeedDataSource
        """
        info = self.__metadb.one(
            """
            SELECT to_json(ds) as datasource
                 , to_json(fc) as connector
                 , to_json(fct) as connector_type
                 , to_json(ctp) as connector_type_preset
                 , json_build_object('email', u.email, 'full_name', u.full_name) as author_user
                 , json_build_object('id', fst.id, 'alias', fst.alias) as share_type
              FROM meta.feed_datasource ds
              LEFT JOIN meta.feed_connector fc 
                     ON fc.id=ds.connector_id
              LEFT JOIN meta.feed_connector_type fct 
                     ON fct.id=fc.connector_type_id
              LEFT JOIN meta.feed_connector_type_preset ctp 
                     ON ctp.id=ds.connector_type_preset_id
              LEFT JOIN meta.user_list u 
                     ON u.id=ds.author_user_id
              LEFT JOIN meta.feed_share_type fst 
                     ON fst.id = ds.share_type_id
             WHERE ds.id = :datasource_id::uuid
            """,
            {"datasource_id": datasource_id}
        )
        return FeedDataSource(**info)

    def get_data(self, datasource, callback):
        """
        Сохранение медиафайла
        :param task:
        :param media_metadata:
        :param file_suffix:
        :param callback:
        :return:
        """
        task = self.__app.worker.current_task
        media_metadata = datasource.connector_type_preset["preset_data"]["media_metadata"]
        result_data = task["result_data"]
        tmp_file = NamedTemporaryFile(delete=False, suffix=SOURCE_FORMAT_EXTENSION.get(media_metadata["sourceFormat"]))
        self.__app.log.info("Открываем файл", {"filename": tmp_file.name})
        with open(tmp_file.name, "wb") as f:
            callback(f)

        self.__app.log.info("start media upload")

        result_data["stage_id"] = "persist_media_file"
        self.__starter.update_task_result_data(task)
        result = self.__media.upload(open(tmp_file.name), {
            "ttlInSec": 60 * 60 * 24,  # 24h
            "entityId": 2770,
            "objectId": task.get("data", {}).get("ds_id"),
            "info": {"metadata": media_metadata},
        })

        result_data["stage_id"] = "generate_media_finish"
        result_data["media_id"] = result["id"]
        self.__starter.update_task_result_data(task)

        return result

    def datasource_process(self, datasource_id: str):
        """
        deprecated
        Запускает настроенные обработки в фиде
        :param datasource_id: uuid
        """
        # TODO Выпилить потом класс используется для другого
        # TODO без applicationId не выбираются поля сущностей. Подумать на сколько это НЕ нормально
        response = self.__app.native_api_call("feed", "datasource/" + datasource_id + "/process?applicationId=1", {},
                                              self.__options, False, None, False, http_method="POST")
        return json.loads(response.text)

    @auth_required
    def list_feeds(self, filters: dict) -> list[dict]:
        """
        Получает список фидов юзера.

        :param filters: поля для фильтрации запроса. Формат '{column_name: filter_value}'.
        :param token: токен авторизации.
        :return: список фидов.
        """
        if not isinstance(filters, dict):
            msg = "filters должен быть словарём, в котором key - это название столбца, а value значение фильтрации"
            raise TypeError(msg)
        query = self._generate_list_feeds_query(filters=filters)
        query_params = {**filters, **self.auth_user_info}
        feeds = self.__metadb.all(command=query, params=query_params)
        return feeds

    def _generate_list_feeds_query(self, filters: dict = None) -> str:
        """
        Генерирует SQL запрос для получения списка фидов.

        :param filters: поля для фильтрации запроса. Формат '{column_name: filter_value}'.
        :return: SQL запрос.
        """
        permission_check_query = self._generate_feed_permissions_check_query()
        base_query = f"""
        SELECT
            fd.id,
            fd.name,
            fd.user_status,
            fd.state,
            fd.last_launch_time,
            fd.is_automated,
            fd.tags,
            us.company_id 
        FROM meta.feed_datasource AS fd
        LEFT JOIN public.users AS us ON fd.author_user_id =us.id
        WHERE {permission_check_query}
        """
        filters_query = self._generate_filters_query(filters=filters)
        final_query = f"{base_query} {filters_query}"
        return sqlparse.format(final_query, reindent=True)

    def _generate_tags_query(self, tags: list[str]) -> str:
        """
        Гененрирует SQL запрос для фильтрации по полю tags.

        :param tags: список тэгов фида.
        :return: часть SQL запроса с фильтрацией по тэгам.
        """
        if not isinstance(tags, list):
            raise TypeError("Wrong format. Expected list of strings")

        if not tags:
            raise ValueError("tags cannot be empty")

        tags_expr = []
        for tag in tags:
            # обработка спец символов
            tag_escaped = re.escape(tag)
            tag = f"""tags @> array['{tag_escaped}']"""
            tags_expr.append(tag)
        return " OR ".join(tags_expr)

    def _generate_filters_query(self, filters: dict = None) -> str:
        """
        Гененирует SQL запрос со значениями фильтров.

        :param filters: поля для фильтрации запроса. Формат '{column_name: filter_value}'.
        :return: часть SQL запроса с фильтрами для вставки в WHERE.
        """
        if not filters:
            return ""

        special_types = {
            "state": "meta.feed_datasource_state_type",
            "user_status": "meta.user_status_type",
            "parent_id": "uuid",
            "share_type_id": "uuid",
            "connector_id": "uuid",
            "connector_type_id": "uuid",
            "connector_type_preset_id": "uuid",
        }
        filters_sql = []
        for key, value in filters.items():
            if key == "tags":
                tags = self._generate_tags_query(tags=value)
                filter_expr = f"AND {tags}"
            else:
                if special_types.get(key):
                    filter_expr = f"AND {key} = :{key}::{special_types[key]}"
                else:
                    filter_expr = f"AND {key} = :{key}"
            filters_sql.append(filter_expr)
        return " ".join(filters_sql)

    @auth_required
    def get_feed_by_id(self, feed_id: str, last_tasks: bool = False) -> dict:
        """
        Получает данные о конкретном фиде.

        :param feed_id: ID фида.
        :param token: токен авторизации.
        :param last_tasks: если True, то возвращает ID последних тасков фида в поле last_tasks.
        :return: данные о фиде.
        """
        if not feed_id:
            raise ValueError("'feed_id' is required")

        query_params = {"feed_id": feed_id}
        query = self._generate_feed_by_id_query(last_tasks=last_tasks)
        feed = self.__metadb.one(query, query_params)
        return feed

    def _generate_feed_by_id_query(self, last_tasks: bool = False) -> str:
        """
        Генерирует SQL запрос для получения данных о фиде.

        Запрос дополнитено фильтруется по author_user_id, а не только по feed_id,
        чтобы ограничить доступ юзеров не к своим фидам.

        Для получения списка последних тасков дополнительно обращается к таблице 'job.task'.
        :param last_tasks: если True, то возвращает ID последних тасков фида в поле last_tasks.
        :return: SQL запрос для получения данных о фиде.
        """
        base_feed_columns = [
            "id", "name", "user_status", "state", "last_launch_time", "is_automated", "tags",
            "creation_time", "modification_time", "author_user_id", "last_user_id", "schedules",
            "connector_type_id", "connector_settings_form_data", "connector_type_preset_id",
            "share_type_id", "share_settings_form_data", "parent_id", "billing_client_id", "feed_data",
        ]
        base_feed_cols_query = [f"fd.{col}" for col in base_feed_columns]
        base_feed_cols_query = ", ".join(base_feed_cols_query)
        base_query = f"""
        SELECT
            {base_feed_cols_query},
            fct.name as connector_type_name,
            ctp.name as connector_type_preset_name,
            fst.name as share_type_name,
            us.company_id
        FROM meta.feed_datasource fd
        LEFT JOIN meta.feed_connector_type fct ON fct.id=fd.connector_type_id
        LEFT JOIN meta.feed_share_type fst ON fst.id = fd.share_type_id
        LEFT JOIN meta.feed_connector_type_preset ctp ON ctp.id = fd.connector_type_preset_id
        LEFT JOIN public.users us ON fd.author_user_id =us.id
        WHERE fd.id = :feed_id::uuid
        """

        if last_tasks:
            last_tasks_query = self._generate_last_tasks_query()
            base_query = f"""
            WITH feed_data AS (
            {base_query}
            ),
            {last_tasks_query}
            SELECT
                {base_feed_cols_query},
                fd.connector_type_name,
                fd.connector_type_preset_name,
                fd.share_type_name,
                aggt.last_tasks
            FROM feed_data fd
            LEFT JOIN agg_tasks aggt ON aggt.ds_id = fd.id
            """
        return sqlparse.format(base_query, reindent=True)

    def _generate_last_tasks_query(self) -> str:
        """
        Генерирет SQL запрос для получения последних тасков фида.

        Таски сортируются по 'creation_time'.
        Кол-во возвращаемых тасков регулируется переменной 'n_last_tasks'.
        :param feed_id: ID фида.
        :return: часть SQL запроса для получения последних тасков фида
        """
        n_last_tasks = 2
        base_query = f"""
        last_tasks AS (
           SELECT 
             id, 
             ("data" ->> 'ds_id')::uuid as ds_id 
           FROM job.task
           WHERE "service_id" = 'meta.datasource_share' AND "data" ->> 'ds_id' = :feed_id::text
           ORDER BY creation_time desc
           LIMIT {n_last_tasks}
        ), agg_tasks AS (
            SELECT array_agg(id) AS last_tasks, ds_id FROM last_tasks GROUP BY ds_id
        )
        """
        return sqlparse.format(base_query, reindent=True)

    @auth_required
    def list_tasks(self, feed_id: str) -> list[dict]:
        """
        Получает список тасков фида.

        :param feed_id: ID фида.
        :param token: токен авторизации.
        :return: данные о таске. '{id: status}'
        """
        if not feed_id:
            raise ValueError("'feed_id' обязательный параметр")

        query_params = {"feed_id": feed_id}
        query = self._generate_list_tasks_query()
        return self.__metadb.all(query, query_params)

    def _generate_list_tasks_query(self) -> str:
        """
        Генерирует SQL запрос для получения списка фидов.

        Таблица 'job.task' переодически очищается, поэтому там будут таски только за последние несколько дней.
        Фильтрация по 'service_id' ускоряет запрос.
        :return: SQL запрос для получения списка тасков фида.
        """
        base_query = """
        SELECT ta.id, ta.status 
        FROM job.task ta
        LEFT JOIN meta.feed_datasource fd ON (ta.data ->> 'ds_id')::uuid = fd.id
        WHERE service_id = 'meta.datasource_share' AND data->>'ds_id' = :feed_id::text
        """
        return sqlparse.format(base_query, reindent=True)

    @auth_required
    def get_task(self, task_id: str) -> dict:
        """
        Получает данные о таске.

        :param task_id: ID таска.
        :return: данные о таске.
        """
        query = self._generate_get_task_query()
        return self.__metadb.one(query, params={"task_id": task_id})

    def _generate_get_task_query(self) -> str:
        """
        Генерирует запрос для получения данных о таске.

        :return: строку с SQL-запросом.
        """
        query = """
        SELECT
            id as task_id,
            status,
            origin,
            result_data,
            start_time,
            end_time,
            creation_time,
            last_error,
            data
        FROM job.task 
        WHERE service_id = 'meta.datasource_share' AND id = :task_id::uuid;
        """
        return sqlparse.format(query, reindent=True)

    @auth_required
    def update_feed(self, feed_id: str, update_values: dict) -> dict:
        """
        Обновляет данные о фиде.

        Для обновления доступны колонки ["name", "user_status", "tags"].
        Для обновления tags нужно передать строку вида "tag1, tag2, tag3".

        Существование feed_id проверяется до выполнения этой функции.
        Поэтому если SQL-запрос ничего не вернул, то значит фид является автоматическим и его нельзя обновлять.
        :param feed_id: ID фида.
        :param update_values: данные для обвноления в формате {col_name: value}
        :return: результаты выполнения запроса от Meta API.
        """
        allowed_cols = ["name", "user_status", "tags"]

        allowed_updates = {}
        allowed_update_col_names = []
        for col_name, coi_value in update_values.items():
            if col_name in allowed_cols:
                allowed_updates.update({col_name: coi_value})
                allowed_update_col_names.append(col_name)
            else:
                raise BadParametersError(f"Column '{col_name}' is not allowed for update")

        if allowed_updates.get("tags"):
            allowed_updates["tags"] = f"{{{allowed_updates['tags']}}}"  # получится строка вида '{tag1, tag2}'

        query_params = {"feed_id": feed_id, **allowed_updates}
        query = self._generate_update_feed_query(allowed_update_col_names)
        result = self.__metadb.one(query, query_params)
        if not result:
            raise BadParametersError("The feed was created automatically and cannot be modified")
        return result

    def _generate_update_feed_query(self, col_names: list[str]) -> str:
        """
        Формирует SQL запрс для обновления данных фида.

        :param col_names: список колонок для обновления.
        :return: строка SQL запроса.
        """
        special_types = {
            "user_status": "meta.user_status_type",
            "tags": "_text",
        }
        col_updates = []
        for col_name in col_names:
            if special_types.get(col_name):
                col_upd_expr = f"{col_name} = :{col_name}::{special_types[col_name]}"
            else:
                col_upd_expr = f"{col_name} = :{col_name}"
            col_updates.append(col_upd_expr)
        col_updates_expr = ", ".join(col_updates)

        returning_sql = "RETURNING id, name, user_status, state, last_launch_time, is_automated, tags;"
        query = f"UPDATE meta.feed_datasource SET {col_updates_expr} WHERE id = :feed_id::uuid AND is_automated = false {returning_sql}"
        return sqlparse.format(query, reindent=True)


class FeedDataSource:
    """
    Класс хранения данных по коннектору
    """

    def __init__(
            self, datasource, author_user, connector,
            connector_type, connector_type_preset,
            share_type,
    ):
        self.datasource = datasource
        self.author_user = author_user
        self.connector = connector
        self.connector_type = connector_type
        self.connector_type_preset = connector_type_preset
        self.share_type = share_type
