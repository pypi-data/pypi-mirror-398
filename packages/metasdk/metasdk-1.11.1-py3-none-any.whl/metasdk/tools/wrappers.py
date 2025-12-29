import functools

# todo: move to AuthService!


def common_auth(func):
    """
    Декоратор используется в классах IssueService для проверки общих прав доступа
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        """
        Помещает в IssueService.auth_user_info следующую информацию о пользователе:
        - auth_user_id: ID пользователя, будь то обычный пользователь или сервисный аккаунт;
        - parent_user_id: ID пользователя, если авторизуется сервисный аккаунт - ID его владельца;
        - scopes: список доступных скоупов;
        - company_id: ID компании;
        - is_admin: признак администратора.
        """
        auth_info = self.auth_service.verify_access_token(self.token, self.required_scopes)
        self.auth_user_info = {
            "auth_user_id": auth_info["verification_server_response"]["userId"],
            "parent_user_id": auth_info["author_info"]["auth_user_id"],
            "scopes": auth_info["verification_server_response"]["scopes"],
            "company_id": auth_info["author_info"]["company_id"],
            "is_admin": auth_info["author_info"]["is_admin"],
        }
        return func(self, *args, **kwargs)
    return wrapper