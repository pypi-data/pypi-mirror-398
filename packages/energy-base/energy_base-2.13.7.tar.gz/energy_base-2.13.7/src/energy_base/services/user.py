import os

from requests import get


class BaseMicroserviceSetting:
    url: str = None
    token: str = None


class UserServiceSetting(BaseMicroserviceSetting):
    url = os.environ.get("USER_SERVICE_URL")


class UserService:
    base_url = UserServiceSetting.url

    @staticmethod
    def url(path):
        return UserService.base_url + path

    @staticmethod
    def get_users(ids: list[str]) -> list[dict]:
        return get(UserService.url('/api/users/all/'), {'ids': ','.join(ids)}).json()
