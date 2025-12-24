from apppy.fs import FileSystem
from apppy.fs.fixtures import local_fs  # noqa: F401
from apppy.fs.local import LocalFileSystem


def test_load_local_proxyfs_by_protocol(local_fs: FileSystem):  # noqa: F811
    _, proxyfs = local_fs.load_proxyfs_by_protocol("local")
    assert proxyfs is not None
    assert isinstance(proxyfs, LocalFileSystem) is True
