import sys
import types

from telegram_dsl.internal.bootstrap import autoload_recursive


def test_autoload_recursive(tmp_path):
    pkg_dir = tmp_path / "temp_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("value = 0")
    (pkg_dir / "module_a.py").write_text("flag = True")

    sys.path.insert(0, str(tmp_path))
    try:
        autoload_recursive("temp_pkg")
        module = __import__("temp_pkg.module_a", fromlist=["flag"])
        assert getattr(module, "flag") is True
    finally:
        sys.path.remove(str(tmp_path))
