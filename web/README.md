# AI4EDA Web Interface

The browser interface provides single-file and batch format conversion, ABC
area/delay measurement, and optional AI-assisted Verilog analysis. The source
includes the Flask backend, HTML/CSS/JavaScript UI, launch scripts, and deployment
examples.

## Install and start

From the repository root, activate your Python environment and run:

```bash
python -m pip install -e .
python -m pip install -r web/requirements.txt
cp web/.env.example web/.env
python web/app.py
```

Open **http://127.0.0.1:5000**. Debug mode is off by default.
The Python CLI and graph conversion dependencies are shared with the Toolkit.
ABC and Yosys must also be available for the conversions and measurements that
use them; see [tool setup](../bin/README.md) and the root README. Compiled tool
binaries are not included in the Web source release.

## Configuration

Edit the ignored `web/.env` file, or export environment variables. Exported values
take precedence. `.env.example` contains placeholders only.

| Variable | Purpose / default |
|---|---|
| `VOLCENGINE_API_KEY` | Optional API key for AI analysis; empty disables that feature |
| `VOLCENGINE_BASE_URL` | OpenAI-compatible API base URL; defaults to Volcengine |
| `VOLCENGINE_MODEL` | Model or endpoint ID available to your API account |
| `AI4EDA_SECRET_KEY` | Optional stable Flask secret; otherwise generated on startup |
| `YOSYS_PATH` | Yosys executable for the AI syntax check; defaults to `yosys` |
| `AI4EDA_HOST`, `AI4EDA_PORT` | Development server address; `127.0.0.1`, `5000` |
| `AI4EDA_DEBUG` | Set to `1` only for local development |
| `AI4EDA_BIND` | Gunicorn address; `127.0.0.1:8080` |
| `WEB_CONCURRENCY` | Gunicorn worker count; `2` |

AI analysis sends the submitted Verilog and question to the configured API
provider. It requires your own key and may incur provider charges. Conversion
and ABC metrics work without an AI key. API keys stay on the backend.

The app executes EDA tools and accepts custom ABC scripts. Run it for trusted
users in an isolated environment; it does not provide authentication or a job
sandbox. The default listener is loopback. A shared deployment needs access
control and process/resource isolation.

## Run with Gunicorn

```bash
cd web
./run_production.sh
```

Open **http://127.0.0.1:8080**. Logs are written under `web/logs/`; stop the
process with `kill "$(cat gunicorn.pid)"`. For a background development process,
`./run_daemon.sh start|stop|restart|status` remains available.

To change the Gunicorn port, run `./change_port.sh 9000`, then restart the
process. Deployment templates and systemd/Nginx setup are described in
[PRODUCTION.md](PRODUCTION.md).

## Features and API

- `POST /api/convert`: `file`, `conversion_type`, optional `top_module`.
  Types: `aig2bench`, `bench2graphml`, `graphml2pt`, `verilog2aig`, `aig2pt`, `verilog2pt`.
- `POST /api/convert/batch`: multiple `files` (or a ZIP), plus `conversion_type`.
- `POST /api/metrics`: `file`, `lib_file` (`asap7`, `nangate45`, or `custom`),
  optional `custom_lib` and `opt_script`.
- `POST /api/metrics/batch`: multiple `files` (or a ZIP), with the same metric options.
- `POST /api/analyze`: Verilog `file` and `prompt`. Returns 503 when no API key is set.
- `GET /api/download/<filename>`: retrieve a generated output.
- `GET /api/info`: installed Toolkit/PyTorch/PyG versions.

## Verify setup

```bash
cd web
python test_setup.py
```

Generated uploads, outputs, logs, PID files, editor backups, `.env` files, and
machine-specific systemd/Nginx configuration are excluded from Git. The public
`.example` files can be copied and customized locally.
