import pytest

from apppy.aws.fs import S3FileSystem
from apppy.aws.fs_fixtures import (  # noqa: F401
    s3_file_write,
    s3_file_write_encrypted,
    s3_fs,
    s3_fs_encrypted,
    s3_fs_version_aware,
)
from apppy.fs import FileSystem, FileUrl


def test_load_s3_proxyfs_by_protocol(s3_fs: FileSystem):  # noqa: F811
    _, proxyfs = s3_fs.load_proxyfs_by_protocol("s3")
    assert proxyfs is not None
    assert isinstance(proxyfs, S3FileSystem) is True


async def test_s3_write_bytes_unencrypted(
    s3_fs: FileSystem,  # noqa: F811
):
    file_url = s3_fs.new_file_url_external(
        protocol="s3",
        external_id=None,
        partition="fs_s3_test",
        directory="test_s3_write_bytes_unencrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is False

    await s3_fs.write_bytes(
        file_url, bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")
    )
    read_bytes = s3_fs.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_s3_write_bytes_encrypted(
    s3_fs_encrypted: FileSystem,  # noqa: F811
):
    file_url = s3_fs_encrypted.new_file_url_external(
        protocol="s3",
        external_id=None,
        partition="fs_s3_test",
        directory="test_s3_write_bytes_encrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is True

    await s3_fs_encrypted.write_bytes(
        file_url, bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")
    )
    read_bytes = s3_fs_encrypted.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_s3_write_text_unencrypted(
    s3_fs: FileSystem,  # noqa: F811
):
    file_url = s3_fs.new_file_url_external(
        protocol="s3",
        external_id=None,
        partition="fs_s3_test",
        directory="test_s3_write_text_unencrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is False

    await s3_fs.write_text(file_url, "The quick brown fox jumped over the lazy dogs.")
    read_bytes = s3_fs.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_s3_write_text_encrypted(
    s3_fs_encrypted: FileSystem,  # noqa: F811
):
    file_url = s3_fs_encrypted.new_file_url_external(
        protocol="s3",
        external_id=None,
        partition="fs_s3_test",
        directory="test_s3_write_text_encrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is True

    await s3_fs_encrypted.write_text(file_url, "The quick brown fox jumped over the lazy dogs.")
    read_bytes = s3_fs_encrypted.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_s3_write_bytes_versioned(
    s3_fs_version_aware: FileSystem,  # noqa: F811
):
    file_url = s3_fs_version_aware.new_file_url_external(
        protocol="s3",
        external_id=None,
        partition="fs_s3_test",
        directory="test_s3_write_bytes_versioned",
        file_name="file.txt",
    )

    # Assert that we have not created a unique id for this file.
    # That is, we'll be writing twice against the exact same url
    assert file_url.filesystem_external_id is None

    await s3_fs_version_aware.write_bytes(file_url, bytes("This is file version 1.", "utf-8"))
    await s3_fs_version_aware.write_bytes(file_url, bytes("This is file version 2.", "utf-8"))
    # Assert that when we read back the bytes, we get the second version
    read_bytes = s3_fs_version_aware.read_bytes(file_url)
    assert read_bytes == bytes("This is file version 2.", "utf-8")


@pytest.mark.parametrize(
    ("algo", "expected_checksum"),
    [
        (
            "md5",
            "5c9f966da28ab24ca7796006a6259494",
        ),
        (
            "sha256",
            "c9c85caa5a93aad2bfcc91b9a02d4185a0f0348aac049e650bd0f4dea10a7393",
        ),
    ],
)
async def test_s3_checksum_file_unencrypted(
    s3_fs: FileSystem,  # noqa: F811
    s3_file_write,  # noqa: F811
    algo,
    expected_checksum,
):
    file_url: FileUrl = await s3_file_write(
        partition="fs_s3_test", directory="test_s3_checksum_file"
    )
    assert file_url.is_encrypted is False

    checksum = s3_fs.checksum_file(file_url, algo=algo)
    assert checksum == expected_checksum


@pytest.mark.parametrize(
    ("algo", "expected_checksum"),
    [
        (
            "md5",
            "5c9f966da28ab24ca7796006a6259494",
        ),
        (
            "sha256",
            "c9c85caa5a93aad2bfcc91b9a02d4185a0f0348aac049e650bd0f4dea10a7393",
        ),
    ],
)
async def test_s3_checksum_file_encrypted(
    s3_fs_encrypted: FileSystem,  # noqa: F811
    s3_file_write_encrypted,  # noqa: F811
    algo,
    expected_checksum,
):
    file_url: FileUrl = await s3_file_write_encrypted(
        partition="fs_s3_test", directory="test_s3_checksum_file"
    )
    assert file_url.is_encrypted is True

    checksum = s3_fs_encrypted.checksum_file(file_url, algo=algo)
    assert checksum == expected_checksum
