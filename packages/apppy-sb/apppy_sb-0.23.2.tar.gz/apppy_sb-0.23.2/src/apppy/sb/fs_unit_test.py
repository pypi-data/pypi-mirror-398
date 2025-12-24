import pytest

from apppy.fs import FileSystemBucket, FileUrl
from apppy.sb.fs import SupabaseFileUrl

_supabase_fs_bucket_external_test = FileSystemBucket(
    bucket_type="external", value="fs_supabase_test"
)

_case_dir_only: SupabaseFileUrl = SupabaseFileUrl(
    _filesystem_protocol="sb",
    _filesystem_bucket=_supabase_fs_bucket_external_test,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir",
    _file_name=None,
)
_case_dir_with_subdir: SupabaseFileUrl = SupabaseFileUrl(
    _filesystem_protocol="sb",
    _filesystem_bucket=_supabase_fs_bucket_external_test,
    _filesystem_external_id=None,
    _partition="partition",
    _directory="dir/subdir",
    _file_name=None,
)
# Malformed url for the Supabase case
# _case_file_name_only: SupabaseFileUrl = SupabaseFileUrl(
#     _filesystem_protocol="sb",
#     _filesystem_bucket=_supabase_fs_bucket_external_test,
#     _filesystem_external_id=None,
#     _partition="partition",
#     _directory=None,
#     _file_name="f.txt",
# )
# Malformed url for the Supabase case
# _case_file_name_with_dir: SupabaseFileUrl = SupabaseFileUrl(
#     _filesystem_protocol="sb",
#     _filesystem_bucket=_supabase_fs_bucket_external_test,
#     _filesystem_external_id=None,
#     _partition="partition",
#     _directory="dir",
#     _file_name="f.txt",
# )
# Malformed url for the Supabase case
# _case_unique_id_only: SupabaseFileUrl = SupabaseFileUrl(
#     _filesystem_protocol="sb",
#     _filesystem_bucket=_supabase_fs_bucket_external_test,
#     _filesystem_external_id="123-abc",
#     _partition="partition",
#     _directory=None,
#     _file_name=None,
# )
# Malformed url for the Supabase case
# _case_unique_id_with_dir: SupabaseFileUrl = SupabaseFileUrl(
#     _filesystem_protocol="sb",
#     _filesystem_bucket=_supabase_fs_bucket_external_test,
#     _filesystem_external_id="123-abc",
#     _partition="partition",
#     _directory="dir",
#     _file_name=None,
# )
_case_unique_id_with_dir_and_file_name: SupabaseFileUrl = SupabaseFileUrl(
    _filesystem_protocol="sb",
    _filesystem_bucket=_supabase_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)
_case_unique_id_with_file_name: SupabaseFileUrl = SupabaseFileUrl(
    _filesystem_protocol="sb",
    _filesystem_bucket=_supabase_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory=None,
    _file_name="f.txt",
)
_case_unique_id_with_dir_and_file_name_encrypted: SupabaseFileUrl = SupabaseFileUrl(
    _filesystem_protocol="enc://sb",
    _filesystem_bucket=_supabase_fs_bucket_external_test,
    _filesystem_external_id="123-abc",
    _partition="partition",
    _directory="dir",
    _file_name="f.txt",
)


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "sb://external/partition/dir"),
        (_case_dir_with_subdir, "sb://external/partition/dir/subdir"),
        (_case_unique_id_with_dir_and_file_name, "sb://external/partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "sb://external/partition/@123-abc$f.txt"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "enc://sb://external/partition/dir/@123-abc$f.txt",
        ),
    ],
)
def test_supabase_file_url_str(file_url: FileUrl, expected_str: str):
    assert str(file_url) == expected_str


@pytest.mark.parametrize(
    "file_url, expected_str",
    [
        (_case_dir_only, "sb://fs_supabase_test/partition/dir"),
        (_case_dir_with_subdir, "sb://fs_supabase_test/partition/dir/subdir"),
        (
            _case_unique_id_with_dir_and_file_name,
            "sb://fs_supabase_test/partition/dir/@123-abc$f.txt",
        ),
        (_case_unique_id_with_file_name, "sb://fs_supabase_test/partition/@123-abc$f.txt"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "sb://fs_supabase_test/partition/dir/@123-abc$f.txt",
        ),
    ],
)
def test_supabase_file_url_str_internal(file_url: FileUrl, expected_str: str):
    assert file_url.as_str_internal() == expected_str


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("external/partition/dir", _case_dir_only),
        ("external/partition/dir/subdir", _case_dir_with_subdir),
        ("external/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("external/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
    ],
)
def test_supabase_file_url_split_path(path: str, expected_file_url: FileUrl):
    file_url = SupabaseFileUrl.split_path(
        path, protocol="sb", bucket=_supabase_fs_bucket_external_test
    )
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "path, expected_file_url",
    [
        ("fs_supabase_test/partition/dir", _case_dir_only),
        ("fs_supabase_test/partition/dir/subdir", _case_dir_with_subdir),
        ("fs_supabase_test/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("fs_supabase_test/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
    ],
)
def test_supabase_file_url_split_path_unobfuscated(path: str, expected_file_url: FileUrl):
    file_url = SupabaseFileUrl.split_path(
        path, protocol="sb", bucket=_supabase_fs_bucket_external_test
    )
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "url, expected_file_url",
    [
        ("sb://external/partition/dir", _case_dir_only),
        ("sb://external/partition/dir/subdir", _case_dir_with_subdir),
        ("sb://external/partition/dir/@123-abc$f.txt", _case_unique_id_with_dir_and_file_name),
        ("sb://external/partition/@123-abc$f.txt", _case_unique_id_with_file_name),
        (
            "enc://sb://external/partition/dir/@123-abc$f.txt",
            _case_unique_id_with_dir_and_file_name_encrypted,
        ),
    ],
)
def test_supabase_file_url_split_url(url: str, expected_file_url: FileUrl):
    file_url = SupabaseFileUrl.split_url(url, bucket=_supabase_fs_bucket_external_test)
    assert file_url == expected_file_url


@pytest.mark.parametrize(
    "file_url, expected_key_prefix",
    [
        (_case_dir_only, "partition/dir"),
        (_case_dir_with_subdir, "partition/dir/subdir"),
        (_case_unique_id_with_dir_and_file_name, "partition/dir/@123-abc$f.txt"),
        (_case_unique_id_with_file_name, "partition/@123-abc$f.txt"),
    ],
)
def test_supabase_file_url_key_prefix(file_url: SupabaseFileUrl, expected_key_prefix: str):
    assert file_url.key_prefix == expected_key_prefix


@pytest.mark.parametrize(
    "file_url, expected_key_prefix_parent",
    [
        (_case_dir_only, "partition"),
        (_case_dir_with_subdir, "partition/dir"),
        (_case_unique_id_with_dir_and_file_name, "partition/dir"),
        (_case_unique_id_with_file_name, "partition"),
    ],
)
def test_supabase_file_url_key_prefix_parent(
    file_url: SupabaseFileUrl, expected_key_prefix_parent: str
):
    assert file_url.key_prefix_parent == expected_key_prefix_parent


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_dir_only),
        (_case_dir_with_subdir),
    ],
)
def test_supabase_file_url_is_directory(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is True
    assert file_url.is_file is False


@pytest.mark.parametrize(
    "file_url",
    [
        (_case_unique_id_with_dir_and_file_name),
        (_case_unique_id_with_file_name),
    ],
)
def test_supabase_file_url_is_file(file_url: FileUrl):
    assert file_url.is_valid is True
    assert file_url.is_directory is False
    assert file_url.is_file is True


@pytest.mark.parametrize(
    "file_url, join_dir, join_file_name, expected_joined_path",
    [
        (_case_dir_only, None, None, "sb://fs_supabase_test/partition/dir"),
        (_case_dir_only, "join_dir", None, "sb://fs_supabase_test/partition/dir/join_dir"),
        (_case_dir_only, None, "join_f.txt", "sb://fs_supabase_test/partition/dir/join_f.txt"),
        (
            _case_dir_only,
            "join_dir",
            "join_f.txt",
            "sb://fs_supabase_test/partition/dir/join_dir/join_f.txt",
        ),
    ],
)
def test_supabase_file_url_join(
    file_url: SupabaseFileUrl,
    join_dir: str | None,
    join_file_name: str | None,
    expected_joined_path: str,
):
    joined_file_url = file_url.join(directory=join_dir, file_name=join_file_name)
    assert joined_file_url.as_str_internal() == expected_joined_path


@pytest.mark.parametrize(
    "file_url, expected_parent_path",
    [
        (_case_dir_only, "sb://fs_supabase_test/partition"),
        (_case_dir_with_subdir, "sb://fs_supabase_test/partition/dir"),
        (_case_unique_id_with_dir_and_file_name, "sb://fs_supabase_test/partition/dir"),
        (_case_unique_id_with_file_name, "sb://fs_supabase_test/partition"),
        (
            _case_unique_id_with_dir_and_file_name_encrypted,
            "sb://fs_supabase_test/partition/dir",
        ),
    ],
)
def test_supabase_file_url_parent(file_url: SupabaseFileUrl, expected_parent_path: str):
    parent_file_url = file_url.parent()
    assert parent_file_url.as_str_internal() == expected_parent_path
