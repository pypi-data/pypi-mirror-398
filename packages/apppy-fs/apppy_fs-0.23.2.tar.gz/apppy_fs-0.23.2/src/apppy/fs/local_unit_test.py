import pytest

from apppy.fs import FileSystemBucket, FileUrl
from apppy.fs.local import LocalFileUrl

_local_fs_bucket_external_test = FileSystemBucket(bucket_type="internal", value="./.file_store")

_case_dir_only: LocalFileUrl = LocalFileUrl(
    _filesystem_bucket=_local_fs_bucket_external_test,
    _partition="partition",
    _directory="dir",
    _file_name=None,
)
_case_dir_with_subdir: LocalFileUrl = LocalFileUrl(
    _filesystem_bucket=_local_fs_bucket_external_test,
    _partition="partition",
    _directory="dir/subdir",
    _file_name=None,
)
_case_file_name_only: LocalFileUrl = LocalFileUrl(
    _filesystem_bucket=_local_fs_bucket_external_test,
    _partition="partition",
    _directory=None,
    _file_name="f.txt",
)
_case_file_name_with_dir: LocalFileUrl = LocalFileUrl(
    _filesystem_bucket=_local_fs_bucket_external_test,
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "local://internal/partition/dir"),
        (_case_dir_with_subdir, "local://internal/partition/dir/subdir"),
        (_case_file_name_only, "local://internal/partition/f.txt"),
        (_case_file_name_with_dir, "local://internal/partition/dir/f.txt"),
    ],
)
def test_local_file_url_str(file_url: FileUrl, expected_str: str):
    assert str(file_url) == expected_str


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "local://./.file_store/partition/dir"),
        (_case_dir_with_subdir, "local://./.file_store/partition/dir/subdir"),
        (_case_file_name_only, "local://./.file_store/partition/f.txt"),
        (_case_file_name_with_dir, "local://./.file_store/partition/dir/f.txt"),
    ],
)
def test_local_file_url_str_internal(file_url: FileUrl, expected_str: str):
    assert file_url.as_str_internal() == expected_str


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("internal/partition/dir", _case_dir_only),
        ("internal/partition/dir/subdir", _case_dir_with_subdir),
        ("internal/partition/f.txt", _case_file_name_only),
        ("internal/partition/dir/f.txt", _case_file_name_with_dir),
    ],
)
def test_local_file_url_split_path(path: str, expected_file_url: FileUrl):
    file_url = LocalFileUrl.split_path(
        path, protocol="local", bucket=_local_fs_bucket_external_test
    )
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("./.file_store/partition/dir", _case_dir_only),
        ("./.file_store/partition/dir/subdir", _case_dir_with_subdir),
        ("./.file_store/partition/f.txt", _case_file_name_only),
        ("./.file_store/partition/dir/f.txt", _case_file_name_with_dir),
    ],
)
def test_local_file_url_split_path_unobfuscated(path: str, expected_file_url: FileUrl):
    file_url = LocalFileUrl.split_path(
        path, protocol="local", bucket=_local_fs_bucket_external_test
    )
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "url, expected_file_url",
    [
        ("local://./.file_store/partition/dir", _case_dir_only),
        ("local://./.file_store/partition/dir/subdir", _case_dir_with_subdir),
        ("local://./.file_store/partition/f.txt", _case_file_name_only),
        ("local://./.file_store/partition/dir/f.txt", _case_file_name_with_dir),
    ],
)
def test_local_file_url_split_url(url: str, expected_file_url: FileUrl):
    file_url = LocalFileUrl.split_url(url, bucket=_local_fs_bucket_external_test)
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_dir_only),
        (_case_dir_with_subdir),
    ],
)
def test_local_file_url_is_directory(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is True
    assert file_url.is_file is False


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_file_name_only),
        (_case_file_name_with_dir),
    ],
)
def test_local_file_url_is_file(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is False
    assert file_url.is_file is True


@pytest.mark.parametrize(
    "file_url, join_dir, join_file_name, expected_joined_path",
    [
        (_case_dir_only, None, None, "local://./.file_store/partition/dir"),
        (_case_dir_only, "join_dir", None, "local://./.file_store/partition/dir/join_dir"),
        (_case_dir_only, None, "join_f.txt", "local://./.file_store/partition/dir/join_f.txt"),
        (
            _case_dir_only,
            "join_dir",
            "join_f.txt",
            "local://./.file_store/partition/dir/join_dir/join_f.txt",
        ),
    ],
)
def test_local_file_url_join(
    file_url: LocalFileUrl,
    join_dir: str | None,
    join_file_name: str | None,
    expected_joined_path: str,
):
    joined_file_url = file_url.join(directory=join_dir, file_name=join_file_name)
    assert joined_file_url.as_str_internal() == expected_joined_path


@pytest.mark.parametrize(
    "file_url, expected_parent_path",
    [
        (_case_dir_only, "local://./.file_store/partition"),
        (_case_dir_with_subdir, "local://./.file_store/partition/dir"),
        (_case_file_name_only, "local://./.file_store/partition"),
        (_case_file_name_with_dir, "local://./.file_store/partition/dir"),
    ],
)
def test_local_file_url_parent(file_url: LocalFileUrl, expected_parent_path: str):
    parent_file_url = file_url.parent()
    assert parent_file_url.as_str_internal() == expected_parent_path
