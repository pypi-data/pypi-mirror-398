import json

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import TypeAlias, Mapping, Any, Optional

from metasdk.tools.validators import check_postgres_datetime_without_tz


JSONb: TypeAlias = Mapping[str, Any]


class IssueStatus(str, Enum):
    WAITING = "1"
    IN_PROGRESS = "2"
    DONE = "3"
    CLARIFICATION = "4"
    PENDING = "5"
    DEPRECATED_PLANNED = "6"
    CANCELED = "7"
    APPROVED = "8"
    APPROVAL_DENIED = "9"


@dataclass
class BaseIssueItem:
    """
    Базовый Датакласс для хранения данных о тикете
    """
    name: str
    issue_type_id: str
    reporter_user_id: int
    entity_id: str
    object_id: str
    application_id: str
    description: str
    issue_priority_id: str
    issue_status_id: str
    assignee_user_id: int
    form_data: JSONb
    watcher_users: JSONb
    deadline_time: str
    estimated_time: float
    tags: list[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class IssueCreateItem(BaseIssueItem):
    """
    Датакласс для хранения данных о создаваемом тикете
    deadline_time должно быть в формате "YYYY-MM-DDTHH:MM:SS"
    estimated_time передается в ЧАСАХ с дальнейшей конвертацией в минуты
    """
    description: str = ""
    issue_priority_id: str = "1"
    issue_status_id: str = "1"
    assignee_user_id: Optional[int] = None
    form_data: JSONb = field(default_factory=dict)
    watcher_users: JSONb = field(default_factory=dict)
    deadline_time: Optional[str] = None
    estimated_time: Optional[float] = None
    tags: list[str] = field(default_factory=list)

    @property
    def deadline_time_datetime(self) -> str | None:
        if self.deadline_time is not None:
            check_postgres_datetime_without_tz(self.deadline_time)
        return self.deadline_time

    @property
    def estimated_time_interval(self) -> str | None:
        if self.estimated_time is None:
            return self.estimated_time
        return f"{self.estimated_time*60} MINUTES"

    def __post_init__(self):
        for issue_field in self.__dataclass_fields__:
            if isinstance(getattr(self, issue_field), dict):
                setattr(self, issue_field, json.dumps(getattr(self, issue_field)))
            if isinstance(getattr(self, issue_field), list):
                initial = str(getattr(self, issue_field))
                final = initial.replace('[', '{').replace(']', '}').replace('"', "").replace("'", "")
                setattr(self, issue_field, final)


@dataclass
class IssueGetItem(BaseIssueItem):
    """
    Датакласс для хранения данных о полученном тикете
    """
    id: int  # noqa: A003
    last_user_id: int
    creation_time: str
    modification_time: str
    status_change_time: str
    ref_key: str
    result: JSONb


@dataclass
class IssueUpdateItem:
    name: Optional[str] = None
    description: Optional[str] = None
    deadline_time: Optional[str] = None
    issue_priority_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    @property
    def deadline_time_datetime(self) -> str | None:
        if self.deadline_time is not None:
            check_postgres_datetime_without_tz(self.deadline_time)
        return self.deadline_time

    def __post_init__(self):
        for issue_field in self.__dataclass_fields__:
            if isinstance(getattr(self, issue_field), list):
                initial = str(getattr(self, issue_field))
                final = initial.replace('[', '{').replace(']', '}').replace('"', "").replace("'", "")
                setattr(self, issue_field, final)