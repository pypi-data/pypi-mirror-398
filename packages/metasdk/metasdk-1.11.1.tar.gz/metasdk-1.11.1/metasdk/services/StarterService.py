import json
import time
from time import sleep
from typing import Callable, Mapping, Any

import requests

from metasdk.exceptions import BadRequestError, UnexpectedError


class StarterService:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def __init__(self, app, db, starter_api_url):
        """
        Прямые запросы к БД скорее всего уйдут в апи запускатора, так как скорее всего пбудет много БД для тасков запускатора, так как
        Если будет 100500 шард, то врядли все будет в одной БД
        :type app: metasdk.MetaApp
        """
        self.__app = app
        self.__options = {}
        self.__data_get_cache = {}
        self.__metadb = db
        self.__starter_api_url = starter_api_url
        self.log = app.log
        self.max_retries = 30

    def update_task_result_data(self, task: Mapping[str, Any], sleep_sec: int | float = 15, **kwargs) -> None:
        """
        Обновляет результат работы таска запускатора.
        :param task: данные таска.
        :param sleep_sec: время ожидания между попытками обновления.
        :param kwargs: дополнительные параметры запроса.
            **requests_timeout: настройка таймаутов request при обращении к Координатору.
        :return: None.
        """
        # импорт тут, так как глобально над классом он не работает
        from metasdk import DEV_STARTER_STUB_URL

        if any([
            not task.get("serviceId"),
            self.__starter_api_url == DEV_STARTER_STUB_URL,
        ]):
            # В этом случае предполагается, что таск запущен локально.
            self.log.info("STARTER DEV. Результат таска условно обновлен", {"task": task})
            return

        self.log.info("Сохраняем состояние в БД", {"result_data": task["result_data"]})
        requests_timeout = kwargs.get("requests_timeout", 15)
        service_id = task.get("serviceId")
        if sleep_sec < 1:
            sleep_sec = 1
        if sleep_sec > 600:
            sleep_sec = 600
        max_tries = 10
        current_try = 0
        while True:
            url = f"{self.__starter_api_url}/services/{service_id}/tasks/updateResultData"
            try:
                resp = requests.post(
                    url=url,
                    data=json.dumps(task),
                    headers=self.headers,
                    timeout=requests_timeout,
                )
                """
                Осуществляем попытки, пока не получим код 200
                Иначе делаем паузу и пробуем снова
                """
                if resp.status_code == 200:
                    return
                else:
                    self.log.warning("Некорректный http статус при обновлении result_data задачи, пробуем снова", {
                        "task": task
                    })
                    current_try = current_try + 1
                    if current_try >= max_tries:
                        self.log.error("Некорректный http статус при обновлении result_data задачи, прерываем выполнение", {
                            "status_code": resp.status_code,
                            "task": task,
                            "response_text": resp.text
                        })
                        raise IOError("Starter response read error: " + resp.text)

            except Exception:
                self.log.warning("Неизвестная ошибка при обновлении result_data задачи, пробуем снова", {
                    "task": task
                })
                current_try = current_try + 1
                if current_try >= max_tries:
                    self.log.error("Неизвестная ошибка при обновлении result_data задачи, прерываем выполнение", {
                        "task": task
                    })
                    raise IOError("Starter response read error")
            time.sleep(sleep_sec)

    def await_task(
            self,
            task_id: str,
            service_id: str,
            callback_fn: Callable[[dict, bool], None] | None = None,
            sleep_sec: int = 15,
            **kwargs,
    ) -> dict[str, Any] | None:
        """
        Подождать выполнения задачи запускатора.

        При работе с Координатором (запросом данных по API) мы будем обращаться к API до тех пор, пока не будет получен корректный ответ

        Пауза делается в начале, а не конце цикла для того, чтобы не сделать запрос слишком рано, когда задача, вероятно, наверняка еще не выполнена
        Тем не менее, при паузе больше 5 секунд она делится на две части - 5 секунд в начале цикла и остальное - после
        Это позволит не ждать слишком долго перед первым запросом и, в то же время, подерживать общую длинну паузы на заданном параметром уровне
        :param task_id: ID задачи, за которой нужно следить.
        :param service_id: ID сервиса.
        :param callback_fn: Функция обратного вызова, в нее будет передаваться task_info и is_finish как признак, что обработка завершена.
        :param sleep_sec: задержка между проверкой по БД. Не рекомендуется делать меньше 10, так как это может очень сильно ударить по производительности БД.
        :param kwargs: дополнительные параметры запроса.
            **requests_timeout: настройка таймаутов request при обращении к Координатору.
        :return: None|dict
        """
        requests_timeout = kwargs.get("requests_timeout", 15)

        sleep_pre_sec = sleep_sec
        sleep_post_sec = 0
        if sleep_sec > 5:
            sleep_pre_sec = 5
            sleep_post_sec = sleep_sec - 5
        max_tries = 10
        current_try = 0
        while True:
            time.sleep(sleep_pre_sec)
            data = {"taskId": task_id}
            url = f"{self.__starter_api_url}/services/{service_id}/tasks/getShortTaskInfo"
            try:
                resp = requests.post(
                    url=url,
                    data=json.dumps(data),
                    headers=self.headers,
                    timeout=requests_timeout,
                )
                """
                Если задача не найдена - возвращать null и правильно его тут обрабатывать!
                """
                if (len(resp.text) > 0):
                    serverResult = json.loads(resp.text)
                    if resp.status_code == 200:
                        self.log.info("Ждем выполнения задачи", {
                            "task_info": serverResult
                        })
                        is_finish = serverResult["status"] != "NEW" and serverResult["status"] != "PROCESSING"
                        if callback_fn:
                            # Уведомляем вызывающего
                            callback_fn(serverResult, is_finish)
                        if is_finish:
                            return serverResult
                else:
                    return None
            except Exception as e:
                self.log.warning("Неизвестная ошибка при выполнении await_task, пробуем снова", {"error": e})
                current_try = current_try + 1
                if current_try >= max_tries:
                    self.log.error("Неизвестная ошибка при выполнении await_task, прерываем выполнение", {"error": e})
                    raise IOError("Starter response read error")
            time.sleep(sleep_post_sec)

    def submit(self, service_id: str, data: dict | None = None, **kwargs) -> dict[str, Any] | None:
        """
        Отправить задачу в запускатор.

        :param service_id: ID службы. Например "meta.docs_generate".
        :param data: Полезная нагрузка задачи.
        :param kwargs: дополнительные параметры запроса.
            **requests_timeout: настройка таймаутов request при обращении к Координатору.
        :return: dict
        """
        requests_timeout = kwargs.get("requests_timeout", 15)

        # импорт тут, так как глобально над классом он не работает
        from metasdk import DEV_STARTER_STUB_URL

        if self.__starter_api_url == DEV_STARTER_STUB_URL:
            self.log.info("STARTER DEV. Задача условно поставлена", {
                "service_id": service_id,
                "data": data,
            })
            return None

        task = {"serviceId": service_id, "data": data}
        url = f"{self.__starter_api_url}/services/{service_id}/tasks"
        last_e = None
        for _idx in range(self.max_retries):
            try:
                resp = requests.post(
                    url=url,
                    data=json.dumps(task),
                    headers=self.headers,
                    timeout=requests_timeout,
                )
                try:
                    return json.loads(resp.text)
                except Exception:
                    raise IOError("Starter response read error: " + resp.text)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                # При ошибках подключения пытаемся еще раз
                last_e = e
                sleep(3)
        if isinstance(last_e, Exception):
            raise last_e
        return last_e

    def stop_task(self, task_id: str, service_id: str, **kwargs) -> str | None:
        """
        Остановить задачу запускатора.

        :param task_id: ID задачи.
        :param service_id: ID службы. Например "meta.datasource_share".
        :param kwargs: дополнительные параметры запроса.
            **requests_timeout: настройка таймаутов request при обращении к Координатору.
        :return: None
        """
        requests_timeout = kwargs.get("requests_timeout", 15)

        last_e = None
        url = f"{self.__starter_api_url}/services/{service_id}/tasks/{task_id}"
        for _ in range(self.max_retries):
            try:
                resp = requests.delete(url=url, headers=self.headers, timeout=requests_timeout)
                if resp.status_code == 200:
                    return task_id
                elif resp.status_code == 400:
                    error = resp.json()
                    raise BadRequestError("Bad Request", {"error": error})
                else:
                    raise UnexpectedError("Непредвиденная ошибка при остановке задачи", {"error": resp.text})
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_e = e
                sleep(3)
        if isinstance(last_e, Exception):
            raise last_e
        return last_e
