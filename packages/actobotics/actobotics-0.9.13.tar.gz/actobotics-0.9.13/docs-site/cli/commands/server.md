# acto server

Run the ACTO server locally for development.

::: danger For Contributors Only
This command is **only for ACTO contributors** developing the codebase locally.

**Regular users should NOT run their own server.** Use the hosted platform:
- **Dashboard:** [api.actobotics.net/dashboard](https://api.actobotics.net/dashboard)  
- **API:** `https://api.actobotics.net`
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

