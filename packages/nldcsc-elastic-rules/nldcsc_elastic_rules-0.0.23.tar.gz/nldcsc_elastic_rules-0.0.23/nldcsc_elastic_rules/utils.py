from importlib import resources

rules = resources.files("nldcsc_elastic_rules") / "rules"


def iter_rules():
    yield from rules.rglob("*.toml")
