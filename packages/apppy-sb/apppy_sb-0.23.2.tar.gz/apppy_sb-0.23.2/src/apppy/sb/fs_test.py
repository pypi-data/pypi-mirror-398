import pytest

from apppy.fs import FileSystem, FileUrl
from apppy.sb.fs import SupabaseFileSystem
from apppy.sb.fs_fixtures import (  # noqa: F401
    sb_file_write,
    sb_file_write_encrypted,
    sb_fs,
    sb_fs_encrypted,
)


def test_load_sb_proxyfs_by_protocol(sb_fs: FileSystem):  # noqa: F811
    _, proxyfs = sb_fs.load_proxyfs_by_protocol("sb")
    assert proxyfs is not None
    assert isinstance(proxyfs, SupabaseFileSystem) is True


async def test_sb_write_bytes_unencrypted(
    sb_fs: FileSystem,  # noqa: F811
):
    file_url = sb_fs.new_file_url_external(
        protocol="sb",
        external_id=None,
        partition="fs_sb_test",
        directory="test_sb_write_bytes_unencrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is False

    await sb_fs.write_bytes(
        file_url, bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")
    )
    read_bytes = sb_fs.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_sb_write_bytes_encrypted(
    sb_fs_encrypted: FileSystem,  # noqa: F811
):
    file_url = sb_fs_encrypted.new_file_url_external(
        protocol="sb",
        external_id=None,
        partition="fs_sb_test",
        directory="test_sb_write_bytes_encrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is True

    await sb_fs_encrypted.write_bytes(
        file_url, bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")
    )
    read_bytes = sb_fs_encrypted.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_sb_write_text_unencrypted(
    sb_fs: FileSystem,  # noqa: F811
):
    file_url = sb_fs.new_file_url_external(
        protocol="sb",
        external_id=None,
        partition="fs_sb_test",
        directory="test_sb_write_text_unencrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is False

    await sb_fs.write_text(file_url, "The quick brown fox jumped over the lazy dogs.")
    read_bytes = sb_fs.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


async def test_sb_write_text_encrypted(
    sb_fs_encrypted: FileSystem,  # noqa: F811
):
    file_url = sb_fs_encrypted.new_file_url_external(
        protocol="sb",
        external_id=None,
        partition="fs_sb_test",
        directory="test_sb_write_text_encrypted",
        file_name="file.txt",
    )

    assert file_url.filesystem_external_id is not None
    assert file_url.is_encrypted is True

    await sb_fs_encrypted.write_text(file_url, "The quick brown fox jumped over the lazy dogs.")
    read_bytes = sb_fs_encrypted.read_bytes(file_url)
    assert read_bytes == bytes("The quick brown fox jumped over the lazy dogs.", "utf-8")


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
async def test_sb_checksum_file_unencrypted(
    sb_fs: FileSystem,  # noqa: F811
    sb_file_write,  # noqa: F811
    algo,
    expected_checksum,
):
    file_url: FileUrl = await sb_file_write(
        partition="fs_sb_test", directory="test_sb_checksum_file"
    )
    assert file_url.is_encrypted is False

    checksum = sb_fs.checksum_file(file_url, algo=algo)
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
async def test_sb_checksum_file_encrypted(
    sb_fs_encrypted: FileSystem,  # noqa: F811
    sb_file_write_encrypted,  # noqa: F811
    algo,
    expected_checksum,
):
    file_url: FileUrl = await sb_file_write_encrypted(
        partition="fs_sb_test", directory="test_sb_checksum_file"
    )
    assert file_url.is_encrypted is True

    checksum = sb_fs_encrypted.checksum_file(file_url, algo=algo)
    assert checksum == expected_checksum
