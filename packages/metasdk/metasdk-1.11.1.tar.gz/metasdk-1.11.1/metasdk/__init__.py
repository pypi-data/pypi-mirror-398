from __future__ import annotations

import json
import os
import platform
import socket
import sys
import time
from typing import Optional

import requests
from urllib3.connection import HTTPConnection

from metasdk.__state import set_current_app
from metasdk.event_bus import EventBus
from metasdk.exceptions import UnexpectedError, DbQueryError, ServerError
from metasdk.internal import read_developer_settings
from metasdk.logger import create_logger, eprint
from metasdk.logger.bulk_logger import BulkLogger
from metasdk.logger.logger import Logger
from metasdk.services import get_api_call_headers, process_meta_api_error_code
from metasdk.services.ApiProxyService import ApiProxyService
from metasdk.services.AsyncDbQueryService import AsyncDbQueryService
from metasdk.services.AuthService import AuthService
from metasdk.services.CacheService import CacheService
from metasdk.services.DbQueryService import DbQueryService
from metasdk.services.DbService import DbService
from metasdk.services.DevService import DevService
from metasdk.services.ExportService import ExportService
from metasdk.services.ExternalSystemService import ExternalSystemService
from metasdk.services.FeedService import FeedService
from metasdk.services.IssueService import IssueService
from metasdk.services.MediaService import MediaService
from metasdk.services.MetaqlService import MetaqlService
from metasdk.services.ObjectLogService import ObjectLogService
from metasdk.services.SettingsService import SettingsService
from metasdk.services.UserManagementService import UserManagementService
from metasdk.services.StarterService import StarterService
from metasdk.services.MailService import MailService
from metasdk.services.LockService import LockService
from metasdk.transport import AsyncNativeApiTransport
from metasdk.worker import Worker

DEV_STARTER_STUB_URL = "http://STUB_URL"


class MetaApp(object):
    current_app: Optional["MetaApp"] = None
    debug: bool = False
    service_id: Optional[str] = None
    build_num: Optional[str] = None
    starter_api_url: Optional[str] = None
    meta_url: Optional[str] = None
    redis_url: Optional[str] = None
    api_proxy_url: Optional[str] = None
    log: Logger = Logger()
    worker: Optional[Worker] = None
    event_bus: Optional[EventBus] = None

    # Будет поставляться в конец UserAgent
    user_agent_postfix = ""

    developer_settings = None

    # Пользователь, из под которого пройдет авторизация после того,
    # как мета авторизует разработчика, в случае, если разработчик имеет разрешения для авторизации из-под других пользователей
    auth_user_id: Optional[int] = None

    MediaService: Optional[MediaService] = None
    MetaqlService: Optional[MetaqlService] = None
    ExportService: Optional[ExportService] = None
    CacheService: Optional[CacheService] = None
    SettingsService: Optional[SettingsService] = None
    IssueService: Optional[IssueService] = None
    UserManagementService: Optional[UserManagementService] = None
    StarterService: Optional[StarterService] = None
    MailService: Optional[MailService] = None
    ApiProxyService: Optional[ApiProxyService] = None
    AuthService: Optional[AuthService] = None

    __default_headers: dict[str, str] = {}
    __db_list: dict[str, DbQueryService] = {}
    __async_db_list: dict[str, AsyncDbQueryService] = {}
    __async_transport: Optional[AsyncNativeApiTransport] = None

    def __init__(self, service_id: Optional[str] = None, debug: Optional[bool] = None,
                 starter_api_url: Optional[str] = None,
                 meta_url: Optional[str] = None,
                 api_proxy_url: Optional[str] = None,
                 include_worker: Optional[bool] = None,
                 redis_url: Optional[str] = None,
                 setup_sockets: bool = True,
                 gcloud_log_host_port: Optional[str] = None,
                 auth_service_host: Optional[str] = None,
                 ):
        if setup_sockets:
            self.setup_sockets()

        if debug is None:
            is_prod = os.environ.get('PRODUCTION', False)
            debug = os.environ.get('DEBUG', not is_prod)
            if include_worker is None:
                include_worker = True
            if debug == 'false':
                debug = False
        self.debug = debug
        defaultEnvParamList = []
        if os.environ.get("REDIS_URL") is None and redis_url is None:
            defaultEnvParamList.append("REDIS_URL")
        if os.environ.get("META_URL") is None and meta_url is None:
            defaultEnvParamList.append("META_URL")
        if os.environ.get("API_PROXY_URL") is None and api_proxy_url is None:
            defaultEnvParamList.append("API_PROXY_URL")
        if os.environ.get("STARTER_URL") is None and starter_api_url is None:
            defaultEnvParamList.append("STARTER_URL")
        if os.environ.get("GCLOUD_LOG_HOST_PORT") is None and gcloud_log_host_port is None:
            defaultEnvParamList.append("GCLOUD_LOG_HOST_PORT")
        if len(defaultEnvParamList) > 0:
            self.log.warning("Пропущены обязательные переменные окружения: " + ", ".join(defaultEnvParamList))

        self.redis_url = os.environ.get("REDIS_URL", redis_url or "s1.meta.vmc.loc:6379:1")
        self.meta_url = os.environ.get("META_URL", meta_url or "https://apimeta.devision.io")
        self.api_proxy_url = os.environ.get("API_PROXY_URL", api_proxy_url or "https://apiproxy.apis.garpun.com")
        self.auth_service_host = os.environ.get("AUTH_SERVICE_HOST", auth_service_host or "https://account.garpun.com")

        if debug and not starter_api_url:
            starter_api_url = DEV_STARTER_STUB_URL
        self.starter_api_url = os.environ.get("STARTER_URL", starter_api_url or "http://starter_url_not_set")

        if service_id:
            self.log.warning("Параметр service_id скоро будет удален из MetaApp")

        gcloud_log_host_port = os.environ.get("GCLOUD_LOG_HOST_PORT", gcloud_log_host_port or "n3.adp.vmc.loc:31891")
        service_ns = os.environ.get('SERVICE_NAMESPACE', "appscript")  # для ns в логах и для префикса Dispatcher
        service_id = os.environ.get('SERVICE_ID', "local_debug_service")
        self.build_num = os.environ.get('BUILD_NUM', '0')
        self.service_ns = service_ns
        self.service_id = service_id
        self.dispatcher_name = self.service_ns + "." + self.service_id

        create_logger(service_id=service_id, service_ns=service_ns, build_num=self.build_num,
                      gcloud_log_host_port=gcloud_log_host_port, debug=self.debug)

        self.__read_developer_settings()

        self.__default_headers = get_api_call_headers(self)

        # Оставляем синхронный sync-кеш (__db_list) как было (классовым),
        # чтобы не ломать старый функционал. Асинхронные кеши/транспорт делаем инстансовыми,
        # чтобы не делить закрытый клиент между MetaApp.
        self.__async_db_list = {}

        self.__async_transport = None
        self.AuthService = AuthService(self)
        self.MediaService = MediaService(self)
        self.MetaqlService = MetaqlService(self)
        self.SettingsService = SettingsService(self)
        self.ExportService = ExportService(self)
        self.CacheService = CacheService(self)
        self.IssueService = IssueService(self)
        self.StarterService = StarterService(self, self.db("meta"), self.starter_api_url)
        self.MailService = MailService(self)
        self.DbService = DbService(self)
        self.UserManagementService = UserManagementService(self)
        self.ApiProxyService = ApiProxyService(self)
        self.ExternalSystemService = ExternalSystemService(self)
        self.FeedService = FeedService(self)
        self.LockService = LockService(self)
        self.ObjectLogService = ObjectLogService(self)
        self.DevService = DevService(self)

        if include_worker:
            self.event_bus = EventBus(self)

            stdin = "[]" if debug else ''.join(sys.stdin.readlines())
            self.worker = Worker(self, stdin)

        set_current_app(self)
        self.log.info("MetaApp initialized", {"version": self.get_lib_version()})

    def bulk_log(self, log_message=u"Еще одна пачка обработана", total=None, part_log_time_minutes=5):
        """
        Возвращает инстант логгера для обработки списокв данных
        :param log_message: То, что будет написано, когда время придет
        :param total: Общее кол-во объектов, если вы знаете его
        :param part_log_time_minutes: Раз в какое кол-во минут пытаться писать лог
        :return: BulkLogger
        """
        return BulkLogger(log=self.log, log_message=log_message, total=total,
                          part_log_time_minutes=part_log_time_minutes)

    def db(self, db_alias, shard_key=None):
        """
        Получить экземпляр работы с БД
        :type db_alias: basestring Альяс БД из меты
        :type shard_key: Любой тип. Некоторый идентификатор, который поможет мете найти нужную шарду. Тип зависи от принимающей стороны
        :rtype: DbQueryService
        """
        if shard_key is None:
            shard_key = ''

        db_key = db_alias + '__' + str(shard_key)
        if db_key not in self.__db_list:
            self.__db_list[db_key] = DbQueryService(self, {"db_alias": db_alias, "dbAlias": db_alias,
                                                           "shard_find_key": shard_key, "shardKey": shard_key})
        return self.__db_list[db_key]

    def db_async(self, db_alias: str, shard_key: Optional[str] = None) -> AsyncDbQueryService:
        """
        Получить экземпляр асинхронного клиента, использующего общий кешированный транспорт.

        Подходит для долгоживущих приложений/воркеров: транспорт создаётся один раз и
        не закрывается автоматически. После завершения работы приложения следует вызвать
        `await app.close_async_transport()`. Конечно, после закрытия контейнера ОС и так зачистит сокеты,
        однако во избежание все же рекомендуется вызывать метод закрытия транспорта.
        :param db_alias: Алиас БД.
        :param shard_key: Название ключа шарда (опционально).
        :return: AsyncDbQueryService.
        """
        if shard_key is None:
            shard_key = ""

        db_key = f"{str(db_alias)}___{str(shard_key)}"
        if db_key not in self.__async_db_list:
            self.__async_db_list[db_key] = AsyncDbQueryService(
                self,
                {
                    "db_alias": db_alias,
                    "dbAlias": db_alias,
                    "shard_find_key": shard_key,
                    "shardKey": shard_key
                },
            )
        return self.__async_db_list[db_key]

    def db_async_session(self, db_alias: str, shard_key: Optional[str] = None) -> AsyncDbQueryService:
        """
        Создаёт асинхронный клиент с выделенным транспортом под контекст.

        Использование: `async with app.db_async_session(...) as db:`. Транспорт будет
        закрыт автоматически при выходе из контекста и не влияет на общий кешированный
        транспорт.
        """
        if shard_key is None:
            shard_key = ""

        transport = self._create_async_transport()
        return AsyncDbQueryService(
            self,
            {
                "db_alias": db_alias,
                "dbAlias": db_alias,
                "shard_find_key": shard_key,
                "shardKey": shard_key,
            },
            transport=transport,
            owns_transport=True,
        )

    @property
    def user_agent(self):
        return self.service_id + " | b" + self.build_num + (
            ' | ' + self.user_agent_postfix if self.user_agent_postfix else "")

    def __read_developer_settings(self):
        """
        Читает конфигурации разработчика с локальной машины или из переменных окружения
        При этом переменная окружения приоритетнее
        :return:
        """
        self.developer_settings = read_developer_settings()
        if not self.developer_settings:
            self.log.warning(
                "НЕ УСТАНОВЛЕНЫ настройки разработчика, это может приводить к проблемам в дальнейшей работе!")

    def api_call(self, service, method, data, options):
        """
        :type app: metasdk.MetaApp
        """
        if 'self' in data:
            # может не быть, если вызывается напрямую из кода,
            # а не из прослоек типа DbQueryService
            data.pop("self")

        if options:
            data.update(options)

        _headers = dict(self.__default_headers)

        if self.auth_user_id:
            _headers['X-META-AuthUserID'] = str(self.auth_user_id)

        request = {
            "url": self.meta_url + "/api/v1/adptools/" + service + "/" + method,
            "data": json.dumps(data),
            "headers": _headers,
            "timeout": (60, 1800)
        }

        last_e = ServerError(request)
        for _try_idx in range(20):
            try:
                resp = requests.post(**request)
                if resp.status_code == 200:
                    decoded_resp = json.loads(resp.text)
                    if 'data' in decoded_resp:
                        return decoded_resp['data'][method]
                    if 'error' in decoded_resp:
                        if 'details' in decoded_resp['error']:
                            eprint(decoded_resp['error']['details'])
                        raise DbQueryError(decoded_resp['error'])
                    raise UnexpectedError()
                else:
                    process_meta_api_error_code(resp.status_code, request, resp.text)
            except (requests.exceptions.ConnectionError, ConnectionError, TimeoutError) as e:
                self.log.warning('META API Connection Error. Sleep...', {"e": e})
                time.sleep(15)

            except ServerError as e:
                last_e = e
                self.log.warning('META Server Error. Sleep...', {"e": e})
                time.sleep(15)

            except Exception as e:
                if 'Служба частично или полностью недоступна' in str(e):
                    self.log.warning('META API Connection Error. Sleep...', {"e": e})
                    time.sleep(15)
                else:
                    raise e

        raise last_e

    def native_api_call(self, service, method, data, options, multipart_form=False, multipart_form_data=None,
                        stream=False, http_path="/api/meta/v1/", http_method='POST',
                        get_params=None, connect_timeout_sec=60, request_timeout_sec=1800):
        """
        :type app: metasdk.MetaApp
        :rtype: requests.Response
        """
        if get_params is None:
            get_params = {}
        if 'self' in data:
            # может не быть, если вызывается напрямую из кода,
            # а не из прослоек типа DbQueryService
            data.pop("self")

        if options:
            data.update(options)

        _headers = dict(self.__default_headers)

        if self.auth_user_id:
            _headers['X-META-AuthUserID'] = str(self.auth_user_id)

        request = {
            "url": self.meta_url + http_path + service + "/" + method,
            "timeout": (connect_timeout_sec, request_timeout_sec),
            "stream": stream,
            "params": get_params,
        }

        if multipart_form:
            if multipart_form_data:
                request['files'] = multipart_form_data
            request['data'] = data
            _headers.pop('content-type', None)
        else:
            request['data'] = json.dumps(data)
        request['headers'] = _headers

        last_e = ServerError(request)
        for _try_idx in range(10):
            try:
                resp = requests.request(http_method, **request)
                # добавляем глобальную трассировку в логи
                self.log.set_entity("request_id", resp.headers.get('request_id'))
                if resp.status_code == 200:
                    return resp
                else:
                    process_meta_api_error_code(resp.status_code, request, resp.text)
            except (requests.exceptions.ConnectionError, ConnectionError, TimeoutError) as e:
                self.log.warning('META API Connection Error. Sleep...', {"e": e})
                time.sleep(15)

            except ServerError as e:
                last_e = e
                self.log.warning('META Server Error. Sleep...', {"e": e})
                time.sleep(15)

            except Exception as e:
                if 'Служба частично или полностью недоступна' in str(e):
                    self.log.warning('META API Service Temporarily Unavailable. Sleep...', {"e": e})
                    time.sleep(15)
                else:
                    raise e
            finally:
                self.log.set_entity("request_id", None)

        raise last_e

    def __ensure_async_transport(self) -> AsyncNativeApiTransport:
        """
        Убеждается, что асинхронный транспорт инициализирован.

        :return: AsyncNativeApiTransport.
        """
        if not self.__async_transport:
            if not self.meta_url:
                raise ValueError("MetaApp.meta_url must be configured before using async transport")
            self.__async_transport = AsyncNativeApiTransport(
                meta_url=self.meta_url,
                default_headers=self.__default_headers,
                logger=self.log,
                auth_user_id_supplier=lambda: self.auth_user_id,
            )
        return self.__async_transport

    def ensure_async_transport(self) -> AsyncNativeApiTransport:
        """
        Публичный доступ к кешированному асинхронному транспорту.
        """
        return self.__ensure_async_transport()

    def _create_async_transport(self) -> AsyncNativeApiTransport:
        """
        Создаёт новый экземпляр асинхронного транспорта без кеширования.
        """
        if not self.meta_url:
            raise ValueError("MetaApp.meta_url must be configured before using async transport")
        return AsyncNativeApiTransport(
            meta_url=self.meta_url,
            default_headers=self.__default_headers,
            logger=self.log,
            auth_user_id_supplier=lambda: self.auth_user_id,
        )

    async def close_async_transport(self) -> None:
        """
        Закрывает асинхронный транспорт.

        :return: None.
        """
        if self.__async_transport:
            await self.__async_transport.aclose()
            self.__async_transport = None

    def get_lib_version(self) -> str:
        """
        Возвращает версию библиотеки MetaSDK.

        :return: Версия библиотеки.
        """
        from metasdk import info
        return info.__version__

    @staticmethod
    def setup_sockets():
        """
        Настройка для решения проблемы с разрывом соединения после, примерно, трёх минут при запросе к сервисам,
        расположенным ва яндекс-облаке
        (больше информации в задаче META-2932)
        """

        # Не все из этих параметров есть в каждой системе (в MacOS, например, нет socket.TCP_KEEPIDLE).
        # Если сделать обычные списки, то при интерпретации отсутствующего параметра возникнет исключение.
        # Чтобы этого избежать всё завёрнуто в лямбды
        additional_socket_options_for_systems = {
            "Windows": lambda: [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                                (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10),
                                (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 60),
                                (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)],
            "Linux": lambda: [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                              (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1),
                              (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3),
                              (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)],
            "Darwin": lambda: [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                               (socket.IPPROTO_TCP, 0x10, 3)]
        }

        HTTPConnection.default_socket_options += additional_socket_options_for_systems[platform.system()]()
