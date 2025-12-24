"""FastAPIバージョン互換性のためのユーティリティ。"""

from __future__ import annotations

from packaging import version as pkg_version


def get_fastapi_version() -> str:
    """インストールされているFastAPIのバージョンを取得する。"""
    try:
        from fastapi import __version__

        return __version__
    except ImportError:
        return "0.0.0"


def is_fastapi_version_at_least(min_version: str) -> bool:
    """FastAPIのバージョンが指定された最小バージョン以上かどうかを確認する。"""
    try:
        current = get_fastapi_version()
        return pkg_version.parse(current) >= pkg_version.parse(min_version)
    except Exception:
        return False
