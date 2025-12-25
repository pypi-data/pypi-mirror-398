from .permissionstestcase import VolumePermissionsTestCase, FileSystemPermissionsTestCase, db_store as fixtures
from heaserver.service.testcase.mixin import PermissionsGetOneMixin, PermissionsGetAllMixin, PermissionsPostMixin, \
    PermissionsPutMixin, PermissionsDeleteMixin
from heaserver.service.representor import nvpjson
from aiohttp import hdrs


class TestVolumeGetWithBadPermissions(VolumePermissionsTestCase, PermissionsGetOneMixin):
    pass


class TestVolumeGetAllWithBadPermissions(VolumePermissionsTestCase, PermissionsGetAllMixin):
    async def test_get_volume_by_filesystem_type_with_bad_permissions_all(self) -> None:
        """
        Checks if a GET request for a volume whose file system type is heaobject.volume.MongoDBFileSystem succeeds but
        returns no objects when the user does not have permissions to any the valid results of the request.
        """
        obj = await self.client.request('GET',
                                        (self._href / 'byfilesystemtype' / 'heaobject.volume.MongoDBFileSystem').path,
                                        headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE})
        if not obj.ok:
            self.fail(f'GET request failed: {await obj.text()}')
        self.assertEqual([], await obj.json())

    async def test_get_volume_by_filesystem_type_and_name_with_bad_permissions(self) -> None:
        """
        Checks if a GET request for a volume whose file system type is heaobject.volume.MongoDBFileSystem and whose
        file system name is DEFAULT_FILE_SYSTEM succeeds but returns no objects when the user does not have
        permissions.
        """
        obj = await self.client.request('GET',
                                        (
                                                self._href / 'byfilesystemtype' / 'heaobject.volume.MongoDBFileSystem' / 'byfilesystemname' / 'DEFAULT_FILE_SYSTEM').path,
                                        headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE})
        if not obj.ok:
            self.fail(f'GET request failed: {await obj.text()}')
        self.assertEqual([], await obj.json())


class TestVolumePostWithBadPermissions(VolumePermissionsTestCase, PermissionsPostMixin):
    pass


class TestVolumePutWithBadPermissions(VolumePermissionsTestCase, PermissionsPutMixin):
    pass


class TestVolumeDeleteWithBadPermissions(VolumePermissionsTestCase, PermissionsDeleteMixin):
    pass


class TestFileSystemGetWithBadPermissions(FileSystemPermissionsTestCase, PermissionsGetOneMixin):
    async def test_get_filesystem_with_type_and_name_with_bad_permissions(self) -> None:
        """
        Checks if a GET request for the filesystem whose type is heaobject.volume.AWSFileSystem and whose name
        is DEFAULT_FILE_SYSTEM fails with status 404 when the user has bad permissions.
        """
        obj = await self.client.request('GET',
                                        (self._href / 'bytype' / 'heaobject.volume.AWSFileSystem' / 'byname' / 'DEFAULT_FILE_SYSTEM').path,
                                        headers={**self._headers, hdrs.ACCEPT: nvpjson.MIME_TYPE})
        self.assertEqual(404, obj.status)


class TestFileSystemGetAllWithBadPermissions(FileSystemPermissionsTestCase, PermissionsGetAllMixin):
    pass


class TestFileSystemPostWithBadPermissions(FileSystemPermissionsTestCase, PermissionsPostMixin):
    pass


class TestFileSystemPutWithBadPermissions(FileSystemPermissionsTestCase, PermissionsPutMixin):
    pass


class TestFileSystemDeleteWithBadPermissions(FileSystemPermissionsTestCase, PermissionsDeleteMixin):
    pass
