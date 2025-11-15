from fastapi_opinionated.app import App
import typer
import os
import importlib.util

# ---------- COLOR CONFIG (SAMA PERSIS DENGAN LOGGER) ----------
RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[37m",     # white
    "INFO": "\033[36m",      # cyan
    "WARNING": "\033[33m",   # yellow
    "ERROR": "\033[31m",     # red
    "CRITICAL": "\033[41m",
}


def c(text, level="INFO"):
    """Colorize text based on log-level color scheme."""
    return COLORS.get(level, COLORS["INFO"]) + text + RESET


# ===========================================================
# LIST CLI
# ===========================================================
list_cli = typer.TypedHelpFormatter if hasattr(typer, 'TypedHelpFormatter') else typer.Typer
list_cli = typer.Typer(help="List utilities")


def load_enabled_plugins():
    CONFIG_FILE = ".fastapi_opinionated/enabled_plugins.py"
    if not os.path.exists(CONFIG_FILE):
        return []

    spec = importlib.util.spec_from_file_location("enabled_plugins_module", CONFIG_FILE)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)

    return getattr(cfg, "ENABLED_PLUGINS", [])


# ===========================================================
# LIST PLUGINS
# ===========================================================
@list_cli.command("plugins")
def list_plugins():
    enabled = load_enabled_plugins()

    if not enabled:
        typer.echo(c("No plugins enabled.", "WARNING"))
        raise typer.Exit()

    typer.echo(c("\nEnabled Plugins:\n", "INFO"))
    for full_path in enabled:
        _, class_name = full_path.rsplit(".", 1)
        typer.echo(f"- {c(class_name, 'DEBUG')}")


# ===========================================================
# LIST HANDLERS (METADATA MODE)
# ===========================================================
@list_cli.command("handlers")
def list_handlers(
    plugin: str = typer.Option(None, "--plugin", "-p", help="Show handlers only for a specific plugin"),
    show_routes: bool = typer.Option(False, "--routes", "-r", help="Show only routes and skip plugin handlers"),
):
    """
    List plugin handlers OR routes based on user selection.
    """

    # -----------------------------
    # ENABLE METADATA SCANNING MODE
    # -----------------------------
    from fastapi_opinionated.registry.plugin import PluginRegistry
    PluginRegistry.metadata_scanning = True

    from fastapi_opinionated.app import App
    from fastapi_opinionated.routing.registry import RouterRegistry
    from fastapi_opinionated.registry.plugin_store import PluginRegistryStore

    App._load_enabled_plugins(metadata_only=True)
    RouterRegistry.load()

    registry = PluginRegistryStore.registries
    routes = RouterRegistry.get_all_routes()

    # ======================================================
    # MODE — ROUTES ONLY (GROUPED BY FILE)
    # ======================================================
    if show_routes:
        typer.echo(c("\n=== Loaded Routes (By File) ===\n", "INFO"))

        if not routes:
            typer.echo(c("No routes found.", "WARNING"))
            return

        # PRIORITY ORDER
        HTTP_ORDER = {
            "GET": 1,
            "POST": 2,
            "PUT": 3,
            "PATCH": 4,
            "DELETE": 5,
        }

        # Group routes by file_path
        grouped = {}
        for r in routes:
            file_path = r.get("file_path") or "<no-file>"

            # normalize relative path
            try:
                file_path = os.path.relpath(file_path, os.getcwd())
            except:
                pass

            grouped.setdefault(file_path, []).append(r)

        # Print grouping
        for file_path, file_routes in grouped.items():
            typer.echo(c(file_path, "WARNING"))

            # SORT ROUTES BY HTTP METHOD PRIORITY
            file_routes = sorted(
                file_routes,
                key=lambda r: HTTP_ORDER.get(r["http_method"].upper(), 999)
            )

            for r in file_routes:
                method = c(r["http_method"], "INFO")
                path = c(r["path"], "DEBUG")
                typer.echo(f"  [{method}] {path}")

            typer.echo()

        return


    # ======================================================
    # MODE — PLUGIN HANDLERS
    # ======================================================
    typer.echo(c("\n=== Plugin Handlers ===\n", "INFO"))

    if not registry:
        typer.echo(c("No plugin handlers found.", "WARNING"))
        return

    for plugin_name, sections in registry.items():

        # FILTER BY PLUGIN NAME
        if plugin and plugin_name != plugin:
            continue

        typer.echo(c(plugin_name, "DEBUG"))

        for section_name, items in sections.items():
            typer.echo("  " + c(f"{section_name}:", "WARNING"))

            for item in items:
                typer.echo("    - " + c(f"event: {item.get('event')}", "DEBUG"))

                if "namespace" in item:
                    typer.echo("      " + c(f"namespace: {item['namespace']}", "DEBUG"))

                handler = item.get("handler")
                if handler:
                    typer.echo("      " + c(f"handler: {handler.__name__}", "DEBUG"))

                    # FILE PATH
                    file_path = handler.__code__.co_filename
                    try:
                        file_path = os.path.relpath(file_path, os.getcwd())
                    except:
                        pass

                    typer.echo("      " + c(f"file: {file_path}", "DEBUG"))

                typer.echo()

        typer.echo()

    typer.echo()
