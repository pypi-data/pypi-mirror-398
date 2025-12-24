from pathlib import Path


def clients_root_dir(app_dir: Path) -> Path:
    return app_dir / "clients" / "__generated__"


def py_root_dir(app_dir: Path) -> Path:
    return clients_root_dir(app_dir) / "py"


def py_src_dir(app_dir: Path, app_name: str) -> Path:
    return py_root_dir(app_dir) / "src" / f"{app_name}_client"


def runtime_dir(app_dir: Path, app_name: str) -> Path:
    return py_src_dir(app_dir, app_name) / "runtime"


def ts_root_dir(app_dir: Path) -> Path:
    return clients_root_dir(app_dir) / "ts"
