# acto server

Run the ACTO server locally.

::: warning For Contributors
Server functionality is primarily for development and self-hosting scenarios.
:::

## Commands

| Command | Description |
|---------|-------------|
| `acto server run` | Start the ACTO server |

## Run Server

```bash
acto server run [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host`, `-h` | Host to bind to | `127.0.0.1` |
| `--port`, `-p` | Port to listen on | `8080` |
| `--reload` | Enable auto-reload | `false` |
| `--config`, `-c` | Config file path | - |

### Examples

```bash
# Basic usage
acto server run

# Custom port
acto server run --port 3000

# Development mode with reload
acto server run --reload

# With config file
acto server run --config config.toml
```

### Output

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

## Requirements

Server functionality requires additional dependencies:

```bash
pip install actobotics[dev]
```

