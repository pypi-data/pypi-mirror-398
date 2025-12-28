# cli-tool Specification

## Purpose
FastAPIアプリケーションに対してサーバーを起動せずにHTTPリクエストを送信するCLIツールの仕様。curlライクなインターフェースでエンドポイントを呼び出し、JSON/フォームデータ/ファイルアップロードをサポートする。
## Requirements
### Requirement: Form Data Support
The CLI tool SHALL support sending multipart/form-data requests using the `-F, --form` option, following curl's convention.

#### Scenario: Single form field
- **WHEN** user executes `fapi-cli request app.py -X POST -P /login -F "username=alice" -F "password=secret"`
- **THEN** the tool sends a POST request to `/login` with Content-Type `multipart/form-data` containing the form fields

#### Scenario: Multiple form fields with same key
- **WHEN** user executes `fapi-cli request app.py -X POST -P /tags -F "tag=python" -F "tag=fastapi"`
- **THEN** the tool sends a POST request with multiple values for the `tag` field

#### Scenario: Form field with special characters
- **WHEN** user executes `fapi-cli request app.py -X POST -P /data -F "message=Hello World!" -F "email=user@example.com"`
- **THEN** the tool correctly encodes and sends the form data

### Requirement: File Upload Support
The CLI tool SHALL support file uploads using the `-F` option with `@` prefix for file paths.

#### Scenario: Single file upload
- **WHEN** user executes `fapi-cli request app.py -X POST -P /upload -F "file=@./document.pdf"`
- **THEN** the tool sends a POST request with the file content as multipart/form-data

#### Scenario: File upload with custom filename
- **WHEN** user executes `fapi-cli request app.py -X POST -P /upload -F "file=@./document.pdf;filename=report.pdf"`
- **THEN** the tool sends the file with the specified filename in the Content-Disposition header

#### Scenario: File upload with Content-Type specification
- **WHEN** user executes `fapi-cli request app.py -X POST -P /upload -F "image=@./photo.jpg;type=image/jpeg"`
- **THEN** the tool sends the file with the specified Content-Type

#### Scenario: Multiple file uploads
- **WHEN** user executes `fapi-cli request app.py -X POST -P /upload -F "files=@./file1.txt" -F "files=@./file2.txt"`
- **THEN** the tool sends multiple files under the same field name

#### Scenario: Mixed form fields and files
- **WHEN** user executes `fapi-cli request app.py -X POST -P /submit -F "title=My Document" -F "document=@./doc.pdf"`
- **THEN** the tool sends both the form field and the file in a single multipart/form-data request

### Requirement: File Path Resolution
The CLI tool SHALL resolve file paths relative to the current working directory.

#### Scenario: Relative file path
- **WHEN** user executes `fapi-cli request app.py -F "file=@./uploads/image.png"` from `/home/user/project`
- **THEN** the tool reads the file from `/home/user/project/uploads/image.png`

#### Scenario: Absolute file path
- **WHEN** user executes `fapi-cli request app.py -F "file=@/tmp/data.json"`
- **THEN** the tool reads the file from the absolute path `/tmp/data.json`

#### Scenario: File not found error
- **WHEN** user specifies a file path that does not exist with `-F "file=@./missing.txt"`
- **THEN** the tool outputs a clear error message indicating the file was not found

### Requirement: Mutual Exclusion of Body Options
The CLI tool SHALL enforce mutual exclusion between `-d` (JSON) and `-F` (form/file) options.

#### Scenario: Both -d and -F specified
- **WHEN** user executes `fapi-cli request app.py -d '{"key":"value"}' -F "field=value"`
- **THEN** the tool outputs an error message indicating that `-d` and `-F` cannot be used together

### Requirement: Command Line Interface
The CLI tool SHALL provide a command-line interface with the following options.

#### Scenario: Help command
- **WHEN** user executes `fapi-cli --help` or `fapi-cli request --help`
- **THEN** the tool displays usage information and available options

#### Scenario: HTTP method specification
- **WHEN** user executes `fapi-cli request src/main.py -X POST` or `fapi-cli request src/main.py --method PUT`
- **THEN** the tool uses the specified HTTP method for the request

#### Scenario: Path specification
- **WHEN** user executes `fapi-cli request src/main.py -P /api/users` or `fapi-cli request src/main.py --path /api/users`
- **THEN** the tool sends the request to the specified path (default: `/`)

#### Scenario: Request body specification
- **WHEN** user executes `fapi-cli request src/main.py -d '{"key":"value"}'` or `fapi-cli request src/main.py --data '{"key":"value"}'`
- **THEN** the tool includes the specified JSON body in the request

#### Scenario: Header specification
- **WHEN** user executes `fapi-cli request src/main.py -H "Key: Value"` or `fapi-cli request src/main.py --header "Key: Value"`
- **THEN** the tool includes the specified header in the request (can be specified multiple times)

#### Scenario: Query parameter specification
- **WHEN** user executes `fapi-cli request src/main.py -q "key=value"` or `fapi-cli request src/main.py --query "key=value"`
- **THEN** the tool appends the query parameters to the request URL

#### Scenario: Form data specification
- **WHEN** user executes `fapi-cli request src/main.py -F "key=value"` or `fapi-cli request src/main.py --form "key=value"`
- **THEN** the tool includes the form field in a multipart/form-data request (can be specified multiple times)

#### Scenario: File upload specification
- **WHEN** user executes `fapi-cli request src/main.py -F "file=@path/to/file"`
- **THEN** the tool uploads the file as part of a multipart/form-data request

### Requirement: FastAPI Request Command
The CLI tool SHALL provide a `fapi-cli request` command that sends HTTP requests to a FastAPI application without starting a server.

#### Scenario: Basic GET request
- **WHEN** user executes `fapi-cli request src/main.py`
- **THEN** the tool loads the FastAPI application from `src/main.py`, sends a GET request to `/`, and outputs the response as JSON to stdout

#### Scenario: GET request with custom path
- **WHEN** user executes `fapi-cli request src/main.py -P /api/users`
- **THEN** the tool sends a GET request to `/api/users` and outputs the response as JSON

#### Scenario: POST request with JSON body
- **WHEN** user executes `fapi-cli request src/main.py -X POST -P /api/users -d '{"name":"Alice"}'`
- **THEN** the tool sends a POST request to `/api/users` with the JSON body `{"name":"Alice"}` and outputs the response as JSON

#### Scenario: Request with custom headers
- **WHEN** user executes `fapi-cli request src/main.py -H "Authorization: Bearer token123" -P /api/protected`
- **THEN** the tool sends a GET request to `/api/protected` with the Authorization header and outputs the response as JSON

#### Scenario: Request with query parameters
- **WHEN** user executes `fapi-cli request src/main.py -P /api/search -q "q=test&limit=10"`
- **THEN** the tool sends a GET request to `/api/search?q=test&limit=10` and outputs the response as JSON

### Requirement: Application Loading
The CLI tool SHALL load FastAPI application instances from Python files.

#### Scenario: Load app from default variable name
- **WHEN** the specified file contains `app = FastAPI()` or `app = FastAPI(...)`
- **THEN** the tool successfully loads the `app` object

#### Scenario: Load app from custom variable name
- **WHEN** the specified file contains `application = FastAPI()` or `fastapi_app = FastAPI()`
- **THEN** the tool attempts to load common variable names (`app`, `application`, `fastapi_app`) and succeeds if found

#### Scenario: File not found error
- **WHEN** user specifies a file path that does not exist
- **THEN** the tool outputs a clear error message indicating the file was not found

#### Scenario: Invalid FastAPI application error
- **WHEN** the specified file does not contain a valid FastAPI application instance
- **THEN** the tool outputs a clear error message indicating the file does not contain a FastAPI application

### Requirement: Response Output Format
The CLI tool SHALL output responses in a structured JSON format to stdout.

#### Scenario: Successful response output
- **WHEN** a request succeeds with status 200
- **THEN** the tool outputs JSON containing at least `status_code` and `body` fields

#### Scenario: Error response output
- **WHEN** a request fails with status 404 or 500
- **THEN** the tool outputs JSON containing `status_code` and `body` fields with error details

#### Scenario: Response headers output (optional)
- **WHEN** user specifies `--include-headers` flag
- **THEN** the tool includes response headers in the output JSON

### Requirement: Error Handling
The CLI tool SHALL handle errors gracefully and provide clear error messages.

#### Scenario: Invalid JSON body
- **WHEN** user specifies `-d` with invalid JSON
- **THEN** the tool outputs a clear error message indicating the JSON is invalid

#### Scenario: Invalid HTTP method
- **WHEN** user specifies an invalid HTTP method with `-X`
- **THEN** the tool outputs a clear error message indicating the method is invalid

#### Scenario: Application import error
- **WHEN** the FastAPI application file has import errors or missing dependencies
- **THEN** the tool outputs a clear error message indicating the import failed

### Requirement: Package Distribution
The CLI tool SHALL be distributable as a Python package on PyPI.

#### Scenario: Package installation
- **WHEN** user executes `pip install fapi-cli`
- **THEN** the `fapi-cli` command becomes available in the user's PATH

#### Scenario: Package metadata
- **WHEN** the package is installed
- **THEN** it includes proper metadata (name, version, description, author, license) in `pyproject.toml`

