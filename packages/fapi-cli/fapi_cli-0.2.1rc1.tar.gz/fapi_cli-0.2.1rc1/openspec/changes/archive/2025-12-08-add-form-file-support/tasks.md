## 1. Core Implementation

- [x] 1.1 `RequestConfig`データクラスに`form_data`と`files`フィールドを追加
- [x] 1.2 `-F, --form`オプションをパースする`_parse_form`関数を実装
  - `key=value`形式のフォームフィールド解析
  - `key=@path`形式のファイル指定検出
  - `;type=`と`;filename=`のメタデータ解析
- [x] 1.3 ファイル読み込み処理の実装（パス解決、存在確認、バイナリ読み込み）
- [x] 1.4 `-d`と`-F`の排他制御を実装（両方指定時はエラー）
- [x] 1.5 `_execute_request`関数を拡張し、`data`と`files`パラメータをTestClientに渡す

## 2. CLI Integration

- [x] 2.1 `request`コマンドに`-F, --form`オプションを追加（複数指定可能）
- [x] 2.2 ヘルプメッセージを更新

## 3. Error Handling

- [x] 3.1 ファイルが存在しない場合のエラーメッセージ
- [x] 3.2 `-F`オプションの形式が不正な場合のエラーメッセージ
- [x] 3.3 `-d`と`-F`の同時指定エラーメッセージ

## 4. Testing

- [x] 4.1 フォームフィールド送信のテスト
- [x] 4.2 ファイルアップロードのテスト
- [x] 4.3 混合（フォーム + ファイル）のテスト
- [x] 4.4 エラーケースのテスト（ファイル不存在、排他制御など）
- [x] 4.5 Content-Type/filename指定のテスト

## 5. Documentation

- [x] 5.1 READMEに使用例を追加

