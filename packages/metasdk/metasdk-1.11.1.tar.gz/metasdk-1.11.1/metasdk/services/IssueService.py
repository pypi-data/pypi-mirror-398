import json
from typing import Any, Mapping, Optional

from metasdk.exceptions import BadParametersError
from metasdk.schemas import IssueCreateItem, IssueGetItem, IssueUpdateItem, IssueStatus
from metasdk.tools.validators import check_postgres_date, check_postgres_period
from metasdk.tools.wrappers import common_auth
from metasdk.tools.parsers import get_bind_params


class IssueService:

    def __init__(self, app, token: Optional[str] = ""):
        """
        :type app: metasdk.MetaApp
        """
        self.__app = app
        self.__options: Mapping[str, Any] = {}
        self.__data_get_cache: Mapping[str, Any] = {}
        self.__metadb = app.db("meta")
        self.token = token
        self.auth_service = app.AuthService
        self.required_scopes: list[str] = []
        self.auth_user_info: Optional[Mapping[str, Any]] = None

    def change_issue_status(self, issue_id: int, status_id: str) -> None:
        """
        Смета статуса тикета
        :param issue_id: Идентификатор тикета.
        :param status_id: Идентификатор статуса тикета.
        :return: None.
        """
        self.__metadb.update(
            """
            UPDATE meta.issue
            SET 
                issue_status_id = :status_id,
                assignee_user_id = valera_user_id(),
                last_user_id = valera_user_id()
            WHERE id = :issue_id
        """,
            {"issue_id": issue_id, "status_id": status_id},
        )

    def pending_issue(self, issue_id: int) -> None: 
        """
        Перевести тикет в статус "В ожидании"
        :param issue_id: int
        """
        self.change_issue_status(issue_id, "1")

    def in_progress_issue(self, issue_id: int) -> None:
        """
        Взять в работу
        :param issue_id: int
        """
        self.change_issue_status(issue_id, "2")

    def reject_issue(self, issue_id: int) -> None:
        """
        Отклонить задачу
        :param issue_id: int
        """
        self.change_issue_status(issue_id, "7")

    def clarification_issue(self, issue_id: int) -> None:
        """
        Уточнение
        :param issue_id: int
        """
        self.change_issue_status(issue_id, "4")

    def done_issue(self, issue_id: int) -> None:
        """
        Успешное выполенение
        :param issue_id: int
        """
        self.change_issue_status(issue_id, "3")

    def add_issue_msg(self, issue_id: int, msg: str) -> None:
        self.__metadb.update(
            """
            INSERT INTO meta.issue_msg (msg, issue_id, user_id, last_user_id)
            VALUES (:msg, :issue_id, valera_user_id(), valera_user_id())
        """,
            {"issue_id": issue_id, "msg": msg},
        )

    @common_auth
    def add_issue_msg_secure(self, issue_id: int, msg: str):
        if not msg.strip():
            raise BadParametersError("Message should not be empty")
        issue_msg = self.__metadb.query(
            """
            INSERT INTO meta.issue_msg (msg, issue_id, user_id, last_user_id)
            VALUES (:msg, :issue_id, :user_id, :user_id)
            RETURNING id, msg
        """,
            {
                "issue_id": issue_id,
                "msg": msg,
                "user_id": self.auth_user_info["auth_user_id"] if self.auth_user_info else None,
            },
        )
        issue_msg_id = issue_msg.get("rows", [])[0].get("id")
        issue_msg_msg = issue_msg.get("rows", [])[0].get("msg")
        return {"message_id": issue_msg_id, "message": issue_msg_msg}

    @common_auth
    def change_issue_status_secure(self, issue_id: int, status_id: str):
        if status_id not in IssueStatus:
            raise BadParametersError(
                f"Status id should be one of {IssueStatus._member_map_}"
            )
        issue = self.__metadb.query(
            """
              UPDATE meta.issue SET 
                issue_status_id=:status_id,
                assignee_user_id=:user_id,
                last_user_id=:user_id
              WHERE id = :issue_id::bigint
              RETURNING id, issue_status_id
        """,
            {
                "issue_id": issue_id,
                "status_id": status_id,
                "user_id": self.auth_user_info["auth_user_id"] if self.auth_user_info else None,
            },
        )
        issue_id = issue.get("rows", [])[0].get("id")
        issue_status_id = issue.get("rows", [])[0].get("issue_status_id")
        return {"issue_id": issue_id, "issue_status_id": issue_status_id}

    @common_auth
    def create_issue(self, issue: IssueCreateItem) -> int | None:
        """
        Создание тикета
        :param issue: IssueCreateItem объект с данными тикета
        :return: ticket_id int айди созданного тикета
        """
        query = """
            INSERT INTO meta.issue (
                application_id,
                name,
                description,
                form_data,
                issue_type_id,
                issue_priority_id,
                reporter_user_id,
                last_user_id,
                entity_id,
                object_id,
                deadline_time,
                estimated_time,
                tags,
                watcher_users,
                assignee_user_id
            )
            SELECT 
                :application_id::text,
                :issue_name::text,
                :description::text,
                :form_data::jsonb,
                :issue_type_id::text,
                :issue_priority_id::text,
                :reporter_user_id::bigint,
                :last_user_id::bigint,
                :entity_id::text,
                :object_id::text,
                :deadline_time::timestamp,
                :estimated_time::interval,
                :tags::text[],
                :watcher_users::jsonb,
                :assignee_user_id::bigint
            RETURNING id
        """
        insert_query_result = self.__metadb.query(
            query,
            {
                "application_id": issue.application_id,
                "issue_name": issue.name,
                "description": issue.description,
                "form_data": issue.form_data,
                "issue_type_id": issue.issue_type_id,
                "issue_priority_id": issue.issue_priority_id,
                "reporter_user_id": issue.reporter_user_id,
                "last_user_id": self.auth_user_info["auth_user_id"] if self.auth_user_info else None,
                "entity_id": issue.entity_id,
                "object_id": issue.object_id,
                "deadline_time": issue.deadline_time_datetime,
                "estimated_time": issue.estimated_time_interval,
                "tags": issue.tags,
                "watcher_users": issue.watcher_users,
                "assignee_user_id": issue.assignee_user_id,
            },
        )
        return insert_query_result.get("rows", [])[0].get("id") if insert_query_result else None

    @common_auth
    def get_issue(self, issue_id: int) -> IssueGetItem | None:
        """
        Возвращает тикет по айди
        :param issue_id: int
        :return: IssueGetItem
        """
        try:
            issue_id = int(issue_id)
        except ValueError:
            raise BadParametersError("Issue id should be integer")
        query = """
            SELECT 
                id,
                name,
                description,
                form_data,
                creation_time,
                modification_time,
                last_user_id,
                issue_type_id,
                reporter_user_id,
                assignee_user_id,
                issue_priority_id,
                issue_status_id,
                entity_id,
                object_id,
                application_id,
                watcher_users,
                deadline_time,
                status_change_time,
                ref_key,
                estimated_time,
                tags,
                result
            FROM meta.issue WHERE id = :id
        """
        issue = self.__metadb.one(query, {"id": issue_id})
        return IssueGetItem(**issue) if issue else None

    @common_auth
    def get_issues(
        self,
        creation_time: Optional[str] = None,
        modification_time_start: Optional[str] = None,
        modification_time_end: Optional[str] = None,
        issue_type_id: Optional[str] = None,
        issue_status_id: Optional[str] = None,
        assignee_user_id: Optional[int] = None,
        reporter_user_id: Optional[int] = None,
        watcher_users: Optional[list[int]] = None,
        form_data: Optional[dict[str, Any]] = None,
        result: Optional[dict[str, Any]] = None
    ) -> list[IssueGetItem]:
        """
        Возвращает список тикетов. Выдача ограничена 1000 записями
        :param creation_time: str согласно выдаче метода DbQueryService.all соответсвует формату '%Y-%m-%dT%H:%M:%S.%f%z',
        но может использоваться формат '%Y-%m-%d', так как в запросе приводится к date
        :param modification_time: str согласно выдаче метода DbQueryService.all соответсвует формату '%Y-%m-%dT%H:%M:%S.%f%z',
        но может использоваться формат '%Y-%m-%d', так как в запросе приводится к date
        :param issue_type_id: str
        :param issue_status_id: str
        :param assignee_user_id: int
        :param reporter_user_id: int
        :param watcher_users: list[int]
        :return: list[IssueGetItem]
        """
        if watcher_users is None:
            watcher_users = []
        if creation_time is not None:
            check_postgres_date(creation_time)
        if modification_time_end and modification_time_start:
            check_postgres_period(modification_time_start, modification_time_end)
            modification_time_query = """
                AND modification_time::date BETWEEN :modification_time_start::date AND :modification_time_end::date
            """
        elif modification_time_start and not modification_time_end:
            check_postgres_date(modification_time_start)
            modification_time_query = """
                AND modification_time::date >= :modification_time_start::date
            """
        elif modification_time_end and not modification_time_start:
            check_postgres_date(modification_time_end)
            modification_time_query = """
                AND modification_time::date <= :modification_time_end::date
            """
        else:
            modification_time_query = ""
        query = """
            SELECT 
                id,
                name,
                description,
                form_data,
                creation_time,
                modification_time,
                last_user_id,
                issue_type_id,
                reporter_user_id,
                assignee_user_id,
                issue_priority_id,
                issue_status_id,
                entity_id,
                object_id,
                application_id,
                watcher_users,
                deadline_time,
                status_change_time,
                ref_key,
                estimated_time,
                tags,
                result
            FROM meta.issue
            WHERE 2>1
                AND creation_time::date = COALESCE(:creation_time::date, creation_time::date)
                AND issue_type_id::text = COALESCE(:issue_type_id::text, issue_type_id::text)
                AND issue_status_id::text = COALESCE(:issue_status_id::text, issue_status_id::text)
                AND assignee_user_id::bigint = COALESCE(:assignee_user_id::bigint, assignee_user_id::bigint)
                AND reporter_user_id::bigint = COALESCE(:reporter_user_id::bigint, reporter_user_id::bigint)
                AND CASE WHEN ARRAY[:watcher_users]::bigint[] IS NOT NULL THEN ARRAY[:watcher_users]::bigint[] <@ ARRAY(
                    SELECT w::bigint as watchers_users_info
                    FROM jsonb_object_keys(issue.watcher_users) w
                ) ELSE TRUE END
                AND (reporter_user_id = :user_id
                    OR assignee_user_id = :user_id
                    OR :user_id::text = ANY(ARRAY(
                        SELECT w::text as watchers_users_info
                        FROM jsonb_object_keys(issue.watcher_users) w
                    )))
        """
        end_of_query = """
            ORDER BY creation_time DESC
            LIMIT 1000"""
        filter_query, params = get_bind_params(form_data=form_data, result=result)
        query += (filter_query.strip() + modification_time_query + end_of_query)
        issues = self.__metadb.all(
            query,
            {
                "creation_time": creation_time,
                "issue_type_id": issue_type_id,
                "issue_status_id": issue_status_id,
                "assignee_user_id": assignee_user_id,
                "reporter_user_id": reporter_user_id,
                "watcher_users": watcher_users or [],
                "modification_time_end": modification_time_end,
                "modification_time_start": modification_time_start,
                "user_id": self.auth_user_info["auth_user_id"] if self.auth_user_info else None,
            } | params,
        )
        return [IssueGetItem(**issue) for issue in issues]

    @common_auth
    def update_issue(self, issue_id: int, issue: IssueUpdateItem) -> IssueGetItem:
        query = """
            UPDATE meta.issue SET 
                name= CASE WHEN :name::text IS NULL THEN name ELSE :name::text END,
                description= CASE WHEN :description::text IS NULL THEN description ELSE :description::text END,
                issue_priority_id= CASE WHEN :issue_priority_id::text IS NULL THEN issue_priority_id ELSE :issue_priority_id::text END,
                deadline_time= CASE WHEN :deadline_time::timestamp IS NULL THEN deadline_time ELSE :deadline_time::timestamp END,
                tags= CASE WHEN :tags::text[] IS NULL THEN tags ELSE :tags::text[] END,
                last_user_id=:user_id::bigint
            WHERE id=:issue_id::bigint
            AND (name <> :name::text
                OR description <> :description::text
                OR issue_priority_id <> :issue_priority_id::text
                OR deadline_time <> :deadline_time::timestamp
                OR tags <> :tags::text[])
        """
        self.__metadb.update(
            query,
            {
                "issue_id": issue_id,
                "name": issue.name,
                "description": issue.description,
                "issue_priority_id": issue.issue_priority_id,
                "deadline_time": issue.deadline_time,
                "tags": issue.tags,
                "user_id": self.auth_user_info["auth_user_id"] if self.auth_user_info else None,
            },
        )
        return self.get_issue(issue_id)

    def update_issue_result(
        self,
        issue_id: int,
        result: Mapping[str, Any],
        soft_update: bool = False,
    ) -> None:
        """
        Обновляет поле result заданного тикета.

        Не требует авторизации и не может использоваться в API тикетов as is.
        :param issue_id: Идентификатор тикета.
        :param result: Содержимое поля result (Тип поля - JSONB).
        :param soft_update: Если True, новое значение будет наложено на старое с заменой пересекающихся ключей.
        :return: None.
        """
        if soft_update:
            issue_result_query = self.__metadb.one(
                "SELECT result FROM meta.issue WHERE id = :issue_id::bigint",
                {"issue_id": issue_id},
            )
            current_result = issue_result_query.get("result", {}) if issue_result_query else {}
            result = {**current_result, **result}

        self.__metadb.update(
            """
            UPDATE meta.issue
            SET result = :result::jsonb
            WHERE id = :issue_id::bigint
            """,
            {"issue_id": issue_id, "result": json.dumps(result)},
        )
