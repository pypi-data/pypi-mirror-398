"""FastAPIバージョン互換性のテスト。"""

from __future__ import annotations

from fapi_cli.version import get_fastapi_version, is_fastapi_version_at_least


def test_get_fastapi_version() -> None:
    """FastAPIのバージョンを取得できることを確認する。"""
    version = get_fastapi_version()
    assert version != "0.0.0"
    # バージョン形式の確認（例: "0.87.0" や "0.115.0"）
    assert "." in version


def test_is_fastapi_version_at_least() -> None:
    """バージョン比較が正しく動作することを確認する。"""
    # 現在のバージョンは0.100.0以上であるべき（最小サポートバージョン）
    assert is_fastapi_version_at_least("0.100.0")
    # 0.0.0より大きいことを確認
    assert is_fastapi_version_at_least("0.0.0")
    # 非常に大きなバージョンより小さいことを確認
    assert not is_fastapi_version_at_least("999.0.0")


def test_version_comparison_logic() -> None:
    """バージョン比較ロジックが正しく動作することを確認する。"""
    current = get_fastapi_version()

    # 現在のバージョンは自分自身以上
    assert is_fastapi_version_at_least(current)

    # 現在のバージョンより1つ大きいバージョンは満たさない
    parts = current.split(".")
    if len(parts) >= 2:
        major, minor = int(parts[0]), int(parts[1])
        future_version = f"{major}.{minor + 1}.0"
        assert not is_fastapi_version_at_least(future_version)
