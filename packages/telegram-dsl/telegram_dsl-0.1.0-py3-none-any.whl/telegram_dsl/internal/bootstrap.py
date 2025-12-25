import importlib
import pkgutil


def autoload_recursive(package_name: str):
    """Recursively import all modules under a package to trigger decorators."""
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        return
    for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            importlib.import_module(name)
        except ValueError as exc:
            raise ValueError(
                f"Autoload failed while importing '{name}': {exc}"
            ) from None
