from pathlib import Path

from kaizo import ConfigParser

VAL = 16

config = f"""
square:
  module: math
  source: sqrt
  call: true
  args:
    - {VAL}
"""


def test_module_resolution(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()
    entry = out["square"]

    assert entry == VAL**0.5
