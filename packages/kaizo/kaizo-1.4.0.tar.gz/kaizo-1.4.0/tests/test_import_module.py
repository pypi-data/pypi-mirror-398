from pathlib import Path

from kaizo import ConfigParser

X = 5

module_config = f"""
x: {X}
"""

relative_config = """
import:
  m: module.yml
run: m.{x}
"""

absolute_config = """
import:
  m: {tmp_path}/module.yml
run: m.{x}
"""


def test_relative_import_module(tmp_path: Path) -> None:
    module = tmp_path / "module.yml"
    module.write_text(module_config)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(relative_config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["run"] == X


def test_absolute_import_module(tmp_path: Path) -> None:
    module = tmp_path / "module.yml"
    module.write_text(module_config)

    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(absolute_config.replace("{tmp_path}", str(tmp_path)))

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    assert out["run"] == X
