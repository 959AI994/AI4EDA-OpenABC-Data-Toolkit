# 网页版快速开始

在仓库根目录、已激活的 Python 环境中运行：

```bash
python -m pip install -e .
python -m pip install -r web/requirements.txt
cp web/.env.example web/.env
python web/app.py
```

打开 http://127.0.0.1:5000，可以转换电路格式、批量处理文件和调用 ABC 计算 Area/Delay。
ABC、Yosys 的安装要求见仓库根目录 README。

AI Verilog 分析为可选功能：在 `web/.env` 设置自己的 `VOLCENGINE_API_KEY` 和
可用的 `VOLCENGINE_MODEL`，再重启。提交给 AI 分析的 Verilog 会发送到配置的 API 服务；
没有密钥时，格式转换和 ABC 指标计算仍可使用。请勿把 `.env` 提交到 Git。

使用 Gunicorn：

```bash
cd web
./run_production.sh
```

打开 http://127.0.0.1:8080。通过 `web/.env` 中的 `AI4EDA_BIND` 设置监听地址，
`WEB_CONCURRENCY` 设置工作进程数。默认关闭 Debug，并只监听本机。

本应用没有内置登录或任务沙箱，EDA 命令功能应仅供可信用户使用。
完整配置见 [README.md](README.md)，部署模板见 [PRODUCTION.md](PRODUCTION.md)。
