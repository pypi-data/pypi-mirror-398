import uuid
from pathlib import Path
from typing import Any

import boto3
from anyio.to_thread import run_sync
from botocore.exceptions import ClientError as BotoClientError
from fastapi_lifespan_manager import LifespanManager
from fsspec import AbstractFileSystem, register_implementation
from mypy_boto3_s3 import S3Client
from pydantic import Field
from s3fs import S3FileSystem as NativeS3FileSystem

from apppy.env import Env, EnvSettings
from apppy.fs import (
    FileSystem,
    FileSystemBucket,
    FileSystemPermission,
    FileUrl,
    GenericFileUrl,
    ProxyFileSystem,
)
from apppy.fs.errors import (
    FileSystemInvalidProtocolError,
    MalformedFileUrlError,
)
from apppy.generic.encrypt import BytesEncrypter
from apppy.logger import WithLogger


class S3FileUrl(GenericFileUrl):
    def __init__(
        self,
        _filesystem_protocol: str,
        _filesystem_bucket: FileSystemBucket,
        _filesystem_external_id: str | None,
        _partition: str,
        _directory: str | None,
        _file_name: str | None,
    ) -> None:
        super().__init__(
            _filesystem_protocol=_filesystem_protocol,
            _filesystem_bucket=_filesystem_bucket,
            _filesystem_external_id=_filesystem_external_id,
            _partition=_partition,
            _directory=_directory,
            _file_name=_file_name,
        )
        str_instance = self.as_str_internal()

        # Validation
        if _filesystem_protocol != "enc://s3" and _filesystem_protocol != "s3":
            raise FileSystemInvalidProtocolError(protocol=_filesystem_protocol)
        # If we have an id, we must also have a file name
        if _filesystem_external_id is not None and _file_name is None:
            raise MalformedFileUrlError(
                url=str_instance, code="s3_file_url_external_id_without_file_name"
            )

        self._key_prefix = str_instance[
            len(f"{self.filesystem_protocol}://{_filesystem_bucket.value}") + 1 :
        ]
        self._key_prefix_parent = str(Path(self.key_prefix).parent)

    @property
    def key_prefix(self) -> str:
        return self._key_prefix

    @property
    def key_prefix_parent(self) -> str:
        return self._key_prefix_parent

    @staticmethod
    def split_path(path: str, protocol: str, bucket: FileSystemBucket) -> "S3FileUrl":
        generic_file_url = GenericFileUrl.split_path(path=path, protocol=protocol, bucket=bucket)

        return S3FileUrl(
            _filesystem_protocol=generic_file_url.filesystem_protocol,
            _filesystem_bucket=bucket,
            _filesystem_external_id=generic_file_url.filesystem_external_id,
            _partition=generic_file_url.partition,
            _directory=generic_file_url.directory,
            _file_name=generic_file_url.file_name,
        )

    @staticmethod
    def split_url(url: str, bucket: FileSystemBucket) -> "S3FileUrl":
        url = url.strip()
        protocol = GenericFileUrl._parse_protocol(url, unencrypted=False)
        path = url[len(f"{protocol}://") :]

        return S3FileUrl.split_path(path=path, protocol=protocol, bucket=bucket)


class S3FileSystemSettings(EnvSettings):
    # S3_FS_BUCKET_EXTERNAL
    bucket_external: str = Field()
    # S3_FS_BUCKET_INTERNAL
    bucket_internal: str = Field()
    # S3_FS_REGION
    region: str = Field()
    # S3_FS_ENDPOINT
    # Used for non-AWS S3 compatible systems
    endpoint: str | None = Field(default=None)
    # S3_FS_USE_SSL
    use_ssl: bool = Field(default=True)
    # S3_FS_VERSION_AWARE
    version_aware: bool = Field(default=False)
    # S3_FS_ACCESS_KEY_ID
    # NOTE - In production environments, this may be skipped
    # in favor of an injected role credentials
    access_key_id: str | None = Field(default=None)
    # S3_FS_SECRET_ACCESS_KEY
    # NOTE - In production environments, this may be skipped
    # in favor of an injected role credentials
    secret_access_key: str | None = Field(default=None, exclude=True)
    # S3_FS_ENCRYPT_PASSPHRASE
    encrypt_passphrase: str | None = Field(default=None, exclude=True)
    # S3_FS_ENCRYPT_SALT
    encrypt_salt: str | None = Field(default=None, exclude=True)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="S3_FS")


class S3FileSystem(ProxyFileSystem, WithLogger):
    def __init__(
        self,
        settings: S3FileSystemSettings,
        lifespan: LifespanManager,
        fs: FileSystem,
    ) -> None:
        self._settings: S3FileSystemSettings = settings

        self._bytes_encrypter: BytesEncrypter | None = None
        if (
            settings.encrypt_passphrase is not None
            and len(settings.encrypt_passphrase) > 0
            and settings.encrypt_salt is not None
            and len(settings.encrypt_salt) > 0
        ):
            self._bytes_encrypter = BytesEncrypter(
                settings.encrypt_passphrase, settings.encrypt_salt
            )

        self._configure_nativefs(settings, fs)
        lifespan.add(self.__configure_s3_storage)

    def _configure_nativefs(
        self,
        settings: S3FileSystemSettings,
        fs: FileSystem,
    ) -> None:
        # Use generic test buckets for all tests
        self._bucket_external = FileSystemBucket(
            bucket_type="external",
            value=settings.bucket_external,
        )
        self._bucket_internal = FileSystemBucket(
            bucket_type="internal",
            value=settings.bucket_internal,
        )

        self._nativefs: NativeS3FileSystem = NativeS3FileSystem(
            endpoint_url=settings.endpoint,
            key=settings.access_key_id,
            secret=settings.secret_access_key,
            version_aware=settings.version_aware,
            use_ssl=settings.use_ssl,
        )
        fs.register_proxyfs(self, "s3")
        fs.register_nativefs(self._nativefs, "s3")

        if self.is_encrypted:
            # In the encrypted case, we'll need to also register the file
            # system with fsspec itself so that the encrypted filesystem
            # can instantiate it independently
            register_implementation("sb", NativeS3FileSystem, clobber=True)

    async def __configure_s3_storage(self):
        if not self._settings.access_key_id or not self._settings.secret_access_key:
            self._logger.info("Skipping setup for S3 buckets (assuming this is done via 3rd party)")
        else:
            self._logger.info("Creating S3 boto3 client for S3 filesystem bucket management")
            s3: S3Client = boto3.client(
                "s3",
                region_name=self._settings.region,
                endpoint_url=self._settings.endpoint,
                aws_access_key_id=self._settings.access_key_id,
                aws_secret_access_key=self._settings.secret_access_key,
                use_ssl=self._settings.use_ssl,
            )
            try:
                for bucket in (self._bucket_external, self._bucket_internal):
                    await run_sync(self.__ensure_s3_bucket, s3, bucket.value)
            finally:
                self._logger.info("Closing S3 boto3 client for S3 filesystem bucket management")
                s3.close()

        yield

        self._logger.info("Closing S3 filesystem clients")

    def __ensure_s3_bucket(self, s3: S3Client, bucket_name: str):
        try:
            s3.head_bucket(Bucket=bucket_name)
            self._logger.info("Found bucket for S3 filesystem", extra={"bucket": bucket_name})
        except BotoClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                self._logger.info("Bucket missing for S3 filesystem", extra={"bucket": bucket_name})
                if self._settings.region == "us-east-1":
                    s3.create_bucket(Bucket=bucket_name)
                else:
                    s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self._settings.region},  # type: ignore[typeddict-item]
                    )
                self._logger.info(
                    "Created new bucket for S3 filesystem",
                    extra={"bucket": bucket_name},
                )
            elif error_code == "403":
                self._logger.warning(
                    "Bucket access is forbidden while bootstrapping S3 filesystem",
                    extra={"bucket": bucket_name},
                )
            else:
                raise

    def convert_file_url(self, file_url: FileUrl) -> FileUrl:
        if isinstance(file_url, S3FileUrl) and self.is_encrypted == file_url.is_encrypted:
            return file_url

        if self.is_encrypted is True and file_url.is_encrypted is False:
            # Add the encyption protocol if we need to
            filesystem_protocol = f"enc://{file_url.filesystem_protocol}"
        else:
            filesystem_protocol = file_url.filesystem_protocol

        # If we're not version aware, ensure that we have a unique id associated
        # with the file_url. Unfortunately, it's not possible to get the actual
        # unique identiter out of S3 storage so we'll just make one up here and
        # pass it along
        filesystem_external_id: str | None = (
            str(uuid.uuid4())
            if file_url.filesystem_external_id is None
            and file_url.file_name is not None
            and self._settings.version_aware is False
            else file_url.filesystem_external_id
        )
        return S3FileUrl(
            _filesystem_protocol=filesystem_protocol,
            _filesystem_bucket=(
                self._bucket_external
                if file_url.filesystem_bucket.is_external
                else self._bucket_internal
            ),
            _filesystem_external_id=filesystem_external_id,
            _partition=file_url.partition,
            _directory=file_url.directory,
            _file_name=file_url.file_name,
        )

    def file_url_kwargs(self, file_url: FileUrl) -> dict[str, Any]:
        # No extra parameters needed
        return {}

    def parse_file_url(self, url: str) -> S3FileUrl:
        if url.find(self._bucket_internal.value) > -1:
            return S3FileUrl.split_url(url, self._bucket_internal)

        return S3FileUrl.split_url(url, self._bucket_external)

    def rm(self, url: str, recursive=False, maxdepth=None, **kwargs) -> None:
        self.native.rm(url, recursive=recursive, maxdepth=maxdepth)

    @property
    def encryption(self) -> BytesEncrypter | None:
        return self._bytes_encrypter

    @property
    def name(self) -> str:
        return "AWS S3"

    @property
    def native(self) -> AbstractFileSystem:
        return self._nativefs

    @property
    def permissions(self) -> list[FileSystemPermission]:
        return [
            FileSystemPermission.PRIVATE_INTERNAL,
            FileSystemPermission.READWRITE,
        ]
