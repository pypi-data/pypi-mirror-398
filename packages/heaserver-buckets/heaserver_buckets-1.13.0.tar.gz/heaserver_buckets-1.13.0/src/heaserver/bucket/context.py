from heaserver.service.db.aws import AWSPermissionContext, is_account_owner
from heaserver.service.db.awsaction import S3_LIST_BUCKET, S3_DELETE_BUCKET, S3_GET_BUCKET_TAGGING, S3_PUT_BUCKET_TAGGING
from heaobject.bucket import AWSDesktopObject
from heaobject.root import Permission, DesktopObject
from aiohttp.web import Request
from cachetools import TTLCache
from pickle import dumps
from copy import copy
from typing import NamedTuple


class _CacheKey(NamedTuple):
    obj_str: str
    attr: str

class S3BucketPermissionsContext(AWSPermissionContext):
    """
    Calculates permissions on a bucket, including attribute-level permissions. The bucket's bucket_id attribute must
    be populated.
    """
    def __init__(self, request: Request, **kwargs):
        """
        Creates the context object.

        :param request: the HTTP request (required). It must have a volume_id path parameter.
        :param volume_id: the ID of the volume being accessed (required)
        """
        actions = [S3_LIST_BUCKET, S3_PUT_BUCKET_TAGGING, S3_DELETE_BUCKET]
        super().__init__(request=request, actions=actions, **kwargs)
        self.__cache: TTLCache[_CacheKey, list[Permission]] = TTLCache(maxsize=128, ttl=30)

    async def get_attribute_permissions(self, obj: DesktopObject, attr: str) -> list[Permission]:
        """
        Returns the requester's permissions for a bucket attribute. The tags attribute may have different
        permissions than the overall bucket. Other attributes have the same permissions as the overall bucket.

        :param obj: the bucket (required). The bucket's bucket_id attribute must be populated.
        :param attr: the attribute (required).
        :return: the requester's permissions.
        """
        key = _CacheKey(repr(obj), attr)
        perms = self.__cache.get(key)
        if perms is None:
            if attr == 'tags' and not await self.is_account_owner() and isinstance(obj, AWSDesktopObject):
                perms = await self._simulate_perms(obj, [S3_GET_BUCKET_TAGGING, S3_PUT_BUCKET_TAGGING])
            else:
                perms = await super().get_attribute_permissions(obj, attr)
            self.__cache[key] = perms
        return copy(perms)

    def _caller_arn(self, obj: AWSDesktopObject):
        """
        Returns a bucket's ARN. Requires the bucket's bucket_id attribute to be populated.
        """
        return f'arn:aws:s3:::{obj.resource_type_and_id}'
