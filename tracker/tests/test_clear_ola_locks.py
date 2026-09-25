"""Real-file tests for the OLA serial lock cleanup command."""

from pathlib import Path

import pytest

from deploy.pi.clear_ola_locks import main


@pytest.fixture
def roots(tmp_path):
    lock_dir = tmp_path / "lock"
    proc_dir = tmp_path / "proc"
    dev_dir = tmp_path / "dev"
    for path in (lock_dir, proc_dir, dev_dir):
        path.mkdir()
    return lock_dir, proc_dir, dev_dir


def run_cleanup(roots):
    return main(lock_dir=roots[0], proc_dir=roots[1], dev_dir=roots[2])


def make_lock(roots, name="LCK..ttyUSB0", pid="123\n"):
    path = roots[0] / name
    path.write_text(pid, encoding="ascii")
    return path


def make_fd_link(path, target):
    try:
        path.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"This host cannot create test symlinks: {exc}")


def test_removes_stale_lock_and_reports_it(roots, capsys):
    lock = make_lock(roots)

    assert run_cleanup(roots) == 0

    assert not lock.exists()
    assert str(lock) in capsys.readouterr().out


def test_removes_lock_when_recorded_pid_no_longer_owns_device(roots):
    lock = make_lock(roots)
    (roots[1] / "123" / "fd").mkdir(parents=True)

    assert run_cleanup(roots) == 0

    assert not lock.exists()


def test_refuses_lock_when_recorded_pid_has_device_open(roots, capsys):
    lock = make_lock(roots)
    device = roots[2] / "ttyUSB0"
    device.touch()
    fd_dir = roots[1] / "123" / "fd"
    fd_dir.mkdir(parents=True)
    make_fd_link(fd_dir / "4", device)

    assert run_cleanup(roots) != 0

    assert lock.exists()
    assert "ttyUSB0" in capsys.readouterr().err


def test_refuses_lock_when_another_pid_has_device_open(roots):
    lock = make_lock(roots)
    device = roots[2] / "ttyUSB0"
    device.touch()
    fd_dir = roots[1] / "456" / "fd"
    fd_dir.mkdir(parents=True)
    make_fd_link(fd_dir / "8", device)

    assert run_cleanup(roots) != 0

    assert lock.exists()


def test_refuses_symlink_lock(roots, capsys):
    target = roots[0] / "target"
    target.write_text("123\n", encoding="ascii")
    lock = roots[0] / "LCK..ttyUSB0"
    make_fd_link(lock, target)

    assert run_cleanup(roots) != 0

    assert lock.is_symlink()
    assert target.exists()
    assert capsys.readouterr().err


def test_refuses_directory_lock(roots, capsys):
    lock = roots[0] / "LCK..ttyUSB0"
    lock.mkdir()

    assert run_cleanup(roots) != 0

    assert lock.is_dir()
    assert capsys.readouterr().err


@pytest.mark.parametrize("pid", ["", "bad\n", "123\n456\n", "0\n"])
def test_refuses_invalid_pid(roots, pid, capsys):
    lock = make_lock(roots, pid=pid)

    assert run_cleanup(roots) != 0

    assert lock.exists()
    assert capsys.readouterr().err


def test_bad_candidate_prevents_any_deletion(roots):
    good = make_lock(roots, name="LCK..ttyUSB0")
    bad = make_lock(roots, name="LCK..ttyUSB1", pid="bad\n")

    assert run_cleanup(roots) != 0

    assert good.exists()
    assert bad.exists()


def test_ignores_other_names_and_nested_locks(roots):
    other = make_lock(roots, name="LCK..ttyACM0")
    nested_dir = roots[0] / "nested"
    nested_dir.mkdir()
    nested = nested_dir / "LCK..ttyUSB0"
    nested.write_text("123\n", encoding="ascii")

    assert run_cleanup(roots) == 0

    assert other.exists()
    assert nested.exists()
