import typer
import os
from fastapi_opinionated.shared.logger import logger

new = typer.Typer(help="Generate new components")


def ensure_domains_folder():
    """Ensure 'app/domains' exists."""
    if not os.path.exists("app/domains"):
        os.makedirs("app/domains", exist_ok=True)


def to_pascal(name: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    clean = name.replace("-", "_")
    return "".join(word.capitalize() for word in clean.split("_"))


def to_group(name: str) -> str:
    """Convert snake_case or kebab-case to UPPER_SNAKE_CASE."""
    clean = name.replace("-", "_")
    return clean.upper()


@new.command("domain")
def generate_domain(
    name: str,
    bootstrap: bool = typer.Option(
        None,
        "--bootstrap",
        help="Generate bootstrapped folders: controllers, services, queues."
    )
):
    """
    Create a new domain folder structure.

    Example:
        fastapi-opinionated new domain user
        fastapi-opinionated new domain user --bootstrap
    """

    ensure_domains_folder()

    bootstrapped_folders = ["controllers", "services", "queues"]

    domain_path = f"app/domains/{name}"

    # Cek domain sudah ada
    if os.path.exists(domain_path):
        logger.info(f"❌ Domain '{name}' already exists.")
        raise typer.Exit()

    # Buat domain folder
    os.makedirs(domain_path, exist_ok=True)

    # Buat file __init__.py
    open(f"{domain_path}/__init__.py", "w").close()

    # Kalau flag tidak diberikan → prompt user
    if bootstrap is None:
        bootstrap = typer.confirm(
            f"Generate bootstrapped folders for domain '{name}'?",
            default=True
        )

    # Kalau generate bootstrapped folders
    if bootstrap:
        for folder in bootstrapped_folders:
            path = f"{domain_path}/{folder}"
            os.makedirs(path, exist_ok=True)
            open(f"{path}/__init__.py", "w").close()

        logger.info(f"📦 Bootstrapped folders created: {bootstrapped_folders}")

    logger.info(f"🎉 Domain '{name}' created successfully at {domain_path}")



@new.command("controller")
def generate_controller(
    domain_name: str,
    controller_name: str = "controller",
    crud: bool = typer.Option(
        None,
        "--crud",
        help="Generate CRUD endpoints (list, create, update, delete)."
    )
):
    """
    Create a controller inside a domain.

    Examples:
        fastapi-opinionated new controller user
        fastapi-opinionated new controller user get_user
        fastapi-opinionated new controller user --crud
    """

    ensure_domains_folder()

    domain_path = f"app/domains/{domain_name}"
    controllers_dir = f"{domain_path}/controllers"
    controller_path = f"{controllers_dir}/{controller_name}.py"

    # Validate domain
    if not os.path.exists(domain_path):
        logger.info(f"❌ Domain '{domain_name}' does not exist. Create it first:")
        logger.info(f"   fastapi-opinionated new domain {domain_name}")
        raise typer.Exit()

    # Prevent duplicates
    if os.path.exists(controller_path):
        logger.info(f"❌ Controller already exists at {controller_path}")
        raise typer.Exit()

    os.makedirs(controllers_dir, exist_ok=True)

    # Determine class name
    if controller_name == "controller":
        class_name = f"{to_pascal(domain_name)}Controller"  # e.g. UserController
        base_path = f"/{domain_name}"
        group = to_group(domain_name)
    else:
        class_name = f"{to_pascal(controller_name)}Controller"  # e.g. GetUserController
        base_path = f"/{controller_name}"
        group = to_group(controller_name)

    # Ask CRUD confirmation only if flag not passed
    if crud is None:
        crud = typer.confirm("Generate CRUD endpoints?", default=False)

    # Templates
    base_template = f"""from fastapi_opinionated.decorators.routing import Controller, Get, Post


@Controller("{base_path}", group="{group}")
class {class_name}:
    pass
"""

    crud_template = f"""from fastapi_opinionated.decorators.routing import Controller, Get, Post, Put, Patch, Delete


@Controller("{base_path}", group="{group}")
class {class_name}:

    @Get("/")
    async def list(self):
        return {{"message": "List {domain_name}"}}

    @Post("/create")
    async def create(self):
        return {{"message": "{class_name} created successfully"}}

    @Put("/update")
    async def update(self):
        return {{"message": "{class_name} updated successfully"}}
        
    @Patch("/partial_update")
    async def partial_update(self):
        return {{"message": "{class_name} updated successfully"}}

    @Delete("/delete")
    async def delete(self):
        return {{"message": "{class_name} deleted successfully"}}
"""

    template = crud_template if crud else base_template

    # Write file
    with open(controller_path, "w") as f:
        f.write(template)

    logger.info(f"🎉 Controller created at {controller_path} (CRUD={crud})")