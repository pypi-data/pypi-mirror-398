# Agents Knowledge

This is an MCP (Model Context Protocol) server for the [SearxNG](https://docs.searxng.org/) meta search engine, providing search capabilities to AI assistants through a standardized protocol.

## Project Overview

The server exposes four main search tools:
- `search_web` - General web search with customizable parameters
- `search_images` - Image search functionality
- `search_videos` - Video search functionality
- `search_news` - News search with time range filtering

## Architecture

### Core Components

- **FastMCP Integration**: Uses the `fastmcp` library for MCP server implementation
- **SearxNGClient**: Main client class in `src/searxng_mcp_server/tools.py` that handles all SearxNG API interactions
- **Pydantic Models**: Type-safe data models in `models.py` for search results and responses
- **Configuration Management**: Environment-based configuration with CLI argument support
- **Logging**: Structured logging with configurable levels

### Module Structure

```
src/searxng_mcp_server/
├── __init__.py      # Package initialization, exports main function
├── main.py          # MCP server setup and tool registration
├── config.py        # Configuration handling from env/CLI args
├── tools.py         # SearxNGClient implementation and search methods
├── models.py        # Pydantic models for search results
└── log.py           # Logging configuration
```

## Dependencies

- **fastmcp**: MCP server framework
- **httpx**: Async HTTP client for SearxNG API calls
- **pydantic**: Data validation and serialization

## Configuration

The server supports environment variables and CLI arguments:

- `SEARXNG_URL`: SearxNG instance URL
- `SEARXNG_TIMEOUT`: Request timeout in seconds (default: 30)
- `SEARXNG_USER_AGENT`: Custom user agent string (default: searxng-mcp-server/0.1.0)
- `LOG_LEVEL`: Logging level (default: INFO)


## Code Conventions

- Write modular, clean and fully typed modern python code.
- Use lower case for logs: logger.info("starting xyz").
- Prefer logger instead of print statements.
- Log lines and exceptions should always start with a lowercase char.
- Log lines should not end with a period.
- Try not to use `Any` for typing.
- All code should be typed using modern python.
- Use early returns to reduce indentation.
- Extract complex logic into functions.
- Flatten loops with list comprehensions.
- Leverage data structures instead of deeply nested conditions.
- Write self-explanatory code – Prefer clear variable and function names over comments.
- Explain "why," not "what" – Comments should clarify intent, not restate code.
- Avoid redundant comments – Don't comment obvious things.
- Use comments for complex logic – Explain non-trivial decisions or workarounds.
- Write docstrings for functions/classes – Document purpose, inputs, and outputs.
- Keep comments updated – Outdated comments are worse than none.
- Use inline comments sparingly – Only when necessary for clarity.
- Let Python handle exceptions by default - prefer crashing over complex error handling
- Only add try-except blocks when:
  - Explicitly required to keep the application running.
  - Requested by the user/product requirements.
  - Handling a specific, recoverable error case.
- Instead of defensive programming with try-except blocks:
  - Use assertions to validate critical assumptions.
  - Let functions fail fast with invalid inputs - Don't catch broad exceptions (except Exception).
  - Trust Python's built-in error handling.
- Let stack traces expose issues during development.

## Linting

```
make lint
```

```
make mypy
```

## Formatting

```
make format
```

## Dependency Management

We use uv to manage Python dependencies.

Run

```
uv add <your-package-name>
```

This installs the package and adds it to `pyproject.toml`.

## Running The Application

```
make run
```
