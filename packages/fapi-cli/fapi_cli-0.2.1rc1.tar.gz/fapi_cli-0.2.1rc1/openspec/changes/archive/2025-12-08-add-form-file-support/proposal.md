# Change: Add Form and File Upload Support

## Why

現在のfapi-cliは`-d`オプションでJSONリクエストボディのみをサポートしています。FastAPIアプリケーションでは、フォームデータ（`application/x-www-form-urlencoded`）やファイルアップロード（`multipart/form-data`）も頻繁に使用されます。これらのコンテンツタイプをサポートすることで、より多くのFastAPIエンドポイントをテストできるようになります。

## What Changes

- curlの`-F, --form`オプションを踏襲した`multipart/form-data`サポートを追加
- フォームフィールド: `-F "key=value"` 形式
- ファイルアップロード: `-F "file=@path/to/file"` 形式（`@`プレフィックスでファイルパスを指定）
- 複数の`-F`オプションを組み合わせて、フォームフィールドとファイルを同時に送信可能
- ファイルのContent-Type指定: `-F "file=@path;type=image/png"` 形式（オプション）

## Impact

- Affected specs: `cli-tool` (既存specの拡張)
- Affected code: `src/fapi_cli/cli.py` - RequestConfig拡張、新しいパーサー関数追加
- 破壊的変更: なし（既存の`-d`オプションの動作は維持）

## Future Scope

将来的に以下のリクエスト/レスポンス形式もサポート予定：
- `--data-urlencode`: URLエンコードされたフォームデータ
- `--stream`: ストリームレスポンスのリアルタイム出力
- WebSocket対応

