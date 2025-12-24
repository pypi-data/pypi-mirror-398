import pytest_asyncio
from fastapi_lifespan_manager import LifespanManager

from apppy.aws.fs import S3FileSystem, S3FileSystemSettings
from apppy.env import Env
from apppy.env.fixtures import current_test_name
from apppy.fs import FileSystem, FileSystemSettings, FileUrl


@pytest_asyncio.fixture(scope="session")
async def s3_fs():
    fs_env: Env = Env.load(name=current_test_name())
    fs_settings = FileSystemSettings(fs_env)
    fs = FileSystem(fs_settings)

    fs_s3_settings = S3FileSystemSettings(fs_env)
    lifespan = LifespanManager()
    fs_s3 = S3FileSystem(fs_s3_settings, lifespan, fs)

    dummy_app = object()
    async with lifespan(dummy_app) as state:
        _ = fs_s3, state
        yield fs


@pytest_asyncio.fixture(scope="session")
async def s3_fs_encrypted():
    fs_env: Env = Env.load(
        name=current_test_name(),
        overrides={
            "encrypt_passphrase": "my-s3-fs-passphrase",
            "encrypt_salt": "some-salt",
        },
    )
    fs_settings = FileSystemSettings(fs_env)
    fs = FileSystem(fs_settings)

    fs_s3_settings = S3FileSystemSettings(fs_env)
    lifespan = LifespanManager()
    fs_s3 = S3FileSystem(fs_s3_settings, lifespan, fs)

    dummy_app = object()
    async with lifespan(dummy_app) as state:
        _ = fs_s3, state
        yield fs


@pytest_asyncio.fixture(scope="session")
async def s3_fs_version_aware():
    fs_env: Env = Env.load(
        name=current_test_name(),
        overrides={
            "version_aware": True,
        },
    )
    fs_settings = FileSystemSettings(fs_env)
    fs = FileSystem(fs_settings)

    fs_s3_settings = S3FileSystemSettings(fs_env)
    lifespan = LifespanManager()
    fs_s3 = S3FileSystem(fs_s3_settings, lifespan, fs)

    dummy_app = object()
    async with lifespan(dummy_app) as state:
        _ = fs_s3, state
        yield fs


@pytest_asyncio.fixture
async def s3_file_write(s3_fs: FileSystem):
    async def _file_url_from_file_write(partition: str, directory: str) -> FileUrl:
        file_url: FileUrl = s3_fs.new_file_url_external(
            protocol="s3",
            external_id=None,
            partition=partition,
            directory=directory,
            file_name="file.txt",
        )

        file_url, _ = await s3_fs.write_text(
            file_url, "The quick brown fox jumped over the lazy dogs."
        )
        return file_url

    return _file_url_from_file_write


@pytest_asyncio.fixture
async def s3_file_write_encrypted(s3_fs_encrypted: FileSystem):
    async def _file_url_from_file_write(partition: str, directory: str) -> FileUrl:
        file_url: FileUrl = s3_fs_encrypted.new_file_url_external(
            protocol="s3",
            external_id=None,
            partition=partition,
            directory=directory,
            file_name="file.txt",
        )

        file_url, _ = await s3_fs_encrypted.write_text(
            file_url, "The quick brown fox jumped over the lazy dogs."
        )
        return file_url

    return _file_url_from_file_write
