# Change: Create FastAPI CLI Tool

## Why

FastAPIアプリケーションをテスト・開発する際、サーバーを立ち上げてHTTPリクエストを送信する必要があり、開発フローが煩雑です。Hono CLIの`hono request`コマンドのように、サーバーを立ち上げずにFastAPIアプリケーションに対して直接リクエストを送信し、レスポンスのJSONを取得できるCLIツールを提供することで、開発効率を向上させます。

また、AIコーディングエージェントがFastAPIアプリケーションをテストする際にも、サーバーの起動・停止の管理が不要になり、より高速で正確なテストが可能になります。

## What Changes

- FastAPIアプリケーションに対してサーバーを立ち上げずにリクエストを送信するCLIツールを追加
- `fapi-cli request`コマンドで、指定したFastAPIアプリケーションファイルに対してHTTPリクエストを送信
- レスポンスをJSONフォーマットで標準出力に表示
- curlライクなコマンドライン引数（`-X`でメソッド指定、`-d`でボディ指定、`-H`でヘッダー指定など）をサポート
- PyPIに公開可能なパッケージ構造を提供

## Impact

- Affected specs: `cli-tool` (新規)
- Affected code: 新規プロジェクト（CLIツールの実装、パッケージング設定）
- 外部依存: FastAPI、ASGI、Click/Typer（CLIフレームワーク）

