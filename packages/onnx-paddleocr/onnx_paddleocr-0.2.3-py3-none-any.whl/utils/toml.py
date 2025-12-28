import toml


def read_toml(fp: str):
    with open(fp, "r", encoding="utf-8") as f:
        return toml.load(f)
