from pathlib import Path
from typing import Any

from fsspec.implementations.local import LocalFileSystem as NativeLocalFileSystem
from pydantic import Field

from apppy.env import Env, EnvSettings
from apppy.fs import (
    FileSystem,
    FileSystemBucket,
    FileSystemPermission,
    FileUrl,
    GenericFileUrl,
    ProxyFileSystem,
)
from apppy.fs.errors import MalformedFileUrlError
from apppy.generic.encrypt import BytesEncrypter
from apppy.logger import WithLogger


class LocalFileUrl(GenericFileUrl):
    def __init__(
        self,
        _filesystem_bucket: FileSystemBucket,
        _partition: str,
        _directory: str | None,
        _file_name: str | None,
    ) -> None:
        super().__init__(
            _filesystem_protocol="local",
            _filesystem_bucket=_filesystem_bucket,
            _filesystem_external_id=None,
            _partition=_partition,
            _directory=_directory,
            _file_name=_file_name,
        )
        self._root_dir = _filesystem_bucket.value
        str_instance = self.as_str_internal()

        # Validation
        if _filesystem_bucket.is_external:
            raise MalformedFileUrlError(
                url=str_instance, code="local_file_url_with_external_bucket"
            )

    @staticmethod
    def split_path(path: str, protocol: str, bucket: FileSystemBucket) -> "LocalFileUrl":
        generic_file_url = GenericFileUrl.split_path(path=path, protocol=protocol, bucket=bucket)

        return LocalFileUrl(
            _filesystem_bucket=bucket,
            _partition=generic_file_url.partition,
            _directory=generic_file_url.directory,
            _file_name=generic_file_url.file_name,
        )

    @staticmethod
    def split_url(url: str, bucket: FileSystemBucket) -> "LocalFileUrl":
        url = url.strip()
        protocol = GenericFileUrl._parse_protocol(url, unencrypted=False)
        path = url[len(f"{protocol}://") :]

        # In some cases, we'll be dealing with the absolute path
        # whereas the default bucket value is a relative path (e.g. ./.file_store)
        # For those cases, we'll try to transform the absolute
        # path into the relative path before continuing on
        path_p = Path(path)
        if path_p.is_absolute():
            bucket_path = Path(bucket.value).resolve()
            path_p = path_p.relative_to(bucket_path)
            path = f"{bucket.value}/{str(path_p)}"

        return LocalFileUrl.split_path(path=path, protocol=protocol, bucket=bucket)


class LocalFileSystemSettings(EnvSettings):
    # FS_LOCAL_ROOT_DIR
    root_dir: str = Field(default="./.file_store")

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="FS_LOCAL")


class LocalFileSystem(ProxyFileSystem, WithLogger):
    def __init__(self, settings: LocalFileSystemSettings, fs: FileSystem) -> None:
        self._bucket_internal = FileSystemBucket(
            bucket_type="internal",
            value=f"{settings.root_dir}",
        )

        self._nativefs: NativeLocalFileSystem = NativeLocalFileSystem(auto_mkdir=True)
        fs.register_proxyfs(self, "local")
        fs.register_nativefs(self._nativefs, "local")

    def convert_file_url(self, file_url: FileUrl) -> FileUrl:
        if isinstance(file_url, LocalFileUrl):
            return file_url

        return LocalFileUrl(
            _filesystem_bucket=self._bucket_internal,
            _partition=file_url.partition,
            _directory=file_url.directory,
            _file_name=file_url.file_name,
        )

    def file_url_kwargs(self, file_url: FileUrl) -> dict[str, Any]:
        # No extra parameters needed
        return {}

    def parse_file_url(self, url: str) -> LocalFileUrl:
        return LocalFileUrl.split_url(url, self._bucket_internal)

    def rm(self, url: str, recursive=False, maxdepth=None, **kwargs) -> None:
        self.native.rm(url, recursive=recursive, maxdepth=maxdepth)

    @property
    def encryption(self) -> BytesEncrypter | None:
        # For now, we'll just consider all locally stored
        # files as unencrypted.
        return None

    @property
    def name(self) -> str:
        return "Local"

    @property
    def native(self) -> NativeLocalFileSystem:
        return self._nativefs

    @property
    def permissions(self) -> list[FileSystemPermission]:
        return [
            FileSystemPermission.PRIVATE_INTERNAL,
            FileSystemPermission.READWRITE,
        ]
