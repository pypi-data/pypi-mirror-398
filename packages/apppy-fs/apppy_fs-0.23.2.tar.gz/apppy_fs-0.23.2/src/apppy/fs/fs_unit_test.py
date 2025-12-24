import pytest

from apppy.fs import (
    FileSystemBucket,
    FileUrl,
    GenericFileUrl,
)

_generic_fs_bucket_external_test = FileSystemBucket(bucket_type="external", value="fs_test")

_case_dir_only: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir",
    _file_name=None,
)
_case_dir_with_subdir: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir/subdir",
    _file_name=None,
)
_case_file_name_only: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id=None,
    _partition="partition",
    _directory=None,
    _file_name="f.txt",
)
_case_file_name_with_dir: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)
_case_unique_id_only: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory=None,
    _file_name=None,
)
_case_unique_id_with_dir: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name=None,
)
_case_unique_id_with_dir_and_file_name: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)
_case_unique_id_with_file_name: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory=None,
    _file_name="f.txt",
)
_case_unique_id_with_dir_and_file_name_encrypted: GenericFileUrl = GenericFileUrl(
    _filesystem_protocol="enc://prtcl",
    _filesystem_bucket=_generic_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "prtcl://external/partition/dir"),
        (_case_dir_with_subdir, "prtcl://external/partition/dir/subdir"),
        (_case_file_name_only, "prtcl://external/partition/f.txt"),
        (_case_file_name_with_dir, "prtcl://external/partition/dir/f.txt"),
        (_case_unique_id_only, "prtcl://external/partition/@123-abc"),
        (_case_unique_id_with_dir, "prtcl://external/partition/dir/@123-abc"),
        (_case_unique_id_with_dir_and_file_name, "prtcl://external/partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "prtcl://external/partition/@123-abc$f.txt"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "enc://prtcl://external/partition/dir/@123-abc$f.txt",
        ),
    ],
)
def test_generic_file_url_str(file_url: FileUrl, expected_str: str):
    assert str(file_url) == expected_str


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "prtcl://fs_test/partition/dir"),
        (_case_dir_with_subdir, "prtcl://fs_test/partition/dir/subdir"),
        (_case_file_name_only, "prtcl://fs_test/partition/f.txt"),
        (_case_file_name_with_dir, "prtcl://fs_test/partition/dir/f.txt"),
        (_case_unique_id_only, "prtcl://fs_test/partition/@123-abc"),
        (_case_unique_id_with_dir, "prtcl://fs_test/partition/dir/@123-abc"),
        (_case_unique_id_with_dir_and_file_name, "prtcl://fs_test/partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "prtcl://fs_test/partition/@123-abc$f.txt"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "prtcl://fs_test/partition/dir/@123-abc$f.txt",
        ),
    ],
)
def test_generic_file_url_str_internal(file_url: FileUrl, expected_str: str):
    assert file_url.as_str_internal() == expected_str


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("external/partition/dir", _case_dir_only),
        ("external/partition/dir/subdir", _case_dir_with_subdir),
        ("external/partition/f.txt", _case_file_name_only),
        ("external/partition/dir/f.txt", _case_file_name_with_dir),
        ("external/partition/@123-abc", _case_unique_id_only),
        ("external/partition/dir/@123-abc", _case_unique_id_with_dir),
        ("external/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("external/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
    ],
)
def test_generic_file_url_split_path(path: str, expected_file_url: FileUrl):
    file_url = GenericFileUrl.split_path(
        path, protocol="prtcl", bucket=_generic_fs_bucket_external_test
    )
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("fs_test/partition/dir", _case_dir_only),
        ("fs_test/partition/dir/subdir", _case_dir_with_subdir),
        ("fs_test/partition/f.txt", _case_file_name_only),
        ("fs_test/partition/dir/f.txt", _case_file_name_with_dir),
        ("fs_test/partition/@123-abc", _case_unique_id_only),
        ("fs_test/partition/dir/@123-abc", _case_unique_id_with_dir),
        ("fs_test/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("fs_test/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
    ],
)
def test_generic_file_url_split_path_unobfuscated(path: str, expected_file_url: FileUrl):
    file_url = GenericFileUrl.split_path(
        path, protocol="prtcl", bucket=_generic_fs_bucket_external_test
    )
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "url, expected_file_url",
    [
        ("prtcl://external/partition/dir", _case_dir_only),
        ("prtcl://external/partition/dir/subdir", _case_dir_with_subdir),
        ("prtcl://external/partition/f.txt", _case_file_name_only),
        ("prtcl://external/partition/dir/f.txt", _case_file_name_with_dir),
        ("prtcl://external/partition/@123-abc", _case_unique_id_only),
        ("prtcl://external/partition/dir/@123-abc", _case_unique_id_with_dir),
        ("prtcl://external/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("prtcl://external/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
        (
            "enc://prtcl://fs_test/partition/dir/@123-abc$f.txt",
            _case_unique_id_with_dir_and_file_name_encrypted,
        ),
    ],
)
def test_generic_file_url_split_url(url: str, expected_file_url: FileUrl):
    file_url = GenericFileUrl.split_url(url, bucket=_generic_fs_bucket_external_test)
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_dir_only),
        (_case_dir_with_subdir),
    ],
)
def test_generic_file_url_is_directory(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is True
    assert file_url.is_file is False


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_file_name_only),
        (_case_file_name_with_dir),
        (_case_unique_id_only),
        (_case_unique_id_with_dir_and_file_name),
        (_case_unique_id_with_dir),
        (_case_unique_id_with_file_name),
    ],
)
def test_generic_file_url_is_file(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is False
    assert file_url.is_file is True


@pytest.mark.parametrize(
    "file_url, expected_filesystem_protocol",
    [
        (_case_unique_id_with_dir_and_file_name, "prtcl"),
        (_case_unique_id_with_dir_and_file_name_encrypted, "enc://prtcl"),
    ],
)
def test_generic_file_url_filesystem_protocol(file_url: FileUrl, expected_filesystem_protocol: str):
    assert file_url.filesystem_protocol == expected_filesystem_protocol


@pytest.mark.parametrize(
    "file_url, expected_filesystem_protocol_unencrypted",
    [
        (_case_unique_id_with_dir_and_file_name, "prtcl"),
        (_case_unique_id_with_dir_and_file_name_encrypted, "prtcl"),
    ],
)
def test_generic_file_url_filesystem_protocol_unencrypted(
    file_url: FileUrl, expected_filesystem_protocol_unencrypted: str
):
    assert file_url.filesystem_protocol_unencrypted == expected_filesystem_protocol_unencrypted
