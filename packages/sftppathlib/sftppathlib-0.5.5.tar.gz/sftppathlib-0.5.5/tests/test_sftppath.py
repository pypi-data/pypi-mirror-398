import pytest
from sftppathlib import SFTPPath, load_configs, get_config_path


def test_non_implemented_abstractmethod():
    path = SFTPPath("sftp://example.com")
    with pytest.raises(NotImplementedError):
        path.hardlink_to("hello")


def test_exists():
    path = SFTPPath("sftp://example.com/tmp")
    print(path.__sftppath__())
    assert path.exists()


def test_equality():
    path1 = SFTPPath("sftp://example.com/path")
    path2 = SFTPPath("sftp://example.com/path/")
    assert path1 == path2


def test_alias():
    path = SFTPPath("sftp://example.com/")
    assert repr(path) == "SFTPPath('sftp://example.com/')"


def test_read_alias():
    path = SFTPPath("sftp://example.com/")
    assert path.exists()


def test_iterdir():
    path = SFTPPath("sftp://example.com/tmp")
    assert len(list(path.iterdir())) > 1


def test_from_config():
    configs = load_configs(get_config_path())
    path = SFTPPath.from_config("sftp://example.com",
        config=configs["example.com"])
    assert str(path) == "sftp://example.com"


def test_parts():
    p = SFTPPath("sftp://example.com", "in\\the", "world")
    assert p.as_posix() == 'sftp://example.com/in\\the/world'


def test_parent():
    p = SFTPPath("sftp://example.com/tmp/file")
    assert p.parent == SFTPPath("sftp://example.com/tmp")


def test_init():
    p = SFTPPath("sftp://example.com/tmp/file")
    p = SFTPPath(p)
    assert True


def test_rename():
    p = SFTPPath("sftp://example.com/tmp")
    f1 = p / "test-file-1.txt"
    f2 = p / "test-file-2.txt"
    f1.touch()
    assert f1.exists()
    f1.rename(f2)
    assert not f1.exists()
    assert f2.exists()
    f2.unlink()
    assert not f2.exists()
