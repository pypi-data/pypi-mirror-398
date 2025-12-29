from pathlib import Path

from kaizo import ConfigParser

cache_config = """
with_cache:
  module: random
  source: random
  cache: true
without_cache:
  module: random
  source: random
  cache: false
"""


def test_cache(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.yml"
    cfg_file.write_text(cache_config)

    parser = ConfigParser(cfg_file)
    out = parser.parse()

    with_cache_1 = out["with_cache"]
    with_cache_2 = out["with_cache"]
    without_cache_1 = out["without_cache"]
    without_cache_2 = out["without_cache"]

    assert with_cache_1 == with_cache_2
    assert without_cache_2 != without_cache_1
