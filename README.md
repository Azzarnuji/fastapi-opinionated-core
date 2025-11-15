# FastAPI Opinionated Core

**FastAPI Opinionated Core** is the foundational engine of an opinionated framework built on top of FastAPI.
It provides structured routing, decorator-based controllers, automatic controller discovery, plugin system, CLI tools, and enhanced logging.

⚠️ **Important:**
This package contains only the **core framework logic**.
If you want a ready-to-use application template (with complete folder structure, examples, and boilerplate),
use the official starter project:

👉 https://github.com/Azzarnuji/fastapi-opinionated-starter

The starter repository is built on top of this core package.

---

## Features

- **Decorator-based routing** (`@Controller`, `@Get`, `@Post`, `@Put`, `@Patch`, `@Delete`, `@Http`, etc.)
- **Automatic controller discovery** from domain folders
- **Plugin system** for extending functionality (Socket.IO, EventBus, etc.)
- **Built-in CLI tools** for generating domains and controllers (`fastapi-opinionated new domain`, `fastapi-opinionated new controller`)
- **Enhanced logging** with file and line tracking
- **Opinionated project structure** for consistent FastAPI development
- **Class-based and functional-based controllers** support
- **Plugin lifecycle management** with comprehensive startup and shutdown hooks
- **Duplicate route detection** to prevent conflicts
- **Comprehensive plugin API** with lifecycle hooks and configuration
- Fully **compatible with FastAPI and Uvicorn**

---

## Installation

```bash
pip install fastapi-opinionated-core
```

---

## Quick Start (Using the Core Directly)

### 1. Define a controller

```python
# app/domains/user/controller.py
from fastapi_opinionated.decorators.routing import Controller, Get, Post

@Controller("/users", group="USERS")
class UserController:

    @Get("/")
    def list_users(self):
        return ["john", "jane", "bob"]

    @Post("/create")
    def create_user(self):
        return {"message": "User created successfully"}
```

Or use functional-based controllers:

```python
from fastapi_opinionated.decorators.routing import Get, Post

@Get("/users", group="USERS")
def list_users():
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

@Post("/users", group="USERS")
def create_user(user: dict):
    return {"id": 3, **user}
```

### 2. Create your application

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_opinionated.app import App

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup code here
        print("Starting up the application...")
        yield
        # Shutdown code here
        print("Shutting down the application...")
    except Exception as e:
        print(f"Lifespan error: {e}")

app = App.create(lifespan=lifespan)
```

### 3. Run your application

```bash
fastapi dev main.py --host 0.0.0.0 --port 8003
```

---

## Recommended: Use the Starter Template

To get a complete project structure,
use the official starter template:

👉 https://github.com/Azzarnuji/fastapi-opinionated-starter

It includes:

- A full domain-based folder layout
- Configured development environment
- Predefined controllers and examples
- Ready-to-run application structure
- Proper project organization with class-based and functional-based approaches

---

## CLI Tools

The package includes a comprehensive CLI for generating components and managing plugins:

### Installation
The CLI is automatically available after installing the package:
```bash
fastapi-opinionated new domain NAME [OPTIONS]
fastapi-opinionated new controller DOMAIN_NAME [OPTIONS]
fastapi-opinionated plugins [enable/disable/list]
fastapi-opinionated list [routes/plugins]
```

### Commands

#### `new domain` - Create a new domain folder structure
```bash
fastapi-opinionated new domain user
fastapi-opinionated new domain user --bootstrap  # Creates controllers, services, queues folders
```

#### `new controller` - Create a controller inside a domain
```bash
fastapi-opinionated new controller user
fastapi-opinionated new controller user get_user
fastapi-opinionated new controller user --crud  # Creates CRUD endpoints
```

#### `plugins` - Manage plugin installation and configuration
```bash
fastapi-opinionated plugins list               # List enabled plugins
fastapi-opinionated plugins enable plugin_path # Enable a plugin
fastapi-opinionated plugins disable plugin_path # Disable a plugin
```

#### `list` - List routes and plugin handlers
```bash
fastapi-opinionated list routes                # List all registered routes
fastapi-opinionated list routes --plugin socket # List routes for specific plugin
fastapi-opinionated list plugins               # List plugin handlers
```

---

## Plugin System

The framework supports plugins for extending functionality with a comprehensive lifecycle system:

### Plugin Lifecycle Phases

**Enable Phase (before app startup):**
- `on_pre_enable`: Validation and state preparation
- `on_enable`: Plugin API binding and initialization
- `on_post_enable`: Discovery and post-registration tasks

**Startup Phase (during app startup):**
- `on_plugins_loaded`: After all plugins enabled, before controllers
- `on_controllers_loaded`: After controller discovery
- `on_ready`: After app is created but before serving
- `on_ready_async`: Async version of on_ready
- `on_app_ready`: After all readiness hooks, app is fully ready

**Shutdown Phase (during app shutdown):**
- `on_before_shutdown`: Before main shutdown hooks
- `on_before_shutdown_async`: Async version of on_before_shutdown
- `on_shutdown`: Final shutdown hook
- `on_shutdown_async`: Async version of on_shutdown

### Creating a Plugin

```python
from fastapi_opinionated.shared.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    public_name = "my_plugin"
    command_name = "my_plugin_cmd"
    required_config = False  # Set to True if plugin requires configuration

    @staticmethod
    def _internal(app, fastapi_app, **kwargs):
        # Plugin initialization logic here
        return {"message": "Plugin API"}

    def on_ready(self, app, fastapi_app, plugin_api):
        # Called when app is ready to serve requests
        pass

    async def on_ready_async(self, app, fastapi_app, plugin_api):
        # Async version of on_ready
        pass

# Enable the plugin
from fastapi_opinionated import App
App.configurePlugin(MyPlugin(), some_config="value")
```

### Plugin Configuration

Plugins can be configured before app creation:

```python
from fastapi_opinionated import App
from my_plugin import MyPlugin

App.configurePlugin(MyPlugin(), config_option="value", another_option=123)
app = App.create()
```

---

## Decorators

The routing system provides the following decorators:

- `@Controller(base_path, group=None)` – Marks a class as a controller
- `@Get(path, group=None)` – Defines a GET route
- `@Post(path, group=None)` – Defines a POST route
- `@Put(path, group=None)` – Defines a PUT route
- `@Patch(path, group=None)` – Defines a PATCH route
- `@Delete(path, group=None)` – Defines a DELETE route
- `@Options(path, group=None)` – Defines an OPTIONS route
- `@Head(path, group=None)` – Defines a HEAD route
- `@Http(method, path, group=None)` – Defines custom HTTP methods

All decorated methods are discovered and registered automatically.

### Advanced Decorator Usage

```python
from fastapi_opinionated.decorators.routing import Controller, Get, Post, Http

@Controller("/users", group="USER_MANAGEMENT")
class UserController:

    @Get("/")  # Maps to GET /users/
    async def list_users(self):
        return {"users": []}

    @Post("/create")  # Maps to POST /users/create
    async def create_user(self, user_data: dict):
        return {"message": "User created", "id": 1}

    @Http("PATCH", "/{user_id}")  # Maps to PATCH /users/{user_id}
    async def update_user(self, user_id: int, data: dict):
        return {"message": f"User {user_id} updated", "data": data}
```

### Functional Route Decorators

Functional routes register immediately upon decoration:

```python
from fastapi_opinionated.decorators.routing import Get, Post

@Get("/health", group="HEALTH")
def health_check():
    return {"status": "healthy"}

@Post("/webhook", group="WEBHOOKS")
async def webhook_handler(payload: dict):
    # Process webhook
    return {"message": "Webhook received"}
```

---

## Architecture Overview

### App (Core Engine)

`App.create()` handles:

- Initializing the FastAPI application with user-provided arguments
- Applying the enhanced logging configuration
- Discovering controller modules via RouterRegistry
- Loading routes from all controller files under `app/domains`
- Registering routes via FastAPI's APIRouter
- Managing plugin lifecycles with combined lifespan
- Detecting and preventing duplicate routes
- Setting up exception handlers for plugin errors

`App.configurePlugin()` handles:

- Configuring plugin instances before app creation
- Storing configuration for later use during plugin enablement

### Routing System

- Searches for controllers inside `app/domains` folder recursively
- Automatically discovers routes based on decorators in both class and functional controllers
- Registers endpoints using FastAPI's `APIRouter`
- Supports both class-based and functional-based routing patterns
- Performs duplicate route detection to prevent conflicts
- Organizes routes by file, method, and controller

Example generated route:
```
[GET] /users/ -> UserController.list_users
```

### Registry System

The framework uses multiple registries:

- `RouterRegistry`: Stores both class-based and functional route metadata
- `PluginRegistry`: Manages plugin instances and lifecycle
- `PluginRegistryStore`: Temporary storage for plugin metadata during scanning

### Logging System

The enhanced logger includes:

- Color-coded log levels (INFO=cyan, ERROR=red, etc.)
- Process ID for multi-process debugging
- Timestamps in MM/DD/YYYY format
- File and line number tracking
- Delta timing for performance monitoring (time between consecutive log calls)
- Namespace support for different components

---

## Configuration

### App.create()

Accepts all FastAPI constructor arguments plus opinionated enhancements:

```python
from fastapi_opinionated import App

app = App.create(
    title="My API",
    version="1.0.0",
    description="An example API built with FastAPI Opinionated Core",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=my_lifespan
)
```

### Plugin Configuration

Configure plugins before creating the app:

```python
from fastapi_opinionated import App
from my_plugin import MyPlugin

App.configurePlugin(
    MyPlugin(),
    config_option="value",
    debug_mode=True
)

app = App.create()
```

### Project Structure

The framework expects an opinionated structure under `app/domains/`:

```
app/
└── domains/
    ├── user/
    │   ├── __init__.py
    │   ├── controllers/
    │   │   ├── __init__.py
    │   │   └── user_controller.py
    │   ├── services/
    │   │   ├── __init__.py
    │   │   └── user_service.py
    │   └── queues/
    │       ├── __init__.py
    │       └── user_queue.py
    └── product/
        ├── __init__.py
        └── controllers/
            ├── __init__.py
            └── product_controller.py
```

---

## Duplicate Route Detection

The framework automatically detects and prevents duplicate routes. If you attempt to define the same HTTP method and path combination twice, it will raise an error:

```python
@Controller("/users")
class UserController:
    @Get("/list")  # This works fine
    def list_users(self):
        return []

# This would cause an error if another route with GET /users/list exists
```

The error message includes details about both conflicting routes to help identify the source.

---

## Enhanced Logging

The logging system provides enhanced debugging capabilities:

```python
from fastapi_opinionated.shared.logger import ns_logger

logger = ns_logger("MyController")

logger.info("Processing request")  # Includes [MyController] namespace
logger.error("Something went wrong")  # Includes timing delta from previous log
```

### Log Format

```
[PID] - MM/DD/YYYY, HH:MM:SS AM/PM  LEVEL [Namespace] Message (Delta: X.XXXms)
```

---

## Best Practices

1. **Domain Organization**: Group related functionality in domain folders
2. **Controller Grouping**: Use meaningful group names for documentation organization
3. **Plugin Configuration**: Always configure plugins before app creation
4. **Error Handling**: Leverage the built-in plugin exception handling
5. **Route Naming**: Use consistent path patterns across your application
6. **Lifespan Management**: Use the combined lifespan for startup/shutdown logic

---

## Contributing

Contributions are welcome!
Please open an issue or submit a pull request.

---

## License

Distributed under the MIT License.
See the `LICENSE` file for more information.
