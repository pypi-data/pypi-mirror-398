from boltpy.core import HarvestConfig


def test_core_imports():
    cfg = HarvestConfig(keywords=["test"], apis=["crossref"], default_ceiling=1)
    assert cfg.default_ceiling == 1
