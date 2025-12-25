import pytest
from nrhgen.hasher import hash_text, hash_file


def test_hash_text_md5():
    result = hash_text("hello", "md5")
    assert result == "5d41402abc4b2a76b9719d911017c592"


def test_hash_text_sha256():
    result = hash_text("hello", "sha256")
    assert result == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e"
        "1b161e5c1fa7425e73043362938b9824"
    )


def test_hash_text_invalid_algo():
    try:
        hash_text("hello", "fakealgo")
        assert False
    except ValueError:
        assert True


def test_hash_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")

    result = hash_file(test_file, "md5")
    assert result == "5d41402abc4b2a76b9719d911017c592"

