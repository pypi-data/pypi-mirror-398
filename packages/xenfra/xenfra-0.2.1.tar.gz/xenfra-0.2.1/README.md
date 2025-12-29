# 🧘 Xenfra: Infrastructure in Zen Mode

**Xenfra** is a modular infrastructure engine for Python developers that automates the deployment of applications to DigitalOcean. It is designed as a library first, with a beautiful and interactive CLI as the default frontend.

It handles the complexity of server provisioning, context-aware configuration, Dockerization, and automatic HTTPS, allowing you to focus on your code.

## ✨ Core Philosophy

*   **Engine as the Brain**: `xenfra.engine` is the core library. It owns the DigitalOcean API, the SSH "Auto-Heal" retry loops, and the Dockerizer services. It is stateful, robust, and can be imported into any Python project.
*   **Clients as the Face**: Frontends like the default CLI (`xenfra.cli`) are thin, stateless clients responsible only for user interaction.
*   **Zen Mode**: If a server setup fails due to common issues like a locked package manager, the Engine automatically fixes it without exposing raw errors to the user.

## 🚀 Quickstart

Using the Xenfra CLI involves a simple workflow: **Configure**, **Initialize**, and then **Deploy & Manage**.

### 1. Configure

Xenfra needs your DigitalOcean API token to manage infrastructure on your behalf. Export it as an environment variable:

```bash
export DIGITAL_OCEAN_TOKEN="dop_v1_your_secret_token_here"
```

### 2. Initialize

Navigate to your project's root directory and run the `init` command. This command scans your project, asks a few questions, and creates a `xenfra.yaml` configuration file.

```bash
xenfra init
```
You should review the generated `xenfra.yaml` and commit it to your repository.

### 3. Deploy & Manage

Once your project is initialized, you can use the following commands to manage your application:

*   **`xenfra deploy`**: Deploys your application based on the settings in `xenfra.yaml`.
*   **`xenfra list`**: Instantly lists all your deployed projects from a local cache.
    *   Use `xenfra list --refresh` to force a sync with your cloud provider.
*   **`xenfra logs`**: Streams real-time logs from a selected project.
*   **`xenfra destroy`**: Decommissions and deletes a deployed project.


## 📦 Supported Frameworks & Features

*   **Smart Context Detection**: Automatically detects your package manager (`uv` or `pip`).
*   **Automatic Dockerization**: If a web framework is detected (`FastAPI`, `Flask`), Xenfra will:
    *   Generate a `Dockerfile`, `docker-compose.yml`, and `Caddyfile`.
    *   Deploy your application as a container.
    *   Configure **Caddy** as a reverse proxy with **automatic HTTPS**.

## 🤝 Contributing

Contributions are welcome! Please check our `CONTRIBUTING.md` for more details.

## 📄 Created by DevHusnainAi