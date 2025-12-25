# Klab Pytest Toolkit - Web Fixtures

Custom pytest fixtures for web testing.
The goal is to allow testers to easily test web applications (html/json/rest api) with reusable components.

At the moment the package provides the following fixtures:

- `response_validator_factory`: Factory for create JSON response validator instances with custom configurations.
- `api_client_factory`: Factory for create different API client instances.
  - REST API client for making HTTP requests to RESTful services.
- `web_client_factory`: Factory to create web client instances for browser automation
  - Playwright-based web client for end-to-end testing of web applications.

## Installation

```bash
pip install klab-pytest-toolkit-webfixtures
```

## Usage

### JSON Response Validator

**Create the fixture**

The factory class `ResponseValidatorFactory` is already provided as a pytest fixture `response_validator_factory`.

```python
@pytest.fixture
def json_validator_user_schema(response_validator_factory) -> JsonResponseValidator:
    """Fixture to provide a JSON response validator for user schema."""
    user_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
        },
        "required": ["id", "name"]
    }
    return response_validator_factory.create_json_validator(schema=user_schema)
```

**Functions**

The validator contains one main function to validate a response against the schema. Below is an example of how to use the validator in a test.

```python
def test_user_api(json_validator_user_schema):
    """Test user API response validation."""
    response_data = {
        "id": 1,
        "name": "John Doe"
    }
    assert json_validator_user_schema.validate_response(response_data)
```

### REST API Client

**Create the fixture**

The factory class `ApiClientFactory` is already provided as a pytest fixture `api_client_factory`.
To pass the url or other header information, you can pass this as environment variables or configure directly in the fixture.
Below is an example of creating a REST API client fixture from a testcontainer url.

```python

@pytest.fixture(scope="session")
def httpbin_container():
    """Fixture to provide an HTTPBin container for testing."""

    with DockerContainer("kennethreitz/httpbin:latest") as httpbin:
        httpbin.with_exposed_ports(80)
        httpbin.waiting_for(HttpWaitStrategy(path="/get", port=80).for_status_code(200))
        httpbin.start()
        port = httpbin.get_exposed_port(80)
        base_url = f"http://localhost:{port}"
        yield base_url

@pytest.fixture
def rest_api_client(api_client_factory, httpbin_container) -> RestApiClient:
    """Fixture to provide a REST API client."""
    return api_client_factory.create_rest_client(base_url=httpbin_container)
```

**Functions** 

The REST API client provides functions to make HTTP requests. These are some examples:

```python
def test_get_users(rest_api_client):
    """Test GET /users endpoint."""
    response = rest_api_client.get("/users")
    assert response.status_code == 200

def test_create_user(rest_api_client):
    """Test POST /users endpoint."""
    user_data = {"name": "Jane Doe"}
    response = rest_api_client.post("/users", json=user_data)
    assert response.status_code == 201

def test_update_user(rest_api_client):
    """Test PUT /users/{id} endpoint."""
    user_data = {"name": "Jane Smith"}
    response = rest_api_client.put("/users/1", json=user_data)
    assert response.status_code == 200

def test_delete_user(rest_api_client):
    """Test DELETE /users/{id} endpoint."""
    response = rest_api_client.delete("/users/1")
    assert response.status_code == 204
```

### Playwright Web Client

**Create the fixture**

The factory class `WebClientFactory` is already provided as a pytest fixture `web_client_factory`.
You can create a Playwright web client fixture as shown below:

```python
@pytest.fixture
def web_client(web_client_factory) -> PlaywrightWebClient:
    """Fixture to provide a Playwright web client."""
     with web_client_factory.create_client(client_type="playwright", headless=True) as client:
        yield client
```

**Functions**

The `WebClient` provides a variety of functions for browser automation. Refer to the api of the instance.
Here are some examples of common operations:

```python
def test_navigate_and_click(web_client):
    """Test navigation and clicking a button."""
    web_client.navigate_to("https://example.com")
    web_client.click("#start-button")
    assert web_client.get_text("#result") == "Started"

def test_form_submission(web_client):
    """Test form submission."""
    web_client.navigate_to("https://example.com/form")
    web_client.fill_input("#name", "Test User")
    web_client.fill_input("#email", "max@muster.com")
    web_client.click("#submit-button")
    assert web_client.get_text("#confirmation") == "Thank you for your submission!"

def test_wait_for_element(web_client):
    """Test waiting for an element to appear."""
    web_client.navigate_to("https://example.com/dynamic")
    web_client.wait_for_element("#dynamic-content", timeout=10)
    assert web_client.get_text("#dynamic-content") == "Loaded Content"
```

## Examples

See the test files for comprehensive examples:
- `tests/test_jsonvalidator.py` - JSON validation examples covering basic validation, type checking, nested objects, constraints, and error handling
- `tests/test_restapiclient.py` - REST API client examples with testcontainers integration
- `tests/test_playwrightclient.py` - Playwright web client examples for browser automation with testcontainers

## Best Practices

### Use Testcontainers for Isolated Environments

When testing web applications, it's recommended to use testcontainers to create isolated environments for your services.
This ensures that your tests are reproducible and do not interfere with each other.

## License

MIT
