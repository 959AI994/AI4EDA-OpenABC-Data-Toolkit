# Deploying the Web interface

Install the Toolkit and `web/requirements.txt` in your Python environment, then
configure `web/.env` as described in [README.md](README.md). Begin with:

```bash
cd web
./run_production.sh
```

Gunicorn listens on `127.0.0.1:8080` by default with two workers. Each worker can
load PyTorch/PyG, so choose `WEB_CONCURRENCY` according to available memory and
EDA tool concurrency. `AI4EDA_BIND` controls the listener. Neither the Flask
server nor Gunicorn should run with the interactive debugger enabled in a
shared deployment.

## systemd and Nginx examples

The public examples assume `/opt/ai4eda`, a virtual environment at
`/opt/ai4eda/.venv`, and a dedicated `ai4eda` service user. These are placeholders
for your installation; create/select the user and change the paths first.

```bash
cp ai4eda-web.service.example ai4eda-web.service
cp nginx-ai4eda.conf.example nginx-ai4eda.conf
```

Edit the service user, working directory, Python environment path, Nginx host,
static-file path, and upstream address. Keep the upstream port consistent with
`AI4EDA_BIND`. The resulting machine-specific files are ignored by Git.

On a Debian/Ubuntu host with Nginx and systemd, the optional helper
`sudo ./setup_production.sh` installs these customized files, enables the
service, configures the firewall if available, and starts the service. It
replaces the default Nginx site; inspect the script and configuration before
using it on an existing server. Manual installation is also possible:

```bash
sudo cp ai4eda-web.service /etc/systemd/system/
sudo cp nginx-ai4eda.conf /etc/nginx/sites-available/ai4eda
sudo ln -s /etc/nginx/sites-available/ai4eda /etc/nginx/sites-enabled/ai4eda
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now ai4eda-web
sudo systemctl reload nginx
```

The examples do not supply login, TLS, request quotas, or EDA job isolation.
Provide those controls before exposing the app to untrusted users. AI analysis
uses the configured external API provider and that account's quota.

## Operations

```bash
sudo systemctl status ai4eda-web
sudo journalctl -u ai4eda-web -f
sudo systemctl restart ai4eda-web
```

Runtime files live in `uploads/`, `outputs/`, and `logs/`; none belongs in Git.
Restrict `web/.env` to the service user (`chmod 600 web/.env` from the repository
root), and back up local configuration separately from the public source.
