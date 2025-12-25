from typing import List, Optional, Union

from django.contrib.auth import models as auth_models
from django.db.models.manager import EmptyManager
from django.utils.functional import cached_property


class MicroserviceUser:
    is_active = True

    _groups = EmptyManager(auth_models.Group)
    _user_permissions = EmptyManager(auth_models.Permission)

    def __str__(self) -> str:
        return f"{self.id}"

    @cached_property
    def id(self) -> Union[int, str]:
        return -1

    @cached_property
    def pk(self) -> Union[int, str]:
        return self.id

    @cached_property
    def username(self) -> str:
        return 'microservice'

    @cached_property
    def is_staff(self) -> bool:
        return True

    @cached_property
    def is_superuser(self) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MicroserviceUser):
            return NotImplemented
        return self.id == other.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.id)

    def save(self) -> None:
        raise NotImplementedError("Microservice users have no DB representation")

    def delete(self) -> None:
        raise NotImplementedError("Microservice users have no DB representation")

    def set_password(self, raw_password: str) -> None:
        raise NotImplementedError("Microservice users have no DB representation")

    def check_password(self, raw_password: str) -> None:
        raise NotImplementedError("Microservice users have no DB representation")

    @property
    def groups(self) -> auth_models.Group:
        return self._groups

    @property
    def user_permissions(self) -> auth_models.Permission:
        return self._user_permissions

    def get_group_permissions(self, obj: Optional[object] = None) -> set:
        return set()

    def get_all_permissions(self, obj: Optional[object] = None) -> set:
        return set()

    def has_perm(self, perm: str, obj: Optional[object] = None) -> bool:
        return False

    def has_perms(self, perm_list: List[str], obj: Optional[object] = None) -> bool:
        return False

    def has_module_perms(self, module: str) -> bool:
        return False

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_authenticated(self) -> bool:
        return True

    def get_username(self) -> str:
        return self.username
