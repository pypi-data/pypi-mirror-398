"""
Writes and reads a .lang file.
"""

import mclang


def test_write_file():
    obj = {
        "test": "§cThis is cool!",
        "test2": "§aIt worked!",
    }

    with mclang.open("tests/en_US.lang", "w") as lang:
        lang.update(obj)


def test_read_file():
    with mclang.open("tests/en_US.lang", "r") as lang:
        assert lang.tl("test") == "§cThis is cool!"
        assert lang.tl("test2") == "§aIt worked!"


def test_rw_file():
    with mclang.open("tests/en_US.lang", "rw") as lang:
        lang["added"] = "§cUpdated!"
