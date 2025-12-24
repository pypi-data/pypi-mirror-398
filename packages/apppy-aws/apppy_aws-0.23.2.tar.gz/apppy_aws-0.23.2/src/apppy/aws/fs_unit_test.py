import pytest

from apppy.aws.fs import S3FileUrl
from apppy.fs import FileSystemBucket, FileUrl

_s3_filesystem_bucket_external = FileSystemBucket(bucket_type="external", value="fs_s3_test")

_case_dir_only: S3FileUrl = S3FileUrl(
    _filesystem_protocol="s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir",
    _file_name=None,
)
_case_dir_with_subdir: S3FileUrl = S3FileUrl(
    _filesystem_protocol="s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir/subdir",
    _file_name=None,
)
# Valid url for version aware case
_case_file_name_only: S3FileUrl = S3FileUrl(
    _filesystem_protocol="s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id=None,
    _partition="partition",
    _directory=None,
    _file_name="f.txt",
)
# Valid url for version aware case
_case_file_name_with_dir: S3FileUrl = S3FileUrl(
    _filesystem_protocol="s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)
# Malformed url for the S3 case
# _case_unique_id_only: S3FileUrl = S3FileUrl(
#     _filesystem_protocol="s3",
#     _filesystem_bucket=_s3_filesystem_bucket_external,
#     _filesystem_external_id="123-abc",
#     _partition="partition",
#     _directory=None,
#     _file_name=None,
# )
# Malformed url for the S3 case
# _case_unique_id_with_dir: S3FileUrl = S3FileUrl(
#     _filesystem_protocol="s3",
#     _filesystem_bucket=_s3_filesystem_bucket_external,
#     _filesystem_external_id="123-abc",
#     _partition="partition",
#     _directory="dir",
#     _file_name=None,
# )
_case_unique_id_with_dir_and_file_name: S3FileUrl = S3FileUrl(
    _filesystem_protocol="s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)
_case_unique_id_with_file_name: S3FileUrl = S3FileUrl(
    _filesystem_protocol="s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory=None,
    _file_name="f.txt",
)
_case_unique_id_with_dir_and_file_name_encrypted: S3FileUrl = S3FileUrl(
    _filesystem_protocol="enc://s3",
    _filesystem_bucket=_s3_filesystem_bucket_external,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "s3://external/partition/dir"),
        (_case_dir_with_subdir, "s3://external/partition/dir/subdir"),
        (_case_file_name_only, "s3://external/partition/f.txt"),
        (_case_file_name_with_dir, "s3://external/partition/dir/f.txt"),
        (_case_unique_id_with_dir_and_file_name, "s3://external/partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "s3://external/partition/@123-abc$f.txt"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "enc://s3://external/partition/dir/@123-abc$f.txt",
        ),
    ],
)
def test_s3_file_url_str(file_url: FileUrl, expected_str: str):
    assert str(file_url) == expected_str


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "s3://fs_s3_test/partition/dir"),
        (_case_dir_with_subdir, "s3://fs_s3_test/partition/dir/subdir"),
        (_case_file_name_only, "s3://fs_s3_test/partition/f.txt"),
        (_case_file_name_with_dir, "s3://fs_s3_test/partition/dir/f.txt"),
        (_case_unique_id_with_dir_and_file_name, "s3://fs_s3_test/partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "s3://fs_s3_test/partition/@123-abc$f.txt"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "s3://fs_s3_test/partition/dir/@123-abc$f.txt",
        ),
    ],
)
def test_s3_file_url_str_internal(file_url: FileUrl, expected_str: str):
    assert file_url.as_str_internal() == expected_str


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("external/partition/dir", _case_dir_only),
        ("external/partition/dir/subdir", _case_dir_with_subdir),
        ("external/partition/f.txt", _case_file_name_only),
        ("external/partition/dir/f.txt", _case_file_name_with_dir),
        ("external/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("external/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
    ],
)
def test_s3_file_url_split_path(path: str, expected_file_url: FileUrl):
    file_url = S3FileUrl.split_path(path, protocol="s3", bucket=_s3_filesystem_bucket_external)
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("fs_s3_test/partition/dir", _case_dir_only),
        ("fs_s3_test/partition/dir/subdir", _case_dir_with_subdir),
        ("fs_s3_test/partition/f.txt", _case_file_name_only),
        ("fs_s3_test/partition/dir/f.txt", _case_file_name_with_dir),
        ("fs_s3_test/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("fs_s3_test/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
    ],
)
def test_s3_file_url_split_path_unobfuscated(path: str, expected_file_url: FileUrl):
    file_url = S3FileUrl.split_path(path, protocol="s3", bucket=_s3_filesystem_bucket_external)
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "url, expected_file_url",
    [
        ("s3://external/partition/dir", _case_dir_only),
        ("s3://external/partition/dir/subdir", _case_dir_with_subdir),
        ("s3://external/partition/f.txt", _case_file_name_only),
        ("s3://external/partition/dir/f.txt", _case_file_name_with_dir),
        ("s3://external/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("s3://external/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
        (
            "enc://s3://external/partition/dir/@123-abc$f.txt",
            _case_unique_id_with_dir_and_file_name_encrypted,
        ),
    ],
)
def test_s3_file_url_split_url(url: str, expected_file_url: FileUrl):
    file_url = S3FileUrl.split_url(url, bucket=_s3_filesystem_bucket_external)
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "file_url, expected_key_prefix",
    [
        (_case_dir_only, "partition/dir"),
        (_case_dir_with_subdir, "partition/dir/subdir"),
        (_case_file_name_only, "partition/f.txt"),
        (_case_file_name_with_dir, "partition/dir/f.txt"),
        (_case_unique_id_with_dir_and_file_name, "partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "partition/@123-abc$f.txt"),
    ],
)
def test_s3_file_url_key_prefix(file_url: S3FileUrl, expected_key_prefix: str):
    assert file_url.key_prefix == expected_key_prefix


@pytest.mark.parametrize(
    "file_url, expected_key_prefix_parent",
    [
        (_case_dir_only, "partition"),
        (_case_dir_with_subdir, "partition/dir"),
        (_case_file_name_only, "partition"),
        (_case_file_name_with_dir, "partition/dir"),
        (_case_unique_id_with_dir_and_file_name, "partition/dir"),
        (_case_unique_id_with_file_name, "partition"),
    ],
)
def test_s3_file_url_key_prefix_parent(file_url: S3FileUrl, expected_key_prefix_parent: str):
    assert file_url.key_prefix_parent == expected_key_prefix_parent


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_dir_only),
        (_case_dir_with_subdir),
    ],
)
def test_s3_file_url_is_directory(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is True
    assert file_url.is_file is False


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_file_name_only),
        (_case_file_name_with_dir),
        (_case_unique_id_with_dir_and_file_name),
        (_case_unique_id_with_file_name),
    ],
)
def test_s3_file_url_is_file(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is False
    assert file_url.is_file is True


@pytest.mark.parametrize(
    "file_url, join_dir, join_file_name, expected_joined_path",
    [
        (_case_dir_only, None, None, "s3://fs_s3_test/partition/dir"),
        (_case_dir_only, "join_dir", None, "s3://fs_s3_test/partition/dir/join_dir"),
        (_case_dir_only, None, "join_f.txt", "s3://fs_s3_test/partition/dir/join_f.txt"),
        (
            _case_dir_only,
            "join_dir",
            "join_f.txt",
            "s3://fs_s3_test/partition/dir/join_dir/join_f.txt",
        ),
    ],
)
def test_s3_file_url_join(
    file_url: S3FileUrl,
    join_dir: str | None,
    join_file_name: str | None,
    expected_joined_path: str,
):
    joined_file_url = file_url.join(directory=join_dir, file_name=join_file_name)
    assert joined_file_url.as_str_internal() == expected_joined_path


@pytest.mark.parametrize(
    "file_url, expected_parent_path",
    [
        (_case_dir_only, "s3://fs_s3_test/partition"),
        (_case_dir_with_subdir, "s3://fs_s3_test/partition/dir"),
        (_case_unique_id_with_dir_and_file_name, "s3://fs_s3_test/partition/dir"),
        (_case_unique_id_with_file_name, "s3://fs_s3_test/partition"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "s3://fs_s3_test/partition/dir",
        ),
    ],
)
def test_s3_file_url_parent(file_url: S3FileUrl, expected_parent_path: str):
    parent_file_url = file_url.parent()
    assert parent_file_url.as_str_internal() == expected_parent_path
