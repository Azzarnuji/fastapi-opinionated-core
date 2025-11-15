import typer
import os
import importlib
from fastapi_opinionated.utils.import_string import import_string

plugins_cli = typer.Typer(help="Manage FastAPI Opinionated plugins.")


CONFIG_DIR = ".fastapi_opinionated"
CONFIG_FILE = os.path.join(CONFIG_DIR, "enabled_plugins.py")


def ensure_config_exists():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            f.write("ENABLED_PLUGINS = []\n")


def load_enabled_plugins():
    ensure_config_exists()

    cfg = {}
    try:
        exec(open(CONFIG_FILE).read(), cfg)
    except Exception:
        cfg["ENABLED_PLUGINS"] = []

    return cfg.get("ENABLED_PLUGINS", [])


def write_enabled_plugins(plugin_list):
    ensure_config_exists()

    with open(CONFIG_FILE, "w") as f:
        f.write("ENABLED_PLUGINS = [\n")
        for item in sorted(plugin_list):
            f.write(f'    "{item}",\n')
        f.write("]\n")


def validate_plugin_path(path: str):
    """
    Validates import path like:
        fastapi_opinionated_socket.plugin.SocketPlugin
    """
    try:
        import_string(path)
        return True
    except Exception:
        return False


# ===========================================
# COMMAND: LIST
# ===========================================
@plugins_cli.command("list")
def list_plugins():
    """
    List all enabled plugins.
    """
    enabled = load_enabled_plugins()

    if not enabled:
        typer.echo("No plugins enabled.")
        raise typer.Exit()

    typer.echo("Enabled plugins:")
    for p in enabled:
        typer.echo(f"  - {p}")


# ===========================================
# COMMAND: ENABLE
# ===========================================
@plugins_cli.command("enable")
def enable_plugin(plugin_path: str):
    """
    Enable a plugin by its import path.
    Automatically installs the plugin.
    Supports development-mode local installs.
    """

    parts = plugin_path.split(".")
    module_root = parts[0]  # example: fastapi_opinionated_socket
    package_name = module_root.replace("_", "-")  # fastapi-opinionated-socket

    # =======================================================
    # FASE 1 — Cek folder plugin lokal (development mode)
    # =======================================================
    local_path_candidates = [
        f"./{package_name}",                 # ./fastapi-opinionated-socket
        f"./{package_name}/",                # with trailing slash
        f"../{package_name}",                # parent folder
        f"../{package_name}/",
    ]

    local_plugin_path = None

    for p in local_path_candidates:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "pyproject.toml")):
            local_plugin_path = os.path.abspath(p)
            break

    # =======================================================
    # FASE 2 — Try import first
    # =======================================================
    if not validate_plugin_path(plugin_path):

        # =====================================================
        # DEVELOPMENT MODE INSTALL
        # =====================================================
        if local_plugin_path:
            typer.echo(f"Detected local plugin directory: {local_plugin_path}")

            # Determine if root project uses Poetry
            use_poetry = False
            if os.path.exists("pyproject.toml"):
                try:
                    with open("pyproject.toml", "r") as f:
                        if "[tool.poetry]" in f.read():
                            use_poetry = True
                except Exception:
                    pass

            import subprocess, sys

            try:
                if use_poetry:
                    typer.echo(f"Installing local plugin (editable) via Poetry...")
                    subprocess.check_call(["poetry", "add", local_plugin_path, "--editable"])
                else:
                    typer.echo(f"Installing local plugin (editable) via pip...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", local_plugin_path])

                typer.echo(f"Successfully installed local plugin: {local_plugin_path}")

            except Exception as e:
                typer.echo(f"Failed to install local plugin: {e}")
                raise typer.Exit(1)

        else:
            # =====================================================
            # NORMAL MODE (PyPI install)
            # =====================================================
            typer.echo(f"Plugin not installed. Installing '{package_name}' ...")

            # detect poetry
            use_poetry = False
            if os.path.exists("pyproject.toml"):
                with open("pyproject.toml") as f:
                    if "[tool.poetry]" in f.read():
                        use_poetry = True

            import subprocess, sys

            try:
                if use_poetry:
                    typer.echo(f"Installing with Poetry...")
                    subprocess.check_call(["poetry", "add", package_name])
                else:
                    typer.echo(f"Installing with pip...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

                typer.echo(f"Successfully installed '{package_name}'")

            except Exception as e:
                typer.echo(f"Failed installing plugin: {e}")
                raise typer.Exit(1)

    # =======================================================
    # FASE 4 — Register in enabled_plugins
    # =======================================================
    enabled = load_enabled_plugins()
    if plugin_path not in enabled:
        enabled.append(plugin_path)
    write_enabled_plugins(enabled)

    typer.echo(f"Enabled plugin: {plugin_path}")



# ===========================================
# COMMAND: DISABLE
# ===========================================
@plugins_cli.command("disable")
def disable_plugin(plugin_path: str = typer.Argument(..., help="Full import path to plugin class")):
    """
    Disable a plugin by its import path.
    """

    enabled = load_enabled_plugins()

    if plugin_path not in enabled:
        typer.echo(f"Plugin not enabled: {plugin_path}")
        raise typer.Exit()

    enabled.remove(plugin_path)
    write_enabled_plugins(enabled)

    typer.echo(f"Disabled plugin: {plugin_path}")
