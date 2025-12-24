import json
from pathlib import Path

__all__ = ["__version__"]


# We want the version of the server extension package match the version
# of NPM package (UI extension)
# Read the version of UI extension from `package.json` and use it as the
# version number of the server extension package
def _fetchVersion():
    HERE = Path(__file__).parent.resolve()

    for settings in HERE.rglob("package.json"):
        try:
            with settings.open(encoding="utf-8") as f:
                return json.load(f)["version"]
        except FileNotFoundError:
            pass

    raise FileNotFoundError(f"Could not find package.json under dir {HERE!s}")


__version__ = _fetchVersion()
