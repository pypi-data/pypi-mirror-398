import tomllib
from pathlib import Path


def load_toml(filename: str) -> dict:
    with Path(filename).open("rb") as f:
        return tomllib.load(f)

if __name__ == "__main__":
    # check: file not exist 
    file = "a.toml"
    load_toml(file)


    