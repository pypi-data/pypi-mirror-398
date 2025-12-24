import pytest

from apppy.env import Env
from apppy.env.fixtures import current_test_name
from apppy.fs import FileSystem, FileSystemSettings
from apppy.fs.local import LocalFileSystem, LocalFileSystemSettings


@pytest.fixture(scope="session")
def local_fs():
    fs_env: Env = Env.load(name=current_test_name())
    fs_settings = FileSystemSettings(fs_env)
    fs = FileSystem(fs_settings)

    fs_local_settings = LocalFileSystemSettings(fs_env)
    _ = LocalFileSystem(fs_local_settings, fs)

    yield fs
