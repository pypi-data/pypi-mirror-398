from pathlib import Path

import pytest

from kaizo import ConfigParser

dummy_config = """
dummy: this_is_dummy
"""

missing_local_config = """
local: missing.py
"""

module_not_exist_config = """
bad:
  module: does_not_exist
  source: thing
"""

invalid_import_type_config = """
import: not_a_dict
"""

missing_import_file_config = """
import:
  miss: missing_module.yml
"""

module_not_given_config = """
bad_ref: missing_module.{some_key}
"""

keyword_not_found_config = """
import:
  dummy: dummy.yml
bad_ref: missing_module.{some_key}
"""

entry_not_found_config = """
import:
  dummy: dummy.yml
bad_key: dummy.{not_here}
"""

local_entry_not_found_config = """
bad_key: .{not_here}
"""


def test_missing_local_module(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yml"
    cfg.write_text(missing_local_config)

    with pytest.raises(FileNotFoundError):
        ConfigParser(cfg)


def test_import_error(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yml"
    cfg.write_text(module_not_exist_config)

    parser = ConfigParser(cfg)

    with pytest.raises(ImportError):
        parser.parse()


def test_invalid_import_type(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yml"
    cfg.write_text(invalid_import_type_config)

    with pytest.raises(TypeError):
        ConfigParser(cfg)


def test_missing_import_file(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yml"
    cfg.write_text(missing_import_file_config)

    with pytest.raises(FileNotFoundError):
        ConfigParser(cfg)


def test_module_not_given(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yml"
    cfg.write_text(module_not_given_config)

    parser = ConfigParser(cfg)

    with pytest.raises(ValueError, match="import module is not given"):
        parser.parse()


def test_keyword_not_found(tmp_path: Path) -> None:
    dummy_module = tmp_path / "dummy.yml"
    dummy_module.write_text(dummy_config)

    cfg = tmp_path / "cfg.yml"
    cfg.write_text(keyword_not_found_config)

    parser = ConfigParser(cfg)

    with pytest.raises(ValueError, match="keyword not found, got missing_module"):
        parser.parse()


def test_entry_not_found(tmp_path: Path) -> None:
    dummy_module = tmp_path / "dummy.yml"
    dummy_module.write_text(dummy_config)

    cfg = tmp_path / "cfg.yml"
    cfg.write_text(entry_not_found_config)

    parser = ConfigParser(cfg)

    with pytest.raises(KeyError, match="entry not found, got not_here"):
        parser.parse()


def test_local_entry_not_found(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.yml"
    cfg.write_text(local_entry_not_found_config)

    parser = ConfigParser(cfg)

    with pytest.raises(KeyError, match="entry not found, got not_here"):
        parser.parse()
