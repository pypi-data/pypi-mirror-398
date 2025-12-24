"""FastAPI CLIツールのパッケージエントリ。"""

__all__ = ["__version__"]

try:
    from fapi_cli._version import __version__
except ImportError:  # pragma: no cover - editable install without build
    try:
        from importlib.metadata import version

        __version__ = version("fapi-cli")
    except Exception:
        __version__ = "0.0.0+unknown"
