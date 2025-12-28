# Design: Form and File Upload Support

## Context

FastAPIでは以下のリクエストボディ形式をサポートしている：
- JSON (`application/json`) - 現在サポート済み
- Form (`application/x-www-form-urlencoded`)
- Multipart (`multipart/form-data`) - ファイルアップロードを含む

curlでは`-F`オプションで`multipart/form-data`を送信できる。fapi-cliもこれを踏襲する。

## Goals / Non-Goals

### Goals
- curlライクな`-F, --form`オプションでmultipart/form-dataを送信
- ファイルアップロード（`@`記法）のサポート
- 複数フィールド/ファイルの同時送信
- FastAPIの`Form()`と`File()`/`UploadFile`エンドポイントをテスト可能にする

### Non-Goals
- WebSocket対応（別変更で対応）
- ストリームレスポンス対応（別変更で対応）
- `-d`オプションの動作変更（既存動作を維持）

## Decisions

### Decision 1: `-F`オプションの形式

curlの`-F`オプションを踏襲し、以下の形式をサポート：

```bash
# フォームフィールド
fapi-cli request app.py -F "name=Alice" -F "age=30"

# ファイルアップロード（@記法）
fapi-cli request app.py -F "avatar=@./image.png"

# Content-Type指定（オプション）
fapi-cli request app.py -F "document=@./file.pdf;type=application/pdf"

# 混合（フォームフィールド + ファイル）
fapi-cli request app.py -F "name=Alice" -F "profile=@./profile.jpg"
```

**Rationale**: curlユーザーにとって馴染みのある形式であり、学習コストが低い。

### Decision 2: `-d`と`-F`の排他制御

`-d`（JSON）と`-F`（multipart）は同時に指定できない。両方指定された場合はエラーとする。

**Rationale**: HTTPリクエストボディは単一のContent-Typeしか持てないため。

### Decision 3: 実装アプローチ

`RequestConfig`データクラスを拡張し、新しいフィールドを追加：

```python
@dataclass
class RequestConfig:
    method: str
    path: str
    headers: Dict[str, str]
    query: List[Tuple[str, str]]
    json_body: Optional[Any]
    form_data: Optional[Dict[str, str]]  # 新規
    files: Optional[Dict[str, Tuple[str, Any, Optional[str]]]]  # 新規
    include_headers: bool
```

TestClientの`request()`メソッドは`data`パラメータ（フォーム）と`files`パラメータ（ファイル）をサポートしているため、これらを活用する。

### Decision 4: ファイルパスの解決

ファイルパスは実行時のカレントディレクトリからの相対パスとして解決する。絶対パスも使用可能。

## Risks / Trade-offs

- **Risk**: 大きなファイルのメモリ使用量
  - **Mitigation**: TestClientがストリーミングを処理するため、CLIレベルでは特別な対応不要

- **Trade-off**: curlとの完全な互換性は目指さない
  - フォームデータの高度な機能（`--form-string`、`--form-escape`など）は初期実装では省略

## Open Questions

- なし（初期実装のスコープは明確）

