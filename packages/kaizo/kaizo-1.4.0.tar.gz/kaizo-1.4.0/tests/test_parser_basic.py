from pathlib import Path

from kaizo import ConfigParser
from kaizo.utils import DictEntry

A = 10
B = "hello"
C = 3.5
PATH = "./local/path"

dict_config = f"""
a: {A}
b: {B}
c: {C}
"""

lst_config = """
lst:
  - 1
  - 2
  - 3
"""

path_config = f"""
path: {PATH}
"""


def test_basic_scalars(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(dict_config)

    parser = ConfigParser(cfg_file)
    res = parser.parse()

    assert isinstance(res, DictEntry)

    assert res["a"] == A
    assert res["b"] == B
    assert res["c"] == C


def test_list_parsing(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(lst_config)

    parser = ConfigParser(cfg_file)
    res = parser.parse()

    assert isinstance(res, DictEntry)

    lst_entry = res["lst"]

    assert list(lst_entry) == [1, 2, 3]


def test_basic_path(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(path_config)

    parser = ConfigParser(cfg_file)
    res = parser.parse()

    assert isinstance(res, DictEntry)

    assert res["path"] == PATH
