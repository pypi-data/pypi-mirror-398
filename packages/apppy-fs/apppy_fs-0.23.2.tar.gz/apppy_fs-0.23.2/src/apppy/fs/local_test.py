import datetime

from apppy.env import DictEnv
from apppy.fs import FileSystem, FileSystemBucket, FileSystemSettings
from apppy.fs.local import LocalFileSystem, LocalFileSystemSettings

_local_fs_bucket_external_test = FileSystemBucket(bucket_type="external", value="./.file_store")

# Poor man's dependency injection
_env = DictEnv(prefix="APP", name="local_test", d={})
_fs_settings = FileSystemSettings(env=_env)
_fs = FileSystem(_fs_settings)
_fs_settings_local = LocalFileSystemSettings(env=_env)
_ = LocalFileSystem(settings=_fs_settings_local, fs=_fs)


async def test_local_write_bytes():
    file_url = _fs.new_file_url_external(
        protocol="local",
        external_id=None,
        partition="local_test",
        directory="test_local_write_bytes",
        # Include timestamp to avoid overwrites
        file_name=f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-file.txt",
    )

    assert file_url.is_encrypted is False

    await _fs.write_bytes(
        file_url, bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")
    )
    read_bytes = _fs.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_local_write_text():
    file_url = _fs.new_file_url_external(
        protocol="local",
        external_id=None,
        partition="fs_local_test",
        directory="test_local_write_text_unencrypted",
        # Include timestamp to avoid overwrites
        file_name=f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-file.txt",
    )

    assert file_url.is_encrypted is False

    await _fs.write_text(file_url, "The quick brown fox jumped over the lazy dogs.")
    read_bytes = _fs.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


# @pytest.mark.parametrize(
#     ("algo", "expected_checksum"),
#     [
#         (
#             "md5",
#             "5c9f966da28ab24ca7796006a6259494",
#         ),
#         (
#             "sha256",
#             "c9c85caa5a93aad2bfcc91b9a02d4185a0f0348aac049e650bd0f4dea10a7393",
#         ),
#     ],
# )
# async def test_local_checksum_file(file_write, algo, expected_checksum):
#     file_url = await file_write(
#         protocol="local", partition="fs_local_test", directory="test_local_checksum_file"
#     )

#     fs: FileSystem = app_local.fs()
#     checksum = fs.checksum_file(file_url, algo=algo)
#     assert checksum == expected_checksum
