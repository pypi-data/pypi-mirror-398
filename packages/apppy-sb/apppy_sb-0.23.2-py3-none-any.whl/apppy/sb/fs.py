import datetime
import io
import time
import uuid
from pathlib import Path
from typing import Any

import tusclient
import tusclient.client
import tusclient.uploader
from fastapi_lifespan_manager import LifespanManager
from fsspec import register_implementation
from fsspec.spec import AbstractBufferedFile, AbstractFileSystem
from pydantic import Field
from storage3.types import CreateOrUpdateBucketOptions
from supabase.client import (
    AsyncClient as NativeSupabaseAsyncClient,
)
from supabase.client import (
    AsyncSupabaseStorageClient as NativeSupabaseStorageAsyncClient,
)
from supabase.client import (
    Client as NativeSupabaseClient,
)
from supabase.client import (
    SupabaseStorageClient as NativeSupabaseStorageClient,
)
from supabase.client import (
    create_async_client,
    create_client,
)

from apppy.env import Env, EnvSettings
from apppy.fs import (
    FileSystem,
    FileSystemBucket,
    FileSystemPermission,
    FileUrl,
    GenericFileUrl,
    ProxyFileSystem,
)
from apppy.fs.errors import FileSystemInvalidProtocolError, MalformedFileUrlError
from apppy.generic.encrypt import BytesEncrypter
from apppy.logger import WithLogger


class SupabaseFileUrl(GenericFileUrl):
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
        if _filesystem_protocol != "enc://sb" and _filesystem_protocol != "sb":
            raise FileSystemInvalidProtocolError(protocol=_filesystem_protocol)
        # The id and file name must either both be None or not None
        if _filesystem_external_id is None and _file_name is not None:
            raise MalformedFileUrlError(
                url=str_instance, code="supabase_file_url_file_name_without_external_id"
            )
        elif _filesystem_external_id is not None and _file_name is None:
            raise MalformedFileUrlError(
                url=str_instance, code="supabase_file_url_external_id_without_file_name"
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
    def split_path(path: str, protocol: str, bucket: FileSystemBucket) -> "SupabaseFileUrl":
        generic_file_url = GenericFileUrl.split_path(path=path, protocol=protocol, bucket=bucket)

        return SupabaseFileUrl(
            _filesystem_protocol=generic_file_url.filesystem_protocol,
            _filesystem_bucket=bucket,
            _filesystem_external_id=generic_file_url.filesystem_external_id,
            _partition=generic_file_url.partition,
            _directory=generic_file_url.directory,
            _file_name=generic_file_url.file_name,
        )

    @staticmethod
    def split_url(url: str, bucket: FileSystemBucket) -> "SupabaseFileUrl":
        url = url.strip()
        protocol = GenericFileUrl._parse_protocol(url, unencrypted=False)
        path = url[len(f"{protocol}://") :]

        return SupabaseFileUrl.split_path(path=path, protocol=protocol, bucket=bucket)


DEFAULT_BLOCK_SIZE = 6 * 1024 * 1024
SYNTHETIC_FILE_SIZE = 2**63 - 1


class SupabaseFile(AbstractBufferedFile):
    def __init__(
        self,
        fs,
        path,
        mode="rb",
        block_size=DEFAULT_BLOCK_SIZE,
        autocommit=True,
        cache_type="readahead",
        cache_options=None,
        size=None,
        **kwargs,
    ):
        super().__init__(
            fs=fs,
            path=path,
            mode=mode,
            block_size=block_size,
            autocommit=autocommit,
            cache_type=cache_type,
            cache_options=cache_options,
            # The AbstractBufferedFile base constructor will attempt to lookup
            # the file size if one is not provided. It's been observed that there's
            # a race condition here because Supabase needs some time to index the
            # new file. So if the caller is not providing a size, we'll attach a
            # synthetic size value to delay the file size lookup.
            size=(size or SYNTHETIC_FILE_SIZE),
            **kwargs,
        )
        self.sb_url: SupabaseFileUrl = SupabaseFileUrl.split_path(
            path=path, protocol=fs.protocol, bucket=kwargs["filesystem_bucket"]
        )

        self._tus_client: tusclient.client.TusClient | None = None
        self._tus_uploader: tusclient.uploader.Uploader | None = None

    @property
    def __tus_uploader(self) -> tusclient.uploader.Uploader:
        if self._tus_uploader is None:
            raise Exception("tus_uploader is uninitialized")

        return self._tus_uploader

    def commit(self):
        """Move from temp to final destination"""
        self._upload_chunk(final=True)

    @property
    def details(self):
        if self._details is None:  # type: ignore[has-type]
            self._details = self._fetch_details_with_retry()
            # See constructor comments about synthetic file size
            # If we encounter this and have a real file size available
            # update the file details to use the real size.
            if self.size == SYNTHETIC_FILE_SIZE:
                real_size = self._details.get("size")
                if isinstance(real_size, int) and real_size >= 0:
                    self.size = real_size
                    # Update any cache value too just in case
                    if hasattr(self, "cache") and hasattr(self.cache, "size"):
                        self.cache.size = real_size

        return self._details

    def discard(self):
        """Throw away temporary file"""

    def _fetch_details_with_retry(self, attempts=8, base_sleep=0.05):
        """
        Attempt to retrieve file details with a linear backoff.

        Supabase takes some time in order to index files so there's a brief
        period in which a file may exist but its information cannot be retrieved.
        """
        last_exc: FileNotFoundError | None = None
        for i in range(attempts):
            try:
                return self.fs.info(self.path, **self.kwargs)
            except FileNotFoundError as e:
                last_exc = e
                time.sleep(base_sleep * (i + 1))
        # If still not visible, surface the error only when metadata is required
        raise last_exc  # type: ignore[invalid-raise]

    def _fetch_range(self, start, end):
        """Get the specified set of bytes from remote"""
        downloaded_bytes = (
            self.fs.storage_client()
            .from_(self.sb_url.filesystem_bucket.value)
            .download(self.sb_url.key_prefix)
        )

        file_like = io.BytesIO(downloaded_bytes)
        size = len(downloaded_bytes)

        # Handle start
        if start is not None:
            if start >= 0:
                file_like.seek(start)
            else:
                file_like.seek(max(0, size + start))
        else:
            file_like.seek(0)

        # Handle end
        if end is not None:
            if end < 0:
                end = size + end
            return file_like.read(end - file_like.tell())

        return file_like.read()

    def _initiate_upload(self):
        """Create remote file/upload"""
        self._tus_client = tusclient.client.TusClient(
            f"{self.fs._settings.api_url}/storage/v1/upload/resumable",
            headers={"Authorization": f"Bearer {self.fs._settings.api_key}", "x-upsert": "true"},
        )
        self._tus_uploader = self._tus_client.uploader(
            file_stream=self.buffer,
            chunk_size=self.blocksize,
            metadata={
                "bucketName": self.sb_url.filesystem_bucket.value,
                "objectName": self.sb_url.key_prefix,
                "contentType": "application/octet-stream",
                "cacheControl": "3600",
            },
        )

    def _upload_chunk(self, final=False):
        """Write one part of a multi-block file upload

        Parameters
        ==========
        final: bool
            This is the last block, so should complete file, if
            self.autocommit is True.
        """
        self.__tus_uploader.upload_chunk()
        if final:
            # There's no apparent close function for these
            # so just set them to None to signal that we
            # should not expect to continue with any more
            # uploading
            self._tus_client = None
            self._tus_uploader = None


class SupabaseFileSystemSettings(EnvSettings):
    # SUPABASE_FS_BUCKET_EXTERNAL
    bucket_external: str = Field()
    # SUPABASE_FS_BUCKET_INTERNAL
    bucket_internal: str = Field()
    # SUPABASE_FS_API_KEY
    api_key: str = Field(exclude=True)
    # SUPABASE_FS_API_URL
    api_url: str = Field()
    # SUPABASE_FS_ENCRYPT_PASSPHRASE
    encrypt_passphrase: str | None = Field(default=None, exclude=True)
    # SUPABASE_FS_ENCRYPT_SALT
    encrypt_salt: str | None = Field(default=None, exclude=True)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="SUPABASE_FS")


class NativeSupabaseFileSystem(AbstractFileSystem, WithLogger):
    """
    A fsspec plugin that works with Supabase. In most other cases,
    we are able to leverage plugins that ship with fsspec itself.

    However, in this case, there is no native Supabase plugin so
    we need to write this one.
    """

    protocol = "sb"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        storage_options = kwargs["storage_options"]

        self._settings: SupabaseFileSystemSettings = storage_options["settings"]

        self._fs_bucket_names: list[str] = storage_options["fs_bucket_names"]
        self._native_storage_client_async: NativeSupabaseStorageAsyncClient | None = None
        lifespan: LifespanManager = storage_options["lifespan"]
        lifespan.add(self.__configure_supabase_storage)

    ##### ##### ##### Configuration and Registration ##### ##### #####

    async def __configure_supabase_storage(self):
        native_client_async: NativeSupabaseAsyncClient = await create_async_client(
            supabase_url=self._settings.api_url, supabase_key=self._settings.api_key
        )

        self._native_storage_client_async = native_client_async.storage

        # Ensure that all buckets used by this FileSystem
        # are created
        all_buckets = await self.list_buckets()
        fs_buckets = []  # Buckets used by this FileSystem
        for fs_bucket_name in self._fs_bucket_names:
            fs_bucket = next(
                (bucket for bucket in all_buckets if bucket.name == fs_bucket_name), None
            )
            if fs_bucket is None:
                fs_bucket = await self.create_bucket(
                    id=fs_bucket_name,
                    options=CreateOrUpdateBucketOptions(public=False),
                )

            fs_buckets.append(fs_bucket)

        yield {
            "native_storage_client_async": self._native_storage_client_async,
            "fs_buckets": fs_buckets,
        }

        self._logger.info("Closing Supabase storage clients")
        await self._native_storage_client_async.aclose()

    def storage_client(self) -> NativeSupabaseStorageClient:
        # This allows us to create a client for every file system
        # interation. This is super safe as we'll guarantee that
        # the client is never closed. But might we leak clients here?
        # TODO: Is this OK to do?
        native_client: NativeSupabaseClient = create_client(
            supabase_url=self._settings.api_url,
            supabase_key=self._settings.api_key,
        )
        return native_client.storage

    ##### ##### ##### Bucket Management ##### ##### #####

    @property
    def __native_storage_client_async(self) -> NativeSupabaseStorageAsyncClient:
        if self._native_storage_client_async is None:
            raise Exception("native_storage_client_async is uninitialied")

        return self._native_storage_client_async

    async def create_bucket(
        self, id: str, name: str | None = None, options: CreateOrUpdateBucketOptions | None = None
    ) -> dict[str, str]:
        return await self.__native_storage_client_async.create_bucket(
            id=id, name=name, options=options
        )

    async def get_bucket(self, id: str):
        return await self.__native_storage_client_async.get_bucket(id=id)

    async def list_buckets(self):
        return await self.__native_storage_client_async.list_buckets()

    ##### ##### ##### FileSystem Implementation ##### ##### #####

    @property
    def fsid(self):
        return "supabase"

    def created(self, path):
        """Return the created timestamp of a file as a datetime.datetime"""
        path_info = self.info(path)
        created_dt = datetime.datetime.fromisoformat(path_info["created"])
        return created_dt

    def cp_file(self, path1, path2, **kwargs):
        sb_file_url1: SupabaseFileUrl = SupabaseFileUrl.split_path(
            path=path1, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )
        sb_file_url2: SupabaseFileUrl = SupabaseFileUrl.split_path(
            path=path2, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )
        # Ensure that we're only copying within the same bucket
        # Copying between buckets is not allowed
        assert sb_file_url1.filesystem_bucket.value == sb_file_url2.filesystem_bucket.value

        self.storage_client().from_(sb_file_url1.filesystem_bucket.value).copy(
            from_path=sb_file_url1.key_prefix,
            to_path=sb_file_url2.key_prefix,
        )

    def info(self, path, **kwargs):
        # For Supabase, treat info just as a straight
        # alias for ls
        path = self._strip_protocol(path)
        sb_file_url = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )
        if sb_file_url.is_file is False:
            if sb_file_url.key_prefix is None:  # The path cannot be parsed
                raise FileNotFoundError

            # Supabase does not really have the concept of
            # directories so we'll fake some data here and
            # just return it. Note that this may create upstream
            # consequences. For example, directories will always
            # be seen as existing when the key prefix is in use or not.
            return {
                "name": Path(sb_file_url.key_prefix).name,
                "size": None,
                "type": "directory",
                "url": path,
            }

        resp = self.ls(path, detail=True, **kwargs)
        if len(resp) == 0:
            raise FileNotFoundError

        return resp[0]

    def isdir(self, path, **kwargs):
        path = self._strip_protocol(path)
        sb_file_url = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )

        return sb_file_url.is_directory

    def isfile(self, path, **kwargs):
        path = self._strip_protocol(path)
        sb_file_url = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )

        return sb_file_url.is_file

    def ls(self, path, detail=True, **kwargs):
        """List objects at path.

        This should include subdirectories and files at that location. The
        difference between a file and a directory must be clear when details
        are requested.

        The specific keys, or perhaps a FileInfo class, or similar, is TBD,
        but must be consistent across implementations.
        Must include:

        - full path to the entry (without protocol)
        - size of the entry, in bytes. If the value cannot be determined, will
          be ``None``.
        - type of entry, "file", "directory" or other

        Additional information
        may be present, appropriate to the file-system, e.g., generation,
        checksum, etc.

        May use refresh=True|False to allow use of self._ls_from_cache to
        check for a saved listing and avoid calling the backend. This would be
        common where listing may be expensive.

        Parameters
        ----------
        path: str
        detail: bool
            if True, gives a list of dictionaries, where each is the same as
            the result of ``info(path)``. If False, gives a list of paths
            (str).
        kwargs: may have additional backend-specific options, such as version
            information

        Returns
        -------
        List of strings if detail is False, or list of directory information
        dicts if detail is True.
        """
        path = self._strip_protocol(path)
        sb_file_url = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )
        if sb_file_url.is_file:
            if sb_file_url.key_prefix is None:
                return []  # The path cannot be parsed

            # This is a bit of a hack. It's been observed
            # that we cannot run a list on a file's key prefix
            # So instead, we'll list the parent and filter here
            # for the file name
            resp_parent = (
                self.storage_client()
                .from_(sb_file_url.filesystem_bucket.value)
                .list(sb_file_url.key_prefix_parent)
            )
            resp = [r for r in resp_parent if sb_file_url.key_prefix.endswith(r["name"])]
        else:
            # CASE: Path is a directory
            resp = (
                self.storage_client()
                .from_(sb_file_url.filesystem_bucket.value)
                .list(sb_file_url.key_prefix)
            )

        ls_results = []
        for r in resp:
            ls_result = {
                "name": r["name"],
            }
            if self.isfile(path, **kwargs):
                ls_result["url"] = sb_file_url.as_str_internal()
            else:
                ls_result["url"] = (
                    f"sb://{sb_file_url.filesystem_bucket.value}/{sb_file_url.key_prefix}/{r['name']}"
                )

            if detail:
                ls_result["size"] = (
                    r["metadata"].get("size") if r.get("metadata") is not None else None
                )
                ls_result["type"] = "file"
                ls_result["created"] = r["created_at"]
                ls_result["modified"] = r["created_at"]
                ls_result["islink"] = False
                ls_result["mode"] = "ro"  # Readonly?
                ls_result["uid"] = r["id"]
                ls_result["gid"] = r["id"]

            ls_results.append(ls_result)

        return ls_results

    def lsdir(self, path, recursive=False, maxdepth=None, **kwargs):
        path = self._strip_protocol(path)

        ls_files = []
        current_depth = kwargs.get("current_depth", 0)
        if maxdepth is not None and current_depth > maxdepth:
            return ls_files

        sb_file_url: SupabaseFileUrl = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )

        if sb_file_url.is_file:
            ls_files.append({"name": sb_file_url.key_prefix, "url": sb_file_url.as_str_internal()})
            return ls_files

        ls_results = self.ls(path, detail=True, **kwargs)
        for ls_result in ls_results:
            ls_result_path = self._strip_protocol(ls_result["url"])
            ls_result_url: SupabaseFileUrl = SupabaseFileUrl.split_path(
                path=ls_result_path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
            )
            ls_files.append(
                {"name": ls_result_url.key_prefix, "url": ls_result_url.as_str_internal()}
            )
            if ls_result_url.is_directory and recursive is True:
                kwargs["current_depth"] = current_depth + 1
                ls_files.extend(
                    self.lsdir(
                        ls_result_path,
                        recursive=True,
                        maxdepth=maxdepth,
                        **kwargs,
                    )
                )

        return ls_files

    def mkdir(self, path, create_parents=True, **kwargs):
        """Create directory entry at path"""
        # Legitimately skip as Supabase storage
        # does not have directories
        pass

    def makedirs(self, path, exist_ok=False):
        """Recursively make directories"""
        # Legitimately skip as Supabase storage
        # does not have directories
        pass

    def modified(self, path):
        """Return the modified timestamp of a file as a datetime.datetime"""
        path_info = self.info(path)
        modified_dt = datetime.datetime.fromisoformat(path_info["modified"])
        return modified_dt

    def rmdir(self, path):
        """Remove a directory, if empty"""
        # Legitimately skip as Supabase storage
        # does not have directories
        pass

    def sign(self, path, expiration=(1 * 60 * 60), **kwargs):
        """
        Create a signed URL representing the given path

        Parameters
        ----------
        path : str
             The path on the filesystem
        expiration : int
            Number of seconds to enable the URL for (if supported)

        Returns
        -------
        URL : str
            The signed URL
        """
        path = self._strip_protocol(path)
        sb_file_url: SupabaseFileUrl = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )
        resp = (
            self.storage_client()
            .from_(sb_file_url.filesystem_bucket.value)
            .create_signed_url(
                path=sb_file_url.key_prefix,
                expires_in=expiration,
            )
        )

        return resp["signedURL"]

    def _open(
        self,
        path,
        mode="rb",
        block_size=None,
        autocommit=True,
        cache_options=None,
        **kwargs,
    ):
        """Return raw bytes-mode file-like from the file-system"""
        return SupabaseFile(
            fs=self,
            path=path,
            mode=mode,
            # block_size=block_size,
            autocommit=autocommit,
            cache_options=cache_options,
            **kwargs,
        )

    def _rm(self, path, recursive=False, maxdepth=None, **kwargs):
        path = self._strip_protocol(path)
        sb_file_url: SupabaseFileUrl = SupabaseFileUrl.split_path(
            path=path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
        )

        ls_dir_results = self.lsdir(path, recursive, maxdepth, **kwargs)
        key_prefixes = []
        for ls_result in ls_dir_results:
            ls_result_path = self._strip_protocol(ls_result["url"])
            ls_result_file_url = SupabaseFileUrl.split_path(
                path=ls_result_path, protocol=self.protocol, bucket=kwargs["filesystem_bucket"]
            )
            key_prefixes.append(ls_result_file_url.key_prefix)

        if len(key_prefixes) > 0:
            self.storage_client().from_(sb_file_url.filesystem_bucket.value).remove(key_prefixes)

    @classmethod
    def _strip_protocol(cls, path):
        # CASE: The protocol has already been stripped
        if path.find("://") == -1:
            return path

        protocol = FileUrl._parse_protocol(path, unencrypted=False)
        return path[len(protocol) + 3 :]


class SupabaseFileSystem(ProxyFileSystem, WithLogger):
    def __init__(
        self,
        env: Env,
        settings: SupabaseFileSystemSettings,
        lifespan: LifespanManager,
        fs: FileSystem,
    ) -> None:
        self._settings: SupabaseFileSystemSettings = settings

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

        self.__configure_nativefs(env, settings, lifespan, fs)

    def __configure_nativefs(
        self,
        env: Env,
        settings: SupabaseFileSystemSettings,
        lifespan: LifespanManager,
        fs: FileSystem,
    ) -> None:
        # Use generic test buckets for all tests
        bucket_external_value = (
            f"{settings.bucket_external}-test"
            if env.is_test or env.is_ci
            else settings.bucket_external
        )
        self._bucket_external = FileSystemBucket(
            bucket_type="external",
            value=bucket_external_value,
        )
        bucket_internal_value = (
            f"{settings.bucket_internal}-test"
            if env.is_test or env.is_ci
            else settings.bucket_internal
        )
        self._bucket_internal = FileSystemBucket(
            bucket_type="internal",
            value=bucket_internal_value,
        )
        fs.register_proxyfs(self, "sb")

        fs_bucket_names: list[str] = [
            self._bucket_external.value,
            self._bucket_internal.value,
        ]

        nativefs = NativeSupabaseFileSystem(
            storage_options={
                "fs_bucket_names": fs_bucket_names,
                "settings": settings,
                "lifespan": lifespan,
            }
        )
        self._nativefs: AbstractFileSystem = nativefs
        fs.register_nativefs(nativefs, "sb")

        if self.is_encrypted:
            # In the encrypted case, we'll need to also register the file
            # system with fsspec itself so that the encrypted filesystem
            # can instantiate it independently
            register_implementation("sb", NativeSupabaseFileSystem, clobber=True)

    def convert_file_url(self, file_url: FileUrl) -> FileUrl:
        if isinstance(file_url, SupabaseFileUrl) and self.is_encrypted == file_url.is_encrypted:
            return file_url

        if self.is_encrypted is True and file_url.is_encrypted is False:
            # Add the encyption protocol if we need to
            filesystem_protocol = f"enc://{file_url.filesystem_protocol}"
        else:
            filesystem_protocol = file_url.filesystem_protocol

        # Always ensure that we always have a unique id associated with the file_url.
        # Unfortunately, it's not possible to get the actual unique identiter out of
        # Supabase storage so we'll just make one up here and pass it along
        filesystem_external_id: str | None = None
        if file_url.file_name is not None:
            filesystem_external_id = (
                str(uuid.uuid4())
                if file_url.filesystem_external_id is None
                else file_url.filesystem_external_id
            )
        return SupabaseFileUrl(
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
        # The NativeSupabaseFileSystem relies on us providing
        # the filesystem_bucket as an extra parameter
        return {"filesystem_bucket": file_url.filesystem_bucket}

    def parse_file_url(self, url: str) -> SupabaseFileUrl:
        if url.find(self._bucket_internal.value) > -1:
            return SupabaseFileUrl.split_url(url, self._bucket_internal)

        return SupabaseFileUrl.split_url(url, self._bucket_external)

    def rm(self, url: str, recursive=False, maxdepth=None, **kwargs) -> None:
        self.native.rm(url, recursive=recursive, maxdepth=maxdepth, **kwargs)

    @property
    def encryption(self) -> BytesEncrypter | None:
        return self._bytes_encrypter

    @property
    def name(self) -> str:
        return "Supabase"

    @property
    def native(self) -> AbstractFileSystem:
        return self._nativefs

    @property
    def permissions(self) -> list[FileSystemPermission]:
        return [
            FileSystemPermission.PRIVATE_INTERNAL,
            FileSystemPermission.READWRITE,
        ]
