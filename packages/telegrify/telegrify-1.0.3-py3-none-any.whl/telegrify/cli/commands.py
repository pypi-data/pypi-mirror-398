"""Command-line interface for Telegrify"""

from pathlib import Path

import click
import uvicorn
import yaml


@click.group()
@click.version_option(version="1.0.3")
def cli():
    """Telegrify - Simple Telegram Notification Framework"""
    pass


@cli.command()
@click.argument("project_name")
def init(project_name: str):
    """Initialize a new Telegrify project"""
    project_path = Path(project_name)

    if project_path.exists():
        click.echo(f"Error: Directory '{project_name}' already exists", err=True)
        return

    click.echo(f"Creating project: {project_name}")

    project_path.mkdir()
    (project_path / "plugins").mkdir()

    config_content = """# Telegrify Configuration

bot:
  token: "${TELEGRAM_BOT_TOKEN}"
  test_mode: false
  webhook_url: "${WEBHOOK_URL}"  # Your public URL (e.g., https://yourapp.onrender.com)

endpoints:
  - path: "/notify/orders"
    chat_id: "${CHAT_ID}"
    formatter: "plain"

  - path: "/notify/alerts"
    chat_id: "${CHAT_ID}"
    formatter: "markdown"
    parse_mode: "Markdown"

server:
  host: "0.0.0.0"
  port: "${PORT:-8000}"  # Use PORT env var or default to 8000
  api_key: "${API_KEY}"
  cors_origins: ["*"]  # Allow all origins, customize as needed

logging:
  level: "INFO"
"""
    (project_path / "config.yaml").write_text(config_content)

    main_content = '''"""Telegrify server entry point"""

from telegrify import create_app

if __name__ == "__main__":
    import uvicorn

    app = create_app("config.yaml")
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    (project_path / "main.py").write_text(main_content)

    plugin_content = '''"""Example custom formatter plugin"""

from typing import Any
from telegrify import IPlugin


class OrderFormatter(IPlugin):
    """Custom formatter for order notifications"""

    @property
    def name(self) -> str:
        return "order_formatter"

    def format(self, payload: dict[str, Any], config: dict[str, Any]) -> str:
        prefix = config.get("prefix", "🛒 New Order")
        lines = [prefix, ""]

        if "order_id" in payload:
            lines.append(f"Order ID: #{payload['order_id']}")
        if "user" in payload:
            lines.append(f"Customer: {payload['user']}")
        if "total" in payload:
            lines.append(f"Total: ${payload['total']}")
        if "message" in payload:
            lines.append("")
            lines.append(payload["message"])

        return "\\n".join(lines)
'''
    (project_path / "plugins" / "example_formatter.py").write_text(plugin_content)

    # Get current telegrify version from development
    import sys
    import subprocess
    try:
        # Try to get version from current development install
        result = subprocess.run([sys.executable, "-c", "import telegrify; print(telegrify.__version__)"], 
                              capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        if result.returncode == 0:
            current_version = result.stdout.strip()
        else:
            current_version = "0.9.0"  # fallback
    except Exception:
        current_version = "0.9.0"  # fallback

    (project_path / "requirements.txt").write_text(f"telegrify>={current_version}\n")

    readme = f"""# {project_name}

Telegrify notification service

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export API_KEY="your-secret-key"
   ```

3. Edit `config.yaml` with your bot settings

4. Run the server:
   ```bash
   python main.py
   # or
   telegrify run
   ```
"""
    (project_path / "README.md").write_text(readme)

    (project_path / ".env.example").write_text(
        "TELEGRAM_BOT_TOKEN=your_bot_token_here\n"
        "WEBHOOK_URL=https://yourapp.onrender.com\n"
        "CHAT_ID=your_chat_id_here\n"
        "API_KEY=your_api_key_here\n"
        "PORT=8000\n"
    )

    click.echo("✓ Project created successfully!")
    click.echo(f"\nNext steps:")
    click.echo(f"  cd {project_name}")
    click.echo(f"  # Edit config.yaml with your settings")
    click.echo(f"  export TELEGRAM_BOT_TOKEN='your-token'")
    click.echo(f"  telegrify run")


@cli.command()
@click.option("--config", default="config.yaml", help="Path to config file")
@click.option("--host", default=None, help="Override host")
@click.option("--port", default=None, type=int, help="Override port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def run(config: str, host: str, port: int, reload: bool):
    """Run the Telegrify server"""
    if not Path(config).exists():
        click.echo(f"Error: Config file '{config}' not found", err=True)
        click.echo("Run 'telegrify init <project_name>' to create a new project")
        return

    with open(config) as f:
        config_data = yaml.safe_load(f)

    server_config = config_data.get("server", {})
    final_host = host or server_config.get("host", "0.0.0.0")
    final_port = port or server_config.get("port", 8000)

    click.echo(f"Starting Telegrify server on {final_host}:{final_port}")

    uvicorn.run(
        "telegrify.server.app:create_app",
        host=final_host,
        port=final_port,
        reload=reload,
        factory=True,
    )


@cli.command()
@click.option("--config", default="config.yaml", help="Path to config file")
def validate(config: str):
    """Validate configuration file"""
    if not Path(config).exists():
        click.echo(f"Error: Config file '{config}' not found", err=True)
        return

    try:
        from telegrify.core.config import AppConfig

        with open(config) as f:
            config_data = yaml.safe_load(f)

        app_config = AppConfig(**config_data)

        click.echo("✓ Configuration is valid!")
        click.echo(f"\nBot token: {'*' * 20}{app_config.bot.token[-4:]}")
        click.echo(f"Endpoints: {len(app_config.endpoints)}")

        for endpoint in app_config.endpoints:
            click.echo(f"  - {endpoint.path} → {endpoint.chat_id} ({endpoint.formatter})")

    except Exception as e:
        click.echo(f"✗ Configuration error: {e}", err=True)


@cli.group()
def webhook():
    """Manage Telegram webhook"""
    pass


@webhook.command("setup")
@click.option("--config", default="config.yaml", help="Path to config file")
@click.option("--url", default=None, help="Override webhook URL")
def webhook_setup(config: str, url: str):
    """Register webhook with Telegram"""
    import asyncio
    from telegrify.core.config import AppConfig
    from telegrify.core.bot import TelegramBot

    if not Path(config).exists():
        click.echo(f"Error: Config file '{config}' not found", err=True)
        return

    with open(config) as f:
        config_data = yaml.safe_load(f)

    app_config = AppConfig(**config_data)
    webhook_url = url or app_config.bot.webhook_url

    if not webhook_url:
        click.echo("Error: No webhook URL specified. Set bot.webhook_url in config or use --url", err=True)
        return

    full_url = f"{webhook_url.rstrip('/')}{app_config.bot.webhook_path}"
    
    async def setup():
        bot = TelegramBot(app_config.bot.token)
        result = await bot.set_webhook(full_url)
        return result

    result = asyncio.run(setup())
    
    if result.get("ok"):
        click.echo(f"✓ Webhook registered: {full_url}")
    else:
        click.echo(f"✗ Failed: {result.get('description', 'Unknown error')}", err=True)


@webhook.command("info")
@click.option("--config", default="config.yaml", help="Path to config file")
def webhook_info(config: str):
    """Show current webhook status"""
    import asyncio
    from telegrify.core.config import AppConfig
    from telegrify.core.bot import TelegramBot

    if not Path(config).exists():
        click.echo(f"Error: Config file '{config}' not found", err=True)
        return

    with open(config) as f:
        config_data = yaml.safe_load(f)

    app_config = AppConfig(**config_data)

    async def get_info():
        bot = TelegramBot(app_config.bot.token)
        return await bot.get_webhook_info()

    result = asyncio.run(get_info())
    
    if result.get("ok"):
        info = result["result"]
        click.echo(f"URL: {info.get('url') or '(not set)'}")
        click.echo(f"Pending updates: {info.get('pending_update_count', 0)}")
        if info.get("last_error_message"):
            click.echo(f"Last error: {info['last_error_message']}")
    else:
        click.echo(f"✗ Failed: {result.get('description', 'Unknown error')}", err=True)


@webhook.command("delete")
@click.option("--config", default="config.yaml", help="Path to config file")
def webhook_delete(config: str):
    """Remove webhook"""
    import asyncio
    from telegrify.core.config import AppConfig
    from telegrify.core.bot import TelegramBot

    if not Path(config).exists():
        click.echo(f"Error: Config file '{config}' not found", err=True)
        return

    with open(config) as f:
        config_data = yaml.safe_load(f)

    app_config = AppConfig(**config_data)

    async def delete():
        bot = TelegramBot(app_config.bot.token)
        return await bot.delete_webhook()

    result = asyncio.run(delete())
    
    if result.get("ok"):
        click.echo("✓ Webhook deleted")
    else:
        click.echo(f"✗ Failed: {result.get('description', 'Unknown error')}", err=True)


if __name__ == "__main__":
    cli()
