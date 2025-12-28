## ADDED Requirements

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

