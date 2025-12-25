from importlib.metadata import PackageNotFoundError, version


def _package_version() -> str:
    try:
        return version("telegram-dsl")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = _package_version()
SUPPORTED_PTB = "22.x"

__all__ = ["__version__", "SUPPORTED_PTB"]
