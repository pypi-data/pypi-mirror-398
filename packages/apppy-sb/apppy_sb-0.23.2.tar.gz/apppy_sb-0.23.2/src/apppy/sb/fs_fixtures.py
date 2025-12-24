import pytest_asyncio
from fastapi_lifespan_manager import LifespanManager

from apppy.env import Env
from apppy.env.fixtures import current_test_name
from apppy.fs import FileSystem, FileSystemSettings, FileUrl
from apppy.sb.fs import SupabaseFileSystem, SupabaseFileSystemSettings


@pytest_asyncio.fixture(scope="session")
async def sb_fs():
    fs_env: Env = Env.load(name=current_test_name())
    fs_settings = FileSystemSettings(fs_env)
    fs = FileSystem(fs_settings)

    fs_sb_settings = SupabaseFileSystemSettings(fs_env)
    lifespan = LifespanManager()
    fs_sb = SupabaseFileSystem(fs_env, fs_sb_settings, lifespan, fs)

    dummy_app = object()
    async with lifespan(dummy_app) as state:
        _ = fs_sb, state
        yield fs


@pytest_asyncio.fixture(scope="session")
async def sb_fs_encrypted():
    fs_env: Env = Env.load(
        name=current_test_name(),
        overrides={
            "encrypt_passphrase": "my-sb-fs-passphrase",
            "encrypt_salt": "some-salt",
        },
    )
    fs_settings = FileSystemSettings(fs_env)
    fs = FileSystem(fs_settings)

    fs_sb_settings = SupabaseFileSystemSettings(fs_env)
    lifespan = LifespanManager()
    fs_sb = SupabaseFileSystem(fs_env, fs_sb_settings, lifespan, fs)

    dummy_app = object()
    async with lifespan(dummy_app) as state:
        _ = fs_sb, state
        yield fs


@pytest_asyncio.fixture
async def sb_file_write(sb_fs: FileSystem):
    async def _file_url_from_file_write(partition: str, directory: str) -> FileUrl:
        file_url: FileUrl = sb_fs.new_file_url_external(
            protocol="sb",
            external_id=None,
            partition=partition,
            directory=directory,
            file_name="file.txt",
        )

        file_url, _ = await sb_fs.write_text(
            file_url, "The quick brown fox jumped over the lazy dogs."
        )
        return file_url

    return _file_url_from_file_write


@pytest_asyncio.fixture
async def sb_file_write_encrypted(sb_fs_encrypted: FileSystem):
    async def _file_url_from_file_write(partition: str, directory: str) -> FileUrl:
        file_url: FileUrl = sb_fs_encrypted.new_file_url_external(
            protocol="sb",
            external_id=None,
            partition=partition,
            directory=directory,
            file_name="file.txt",
        )

        file_url, _ = await sb_fs_encrypted.write_text(
            file_url, "The quick brown fox jumped over the lazy dogs."
        )
        return file_url

    return _file_url_from_file_write
