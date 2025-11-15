import typer
import os
import sys
import subprocess
from fastapi_opinionated.utils.import_string import import_string

plugins_cli = typer.Typer(help="Manage FastAPI Opinionated plugins.")

# ---------- COLOR CONFIG ----------
RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[37m",
    "INFO": "\033[36m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m",
    "SUCCESS": "\033[32m",
}

def c(text, level="INFO"):
    return COLORS.get(level, COLORS["INFO"]) + text + RESET

CONFIG_DIR = ".fastapi_opinionated"
CONFIG_FILE = os.path.join(CONFIG_DIR, "enabled_plugins.py")


# ===========================================================
# CONFIG MANAGEMENT
# ===========================================================
def ensure_config_exists():
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
    try:
        import_string(path)
        return True
    except Exception:
        return False


# ===========================================================
# COMMAND: LIST
# ===========================================================
@plugins_cli.command("list")
def list_plugins():
    enabled = load_enabled_plugins()
    if not enabled:
        typer.echo(c("No plugins enabled.", "WARNING"))
        raise typer.Exit()

    typer.echo(c("Enabled plugins:", "INFO"))
    for p in enabled:
        typer.echo("  - " + p)


# ===========================================================
# COMMAND: ENABLE
# ===========================================================
@plugins_cli.command("enable")
def enable_plugin(plugin_path: str):
    parts = plugin_path.split(".")
    module_root = parts[0]
    package_name = module_root.replace("_", "-")

    # LOCAL SAFE
    local_candidates = [
        f"./{package_name}",
        f"../{package_name}",
        f"./{package_name}/",
        f"../{package_name}/",
    ]

    local_plugin_path = None
    for p in local_candidates:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "pyproject.toml")):
            local_plugin_path = os.path.abspath(p)
            break

    # Try import first
    if not validate_plugin_path(plugin_path):

        # DEV MODE
        if local_plugin_path:
            typer.echo(c(f"Detected local plugin directory: {local_plugin_path}", "INFO"))

            use_poetry = False
            if os.path.exists("pyproject.toml"):
                with open("pyproject.toml") as f:
                    if "[tool.poetry]" in f.read():
                        use_poetry = True

            try:
                if use_poetry:
                    typer.echo(c("Installing local plugin (editable) via Poetry...", "INFO"))
                    subprocess.check_call(["poetry", "add", local_plugin_path, "--editable"])
                else:
                    typer.echo(c("Installing local plugin (editable) via pip...", "INFO"))
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", local_plugin_path])

                typer.echo(c(f"Successfully installed local plugin: {local_plugin_path}", "SUCCESS"))

            except Exception as e:
                typer.echo(c(f"Failed installing local plugin: {e}", "ERROR"))
                raise typer.Exit(1)

        else:
            typer.echo(c(f"Plugin not installed. Installing '{package_name}'...", "INFO"))

            use_poetry = False
            if os.path.exists("pyproject.toml"):
                with open("pyproject.toml") as f:
                    if "[tool.poetry]" in f.read():
                        use_poetry = True

            try:
                if use_poetry:
                    typer.echo(c("Installing with Poetry...", "INFO"))
                    subprocess.check_call(["poetry", "add", package_name])
                else:
                    typer.echo(c("Installing with pip...", "INFO"))
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

                typer.echo(c(f"Successfully installed '{package_name}'", "SUCCESS"))

            except Exception as e:
                typer.echo(c(f"Failed installing plugin: {e}", "ERROR"))
                raise typer.Exit(1)

    # REGISTER
    enabled = load_enabled_plugins()
    if plugin_path not in enabled:
        enabled.append(plugin_path)
        write_enabled_plugins(enabled)

    typer.echo(c(f"Enabled plugin: {plugin_path}", "SUCCESS"))


    # ===========================================================
    # AUTO-PUBLISH PROMPT
    # ===========================================================
    try:
        PluginClass = import_string(plugin_path)
        plugin_instance = PluginClass()
    except Exception:
        typer.echo(c("⚠ Cannot import plugin to check publishability.", "WARNING"))
        return

    if getattr(plugin_instance, "publishable", False):
        typer.echo("")
        typer.echo(c(f"📦 Plugin '{plugin_instance.public_name}' is publishable.", "INFO"))

        do_publish = typer.confirm("Do you want to publish plugin assets now?", default=False)

        if do_publish:
            typer.echo(c("Publishing plugin assets...", "INFO"))
            from fastapi_opinionated.cli.commands.plugins import publish_plugin
            publish_plugin(plugin_path)
        else:
            typer.echo(c("Skipping publish. You can publish later with:", "WARNING"))
            typer.echo("  fastapi-opinionated plugins publish " + plugin_path)


# ===========================================================
# COMMAND: PUBLISH
# ===========================================================
@plugins_cli.command("publish")
def publish_plugin(plugin_path: str, force: bool = typer.Option(False, "--force", "-f", help="Force re-publish of all assets")):
    enabled = load_enabled_plugins()
    if plugin_path not in enabled:
        typer.echo(c(f"Plugin '{plugin_path}' is not enabled.", "ERROR"))
        typer.echo("Enable first:")
        typer.echo("  fastapi-opinionated plugins enable " + plugin_path)
        raise typer.Exit(1)

    # LOCAL SAFE
    parts = plugin_path.split(".")
    module_root = parts[0]
    package_name = module_root.replace("_", "-")

    local_candidates = [
        f"./{package_name}",
        f"../{package_name}",
        f"./{package_name}/",
        f"../{package_name}/",
    ]

    local_plugin_path = None
    for p in local_candidates:
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "pyproject.toml")):
            local_plugin_path = os.path.abspath(p)
            break

    if local_plugin_path:
        typer.echo(c(f"Using LOCAL plugin folder: {local_plugin_path}", "INFO"))
        if local_plugin_path not in sys.path:
            sys.path.insert(0, local_plugin_path)

    # IMPORT
    try:
        PluginClass = import_string(plugin_path)
        plugin_instance = PluginClass()
    except Exception as e:
        typer.echo(c(f"Failed to import plugin: {e}", "ERROR"))
        raise typer.Exit(1)

    if not getattr(plugin_instance, "publishable", False):
        typer.echo(c(f"Plugin '{plugin_instance.public_name}' is NOT publishable.", "WARNING"))
        raise typer.Exit(0)

    # LOAD METADATA
    meta = plugin_instance.get_publish_metadata()
    domain = meta.domain
    overwrite_all = meta.overwrite
    overwrite_rules = meta.overwrite_rules or {}

    typer.echo(c(f"📦 Publishing plugin assets for domain: {domain}", "INFO"))

    import shutil

    plugin_root = PluginClass.get_plugin_root()
    publish_src = os.path.join(plugin_root, plugin_instance.publish_dir)

    if not os.path.exists(publish_src):
        typer.echo(c(f"Missing publish directory: {publish_src}", "ERROR"))
        raise typer.Exit(1)

    project_domain_root = os.path.join("app", "domains", domain)
    os.makedirs(project_domain_root, exist_ok=True)

    copied = []
    skipped = []

    for root, dirs, files in os.walk(publish_src):
        # ---------------------------------------------
        # EXCLUDE publish.py (metadata-only file)
        # ---------------------------------------------
        files = [f for f in files if f != "publish.py"]

        rel = os.path.relpath(root, publish_src)
        target = os.path.join(project_domain_root, rel)
        os.makedirs(target, exist_ok=True)

        for file in files:
            src = os.path.join(root, file)
            dst = os.path.join(target, file)

            rule = overwrite_rules.get(file)
            allow = overwrite_all or rule is True or force

            if os.path.exists(dst) and not allow:
                skipped.append(dst)
                continue

            shutil.copy2(src, dst)
            copied.append(dst)


    typer.echo("")
    typer.echo(c("✨ Publish Summary", "SUCCESS"))

    if copied:
        typer.echo(c("Copied:", "INFO"))
        for f in copied:
            typer.echo("  - " + f)

    if skipped:
        typer.echo("")
        typer.echo(c("Skipped:", "WARNING"))
        for f in skipped:
            typer.echo("  - " + f)

    typer.echo("")
    typer.echo(c("✔ Publish completed.", "SUCCESS"))
