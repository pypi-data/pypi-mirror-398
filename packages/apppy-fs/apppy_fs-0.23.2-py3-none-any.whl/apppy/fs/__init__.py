import hashlib
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from fsspec import AbstractFileSystem
from fsspec.utils import stringify_path
from pydantic import Field

from apppy.env import Env, EnvSettings
from apppy.fs.errors import (
    FileSystemNotFoundError,
    FileSystemPermissionsError,
    FileSystemSizeLimitExceededError,
    MalformedFileUrlError,
)
from apppy.fs.hash import hasher
from apppy.generic.encrypt import BytesEncrypter
from apppy.logger import WithLogger

FileSystemBucketType = Literal["external", "internal"]


@dataclass
class FileSystemBucket:
    bucket_type: FileSystemBucketType
    value: str

    @property
    def is_external(self) -> bool:
        return self.bucket_type == "external"


class FileUrl(ABC):
    ##### ##### ##### URL Parts ##### ##### #####
    @property
    @abstractmethod
    def filesystem_protocol(self) -> str:
        pass

    @property
    def filesystem_protocol_unencrypted(self) -> str:
        return self.filesystem_protocol.removeprefix("enc://")

    @property
    @abstractmethod
    def filesystem_bucket(self) -> FileSystemBucket:
        pass

    @property
    @abstractmethod
    def filesystem_external_id(self) -> str | None:
        pass

    @property
    @abstractmethod
    def partition(self) -> str:
        pass

    @property
    @abstractmethod
    def directory(self) -> str | None:
        pass

    @property
    @abstractmethod
    def file_name(self) -> str | None:
        pass

    ##### ##### ##### URL Utils ##### ##### #####
    @abstractmethod
    def as_str(self, obfuscate: bool = True, unencrypted: bool = False) -> str:
        # There are two types of string representation for a
        # FileUrl -- the internal one which includes details about
        # the bucket. And the external one which obfuscates these details.
        # We want obfuscation when exposing the url to a third party
        # (e.g. when sending the url in an API response) to guard internal
        # details of the filesystem. However, the internal code requires
        # knowledge about the bucket's value.
        #
        # Note that we also allow the caller to strip the encryption protocol
        # from the url if it exists.
        pass

    def as_str_external(self) -> str:
        return self.as_str(obfuscate=True, unencrypted=False)

    def as_str_internal(self) -> str:
        return self.as_str(obfuscate=False, unencrypted=True)

    @abstractmethod
    def join(self, directory: str | None, file_name: str | None) -> "FileUrl":
        pass

    @abstractmethod
    def parent(self) -> "FileUrl":
        pass

    @property
    @abstractmethod
    def is_directory(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_encrypted(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_file(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        pass

    @staticmethod
    def _parse_protocol(url: str, unencrypted: bool = True) -> str:
        # This is mostly copied from the fsspec util
        # get_protocol. However, we tweak the split
        # logic to handle multiple protocols (e.g. for
        # encryption like enc://sb )
        file_url = stringify_path(url)
        parts = re.split(r"(\:\:|\://)", str(file_url), maxsplit=2)
        # CASE: 2 protocols (e.g. enc://sb://)
        if len(parts) > 3:
            protocol = f"{parts[0]}://{parts[2]}"
        # CASE: 1 protocol (e.g. sb://)
        elif len(parts) > 1:
            protocol = parts[0]
        # CASE: 0 protocols
        else:
            raise MalformedFileUrlError(url=url)
        if unencrypted is True:
            return protocol.removeprefix("enc://")

        return protocol

    @staticmethod
    @abstractmethod
    def split_path(path: str, protocol: str, bucket: FileSystemBucket) -> "FileUrl":
        pass

    @staticmethod
    @abstractmethod
    def split_url(url: str, bucket: FileSystemBucket) -> "FileUrl":
        pass


generic_filesystem_bucket_external = FileSystemBucket(bucket_type="external", value="external")
generic_filesystem_bucket_internal = FileSystemBucket(bucket_type="internal", value="internal")


@dataclass
class GenericFileUrl(FileUrl):
    _filesystem_protocol: str
    _filesystem_bucket: FileSystemBucket
    _filesystem_external_id: str | None
    _partition: str
    _directory: str | None
    _file_name: str | None

    @property
    def filesystem_protocol(self) -> str:
        return self._filesystem_protocol

    @property
    def filesystem_bucket(self) -> FileSystemBucket:
        return self._filesystem_bucket

    @property
    def filesystem_external_id(self) -> str | None:
        return self._filesystem_external_id

    @property
    def partition(self) -> str:
        return self._partition

    @property
    def directory(self) -> str | None:
        return self._directory

    @property
    def file_name(self) -> str | None:
        return self._file_name

    def __str__(self) -> str:
        # By default, obfuscate the string representation
        return self.as_str(obfuscate=True)

    def as_str(self, obfuscate: bool = True, unencrypted: bool = False) -> str:
        # See comment in FileUrl regarding obfuscation
        bucket_part = (
            self._filesystem_bucket.bucket_type if obfuscate else self._filesystem_bucket.value
        )

        protocol = (
            self._filesystem_protocol
            if unencrypted is False
            else self._filesystem_protocol.removeprefix("enc://")
        )
        joined_file_url = f"{protocol}://{bucket_part}/{self._partition}"

        if self.directory is not None:
            joined_file_url = f"{joined_file_url}/{self.directory}"

        if self.is_directory:
            return joined_file_url

        if self._filesystem_external_id is not None and self._file_name is not None:
            joined_file_url = f"{joined_file_url}/@{self._filesystem_external_id}${self._file_name}"
        elif self._filesystem_external_id is not None:
            joined_file_url = f"{joined_file_url}/@{self._filesystem_external_id}"
        elif self._file_name is not None:
            joined_file_url = f"{joined_file_url}/{self._file_name}"

        return joined_file_url

    def join(self, directory: str | None, file_name: str | None) -> "FileUrl":
        if self.file_name is not None:
            raise MalformedFileUrlError(
                url=self.as_str_internal(), code="joining_with_existing_file_name"
            )

        new_file_url = GenericFileUrl(
            _filesystem_protocol=self.filesystem_protocol,
            _filesystem_bucket=self.filesystem_bucket,
            _filesystem_external_id=self.filesystem_external_id,
            _partition=self.partition,
            _directory=self.directory,
            _file_name=None,
        )
        if directory is not None and new_file_url.directory is None:
            new_file_url._directory = directory
        elif directory is not None and new_file_url.directory is not None:
            new_file_url._directory = f"{new_file_url._directory}/{directory}"

        if file_name is not None:
            new_file_url._file_name = file_name

        return new_file_url

    def parent(self) -> "FileUrl":
        if self.file_name is not None:
            return GenericFileUrl(
                _filesystem_protocol=self.filesystem_protocol,
                _filesystem_bucket=self.filesystem_bucket,
                _filesystem_external_id=None,
                _partition=self.partition,
                _directory=self.directory,
                _file_name=None,
            )
        elif self.directory is not None:
            directory_path = Path(self.directory)
            directory_parent = str(directory_path.parent)
            return GenericFileUrl(
                _filesystem_protocol=self.filesystem_protocol,
                _filesystem_bucket=self.filesystem_bucket,
                _filesystem_external_id=None,
                _partition=self.partition,
                _directory=(directory_parent if directory_parent != "." else None),
                _file_name=None,
            )

        # Note that we never remove the partition. In other words,
        # the partition is the root of the FileUrl.
        return GenericFileUrl(
            _filesystem_protocol=self.filesystem_protocol,
            _filesystem_bucket=self.filesystem_bucket,
            _filesystem_external_id=None,
            _partition=self.partition,
            _directory=None,
            _file_name=None,
        )

    @property
    def is_directory(self) -> bool:
        return (
            self._filesystem_external_id is None
            and self._directory is not None
            and self._file_name is None
        )

    @property
    def is_encrypted(self) -> bool:
        return self.filesystem_protocol.startswith("enc")

    @property
    def is_file(self) -> bool:
        return self.is_directory is False

    @property
    def is_valid(self) -> bool:
        return self.is_directory or self.is_file

    @staticmethod
    def split_path(path: str, protocol: str, bucket: FileSystemBucket) -> "FileUrl":
        path = path.strip()

        if path.startswith(bucket.bucket_type):
            path_body = path[len(bucket.bucket_type) :].lstrip("/")
        elif path.startswith(bucket.value):
            path_body = path[len(bucket.value) :].lstrip("/")
        else:
            raise MalformedFileUrlError(f"{protocol}://{path}")

        parts = path_body.split("/") if path_body else []

        if not parts or len(parts) < 2:
            # CASE: just partition
            raise MalformedFileUrlError(f"{protocol}://{path}")
        partition = parts[0]

        directory = None
        file_name = None
        filesystem_external_id = None

        last = parts[-1]

        # CASE: readable with @
        if last.startswith("@"):
            *directory_parts, last_part = parts[1:]
            directory = "/".join(directory_parts) if directory_parts else None

            payload = last_part[1:]
            if "$" in payload:
                filesystem_external_id, file_name = payload.split("$", 1)
            else:
                filesystem_external_id = payload
                file_name = None

        else:
            *directory_parts, last_part = parts[1:]

            # Determine by file extension
            name, ext = os.path.splitext(last_part)
            if ext:
                file_name = last_part
                directory = "/".join(directory_parts) if directory_parts else None
            else:
                # No extension = treat entire thing as directory
                directory = "/".join(parts[1:])
                file_name = None

        return GenericFileUrl(
            _filesystem_protocol=protocol,
            _filesystem_bucket=bucket,
            _filesystem_external_id=filesystem_external_id,
            _partition=partition,
            _directory=directory,
            _file_name=file_name,
        )

    @staticmethod
    def split_url(url: str, bucket: FileSystemBucket) -> "FileUrl":
        url = url.strip()
        protocol = GenericFileUrl._parse_protocol(url, unencrypted=False)
        path = url[len(f"{protocol}://") :]

        return GenericFileUrl.split_path(path=path, protocol=protocol, bucket=bucket)


class FileSystemPermission(Enum):
    # Marks public external file system implementations
    # which are visible for public consumption
    PUBLIC_EXTERNAL = "public_external"
    # Marks private internal file system implementations
    # which are obfuscated from public consumption
    PRIVATE_INTERNAL = "private_internal"
    READONLY = "readonly"
    READWRITE = "readwrite"


class ProxyFileSystem(ABC):
    @abstractmethod
    def convert_file_url(self, file_url: FileUrl) -> FileUrl:
        pass

    @abstractmethod
    def file_url_kwargs(self, file_url: FileUrl) -> dict[str, Any]:
        pass

    @abstractmethod
    def parse_file_url(self, url: str) -> FileUrl:
        pass

    def has_permissions(
        self, permissions_to_check: list[FileSystemPermission] | None = None
    ) -> bool:
        # Special case whereby if we have no permission
        # checks then we'll just return in the affirmative
        if permissions_to_check is None:
            return True

        is_subset = set(permissions_to_check).issubset(self.permissions)
        return is_subset

    @abstractmethod
    def rm(self, url: str, recursive=False, maxdepth=None, **kwargs) -> None:
        # Create a required proxy for file removal. The native rm()
        # method does not include **kwargs which are required by some
        # filesystem plugin in order to work correctly.
        pass

    @property
    @abstractmethod
    def encryption(self) -> BytesEncrypter | None:
        pass

    @property
    def is_encrypted(self) -> bool:
        return self.encryption is not None

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def native(self) -> AbstractFileSystem:
        pass

    @property
    @abstractmethod
    def permissions(self) -> list[FileSystemPermission]:
        pass


class FileSystemSettings(EnvSettings):
    # FS_FILE_MAX_SIZE_MB
    file_max_size_mb: int = Field(default=32)
    # FS_DEFAULT_PROTOCOL
    default_protocol: str = Field(default="local")

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="FS")


class FileSystem(WithLogger):
    def __init__(self, settings: FileSystemSettings) -> None:
        self._settings = settings
        self._file_max_size_bytes = settings.file_max_size_mb * 1024 * 1024

        self._proxyfs_by_protocol: dict[str, ProxyFileSystem] = {}
        self._nativefs_by_protocol: dict[
            str, AbstractFileSystem | Callable[[], AbstractFileSystem]
        ] = {}

    ##### ##### ##### Registry Controls ##### ##### #####

    def load_proxyfss(
        self, permissions: list[FileSystemPermission] | None = None
    ) -> set[ProxyFileSystem]:
        if permissions is None:
            permissions = []

        results: set[ProxyFileSystem] = set()
        for _, proxyfs in self._proxyfs_by_protocol.items():
            if proxyfs.has_permissions(permissions):
                results.add(proxyfs)

        return results

    def load_proxyfs(self, file_url: FileUrl) -> tuple[str, ProxyFileSystem]:
        return self.load_proxyfs_by_protocol(file_url.filesystem_protocol_unencrypted)

    def load_proxyfs_by_protocol(self, protocol: str) -> tuple[str, ProxyFileSystem]:
        proxyfs = self._proxyfs_by_protocol.get(protocol)
        if proxyfs is None:
            self._logger.error(
                "No registered proxy FileSystem for protocol", extra={"protocol": protocol}
            )
            raise FileSystemNotFoundError(protocol=protocol)

        return protocol, proxyfs

    def load_nativefs(self, file_url: FileUrl) -> tuple[str, AbstractFileSystem]:
        return self.load_nativefs_by_protocol(file_url.filesystem_protocol_unencrypted)

    def load_nativefs_by_protocol(self, protocol: str) -> tuple[str, AbstractFileSystem]:
        native_fs = self._nativefs_by_protocol.get(protocol)
        if native_fs is None:
            self._logger.error(
                "No registered native FileSystem for url", extra={"protocol": protocol}
            )
            raise FileSystemNotFoundError(protocol=protocol)
        elif callable(native_fs):
            return protocol, native_fs()

        return protocol, native_fs

    def register(
        self, proxyfs: ProxyFileSystem, alt_protocol: str | tuple[str, ...] | None = None
    ) -> None:
        if alt_protocol is not None and isinstance(alt_protocol, tuple):
            for p in alt_protocol:
                self.register_proxyfs(fs=proxyfs, protocol=p)
                self.register_nativefs(fs=proxyfs.native, protocol=p)
        elif alt_protocol is not None and isinstance(alt_protocol, str):
            self.register_proxyfs(fs=proxyfs, protocol=alt_protocol)
            self.register_nativefs(fs=proxyfs.native, protocol=alt_protocol)
        elif isinstance(proxyfs.native.protocol, tuple):
            for p in proxyfs.native.protocol:
                self.register_proxyfs(fs=proxyfs, protocol=p)
                self.register_nativefs(fs=proxyfs.native, protocol=p)
        else:
            self.register_proxyfs(fs=proxyfs, protocol=proxyfs.native.protocol)
            self.register_nativefs(fs=proxyfs.native, protocol=proxyfs.native.protocol)

    def register_proxyfs(self, fs: ProxyFileSystem, protocol: str) -> None:
        self._logger.info(
            "Registering proxy filesystem",
            extra={"protocol": protocol, "class_name": fs.__class__.__name__},
        )
        self._proxyfs_by_protocol[protocol] = fs

    def register_nativefs(
        self, fs: AbstractFileSystem | Callable[[], AbstractFileSystem], protocol: str
    ) -> None:
        self._logger.info(
            "Registering native filesystem",
            extra={"protocol": protocol, "class_name": fs.__class__.__name__},
        )
        self._nativefs_by_protocol[protocol] = fs

    ##### ##### ##### Helper Utilities ##### ##### #####

    def convert_file_url(self, url: FileUrl) -> FileUrl:
        _, proxyfs = self.load_proxyfs(url)
        if type(url) is GenericFileUrl:
            return proxyfs.convert_file_url(file_url=url)

        if not url.is_encrypted and proxyfs.is_encrypted:
            # In some limited cases, we may have an unencrypted
            # URL attempting to interact with an encrypted filesystem
            # For those cases, allow the filesystem to convert to an
            # encrypted url
            return proxyfs.convert_file_url(file_url=url)

        return url

    def new_file_url_external(
        self,
        protocol: str,
        external_id: str | None,
        partition: str,
        directory: str | None,
        file_name: str | None,
    ) -> FileUrl:
        return self.convert_file_url(
            GenericFileUrl(
                _filesystem_protocol=protocol,
                _filesystem_bucket=generic_filesystem_bucket_external,
                _filesystem_external_id=external_id,
                _partition=partition,
                _directory=directory,
                _file_name=file_name,
            )
        )

    def new_file_url_internal(
        self,
        protocol: str,
        partition: str,
        directory: str | None,
        file_name: str | None,
    ) -> FileUrl:
        return self.convert_file_url(
            GenericFileUrl(
                _filesystem_protocol=protocol,
                _filesystem_bucket=generic_filesystem_bucket_internal,
                _filesystem_external_id=None,
                _partition=partition,
                _directory=directory,
                _file_name=file_name,
            )
        )

    def parse_file_url(self, url: str) -> FileUrl:
        unencrypted = bool(not url.startswith("enc"))
        protocol = GenericFileUrl._parse_protocol(url, unencrypted=unencrypted)
        _, proxyfs = self.load_proxyfs_by_protocol(protocol)
        return proxyfs.parse_file_url(url)

    @property
    def settings(self) -> FileSystemSettings:
        return self._settings

    ##### ##### ##### FileSystem Implementation ##### ##### #####

    def checksum_contents(
        self,
        contents: bytes,
        *,
        h: "hashlib._Hash",
        **kwargs,
    ) -> str:
        h.update(contents)
        return h.hexdigest()

    def checksum_file(
        self,
        url: "FileUrl",
        *,
        algo: str = "sha256",
        **kwargs,
    ) -> str:
        contents = self.read_bytes(url, **kwargs)
        return self.checksum_contents(contents=contents, h=hasher(algo), **kwargs)

    # TODO: Implement
    # def created(self, url: FileUrl) -> datetime.datetime:
    #     _, proxyfs = self.load_proxyfs(url)
    #     return proxyfs.native.created(url.as_str_internal())

    def exists(self, url: FileUrl, **kwargs) -> bool:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)
        return proxyfs.native.exists(
            file_url.as_str_internal(), **proxyfs.file_url_kwargs(file_url)
        )

    # TODO: Implement
    # def get_latest_file(self, path: FileUrl) -> dict | None:
    #     protocol, nativefs = self.load_nativefs(path)
    #     if not nativefs.exists(file_url_full(path)):
    #         self._logger.warning(
    #             "Path does not exist in call to get_latest_file", extra={"path": path}
    #         )
    #         return None

    #     ls_results = nativefs.ls(path=file_url_full(path), detail=True)
    #     files = []
    #     for f in ls_results:
    #         if "url" not in f:
    #             f["url"] = f"{protocol}://{f['name']}"
    #         if "type" in f and f["type"] == "file":
    #             if "modified" not in f:
    #                 f["modified"] = nativefs.modified(f["name"])
    #             files.append(f)

    #     if len(files) == 0:
    #         return None

    #     sorted_files = sorted(files, key=lambda f: f["modified"], reverse=True)
    #     return sorted_files[0]

    def isdir(self, url: FileUrl) -> bool:
        return url.is_directory

    def isfile(self, url: FileUrl) -> bool:
        return url.is_file

    def ls(self, url: FileUrl, detail: bool = True, **kwargs) -> list[dict]:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)

        # JSON Payload:
        # - name
        # - size
        # - type
        # - created
        # - islink
        # - mode
        # - uid
        # - gid
        # - mtime
        # - ino
        # - nlink
        ls_results = proxyfs.native.ls(
            file_url.as_str_internal(),
            detail,
            **proxyfs.file_url_kwargs(file_url),
        )
        if detail:
            for f in ls_results:
                if "url" not in f:
                    f["url"] = f"{file_url.filesystem_protocol}://{f['name']}"

        return ls_results

    def makedir(self, url: FileUrl, create_parents=True, **kwargs) -> None:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)

        proxyfs.native.makedir(file_url.as_str_internal(), create_parents, **kwargs)

    # TODO: Implement
    # def modified(self, url: FileUrl) -> datetime.datetime:
    #     _, nativefs = self.load_nativefs(path)
    #     return nativefs.modified(file_url_full(path))

    def read_bytes(
        self, url: FileUrl, start: int | None = None, end: int | None = None, **kwargs
    ) -> bytes:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)
        # TODO: Permissions checks?

        if file_url.is_encrypted and proxyfs.encryption is None:
            self._logger.error(
                "Attempting encrypted read from unencrypted FileSystem",
                extra={"file_url": file_url.as_str_internal()},
            )
            raise FileSystemPermissionsError("encrypted_read_from_unencrypted_filesystem")

        read_bytes = proxyfs.native.read_bytes(
            file_url.as_str_internal(),
            start,
            end,
            **proxyfs.file_url_kwargs(file_url),
        )
        if file_url.is_encrypted and proxyfs.encryption is not None:
            return proxyfs.encryption.decrypt_bytes(read_bytes)

        return read_bytes

    def rm(self, url: FileUrl, recursive=False, maxdepth=None):
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)

        proxyfs.rm(
            url=file_url.as_str_internal(),
            recursive=recursive,
            maxdepth=maxdepth,
            **proxyfs.file_url_kwargs(file_url),
        )

    async def write_bytes(self, url: FileUrl, value, **kwargs) -> tuple[FileUrl, str]:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)

        if proxyfs.has_permissions([FileSystemPermission.READONLY]):
            self._logger.error(
                "Attempting write to readonly FileSystem",
                extra={"file_url": file_url.as_str_internal()},
            )
            raise FileSystemPermissionsError("write_to_readonly_filesystem")

        if file_url.is_encrypted and proxyfs.encryption is None:
            self._logger.error(
                "Attempting encrypted write to unencrypted FileSystem",
                extra={"file_url": file_url.as_str_internal()},
            )
            raise FileSystemPermissionsError("encrypted_write_to_unencrypted_filesystem")

        # Enforce max file size (plaintext)
        try:
            file_size_bytes = memoryview(value).nbytes  # avoids copy if possible
        except TypeError:
            file_size_bytes = len(value)

        if file_size_bytes > self._file_max_size_bytes:
            self._logger.warning(
                "File too large for write_bytes",
                extra={
                    "file_url": file_url.as_str_internal(),
                    "file_size_bytes": file_size_bytes,
                    "file_size_bytes_max": self._file_max_size_bytes,
                },
            )
            raise FileSystemSizeLimitExceededError(
                file_size=file_size_bytes, file_size_max=self._file_max_size_bytes
            )

        file_contents = (
            proxyfs.encryption.encrypt_bytes(value)
            if file_url.is_encrypted and proxyfs.encryption is not None
            else value
        )
        proxyfs.native.write_bytes(
            path=file_url.as_str_internal(),
            value=file_contents,
            **proxyfs.file_url_kwargs(file_url),
        )

        return file_url, self.checksum_contents(value, h=hasher("sha256"))

    async def write_file(self, url: FileUrl, file: Any, **kwargs) -> tuple[FileUrl, str]:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)

        if proxyfs.has_permissions([FileSystemPermission.READONLY]):
            self._logger.error(
                "Attempting write to readonly FileSystem",
                extra={"file_url": file_url.as_str_internal()},
            )
            raise FileSystemPermissionsError("write_to_readonly_filesystem")

        if file_url.is_encrypted and not proxyfs.is_encrypted:
            self._logger.error(
                "Attempting encrypted write to unencrypted FileSystem",
                extra={"file_url": file_url.as_str_internal()},
            )
            raise FileSystemPermissionsError("encrypted_write_to_unencrypted_filesystem")

        if isinstance(file, str | os.PathLike):
            # Pre-check max file size using filesystem stat if we can
            try:
                file_size_bytes = os.path.getsize(file)
            except OSError:
                file_size_bytes = None

            if file_size_bytes is not None and file_size_bytes > self._file_max_size_bytes:
                self._logger.warning(
                    "File too large for write_file",
                    extra={
                        "size_check_method": "os_stat",
                        "file_url": file_url.as_str_internal(),
                        "file_size_bytes": file_size_bytes,
                        "file_size_bytes_max": self._file_max_size_bytes,
                    },
                )
                raise FileSystemSizeLimitExceededError(
                    file_size=file_size_bytes, file_size_max=self._file_max_size_bytes
                )

            with open(file, "rb") as fd:
                file_data = fd.read()
                if len(file_data) > self._file_max_size_bytes:
                    self._logger.warning(
                        "File too large for write_file",
                        extra={
                            "size_check_method": "data_read",
                            "file_url": file_url.as_str_internal(),
                            "file_size_bytes": len(file_data),
                            "file_size_bytes_max": self._file_max_size_bytes,
                        },
                    )
                    raise FileSystemSizeLimitExceededError(
                        file_size=len(file_data), file_size_max=self._file_max_size_bytes
                    )

                file_contents = (
                    proxyfs.encryption.encrypt_bytes(file_data)
                    if file_url.is_encrypted and proxyfs.encryption is not None
                    else file_data
                )
                proxyfs.native.write_bytes(
                    file_url.as_str_internal(),
                    file_contents,
                    **proxyfs.file_url_kwargs(file_url),
                )
        else:
            file_data = file.read()
            if len(file_data) > self._file_max_size_bytes:
                self._logger.warning(
                    "File too large for write_file",
                    extra={
                        "file_url": file_url.as_str_internal(),
                        "file_size_bytes": len(file_data),
                        "file_size_bytes_max": self._file_max_size_bytes,
                    },
                )
                raise FileSystemSizeLimitExceededError(
                    file_size=len(file_data), file_size_max=self._file_max_size_bytes
                )
            # NOTE: This is only going to work if the caller awaits
            # on this call. Otherwise, the file object will likely be
            # close before we get a chance to read it.
            file_contents = (
                proxyfs.encryption.encrypt_bytes(file_data)
                if file_url.is_encrypted and proxyfs.encryption is not None
                else file_data
            )
            proxyfs.native.write_bytes(
                file_url.as_str_internal(),
                file_contents,
                **proxyfs.file_url_kwargs(file_url),
            )

        return file_url, self.checksum_contents(file_data, h=hasher("sha256"))

    async def write_text(
        self, url: FileUrl, value, encoding=None, errors=None, newline=None, **kwargs
    ) -> tuple[FileUrl, str]:
        file_url = self.convert_file_url(url)
        _, proxyfs = self.load_proxyfs(file_url)

        if proxyfs.has_permissions([FileSystemPermission.READONLY]):
            self._logger.error(
                "Attempting write to readonly FileSystem",
                extra={"file_url": file_url.as_str_internal()},
            )
            raise FileSystemPermissionsError("write_to_readonly_filesystem")

        value_encoding = "utf-8" if encoding is None else encoding
        if file_url.is_encrypted:
            if proxyfs.encryption is None:
                self._logger.error(
                    "Attempting encrypted write to unencrypted FileSystem",
                    extra={"file_url": file_url.as_str_internal()},
                )
                raise FileSystemPermissionsError("encrypted_write_to_unencrypted_filesystem")

            # Enforce max size on encoded plaintext
            file_encoded = value.encode(value_encoding)
            if len(file_encoded) > self._file_max_size_bytes:
                self._logger.warning(
                    "File too large for write_text",
                    extra={
                        "encrypted": True,
                        "file_url": file_url.as_str_internal(),
                        "file_size_bytes": len(file_encoded),
                        "file_size_bytes_max": self._file_max_size_bytes,
                    },
                )
                raise FileSystemSizeLimitExceededError(
                    file_size=len(file_encoded), file_size_max=self._file_max_size_bytes
                )

            # The encryption workflow cannot work on plain text
            # so we actually need to write the text as bytes here
            proxyfs.native.write_bytes(
                file_url.as_str_internal(),
                proxyfs.encryption.encrypt_bytes(file_encoded),
                **proxyfs.file_url_kwargs(file_url),
            )

            return file_url, self.checksum_contents(file_encoded, h=hasher("sha256"))

        file_encoded = value.encode(value_encoding)
        if len(file_encoded) > self._file_max_size_bytes:
            self._logger.warning(
                "File too large for write_text",
                extra={
                    "encrypted": False,
                    "file_url": file_url.as_str_internal(),
                    "file_size_bytes": len(file_encoded),
                    "file_size_bytes_max": self._file_max_size_bytes,
                },
            )
            raise FileSystemSizeLimitExceededError(
                file_size=len(file_encoded), file_size_max=self._file_max_size_bytes
            )

        proxyfs.native.write_text(
            file_url.as_str_internal(),
            value,
            value_encoding,
            errors,
            newline,
            **proxyfs.file_url_kwargs(file_url),
        )

        return file_url, self.checksum_contents(file_encoded, h=hasher("sha256"))
