from heaserver.service.db.aws import is_account_owner
from heaobject.account import AWSAccount
from heaobject.root import PermissionContext, DesktopObject, Permission
from heaobject.user import NONE_USER
from heaserver.service.oidcclaimhdrs import SUB
from aiohttp.web import Request
from copy import copy

class AWSAccountPermissionContext(PermissionContext):
    def __init__(self, request: Request, volume_id: str, **kwargs):
        self.__request = request
        self.__volume_id = volume_id
        sub = request.headers.get(SUB, NONE_USER)
        super().__init__(sub, **kwargs)
        self.__cache: dict[str, list[Permission]] = {}

    @property
    def request(self) -> Request:
        return self.__request

    @property
    def volume_id(self) -> str:
        return self.__volume_id

    async def get_permissions(self, obj: DesktopObject) -> list[Permission]:
        if obj.instance_id is None:
            raise ValueError('obj.instance_id is None, which likely means the object has not yet been persisted.')
        cached_value = self.__cache.get(obj.instance_id)
        if cached_value is not None:
            return copy(cached_value)
        else:
            # The logic below is commented out because we don't support editing nor deleting AWS accounts yet.
            # if not await is_account_owner(request=self.request, volume_id=self.volume_id):
            #     perms = [Permission.COOWNER]
            # else:
            #     perms = [Permission.VIEWER]
            perms = [Permission.VIEWER]
            self.__cache[obj.instance_id] = perms
            return copy(perms)

    def _caller_arn(self, obj: AWSAccount):
        return f'arn:aws:s3::{obj.id}'
