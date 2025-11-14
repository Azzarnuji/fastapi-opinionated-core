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
- **Plugin lifecycle management** with startup and shutdown hooks
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

The package includes a CLI for generating components:

### Installation
The CLI is automatically available after installing the package:
```bash
fastapi-opinionated new domain NAME [OPTIONS]
fastapi-opinionated new controller DOMAIN_NAME [OPTIONS]
```

### Commands

#### `new domain` - Create a new domain folder structure
```bash
fastapi-opinionated new domain user --bootstrap
```

#### `new controller` - Create a controller inside a domain
```bash
fastapi-opinionated new controller user --crud
```

---

## Plugin System

The framework supports plugins for extending functionality:

```python
from fastapi_opinionated import App

app = App.create()

# Enable plugins (example with SocketPlugin)
# App.enable(SocketPlugin())
```

### Plugin Lifecycle
- `on_ready`: Called after FastAPI app is created but before serving
- `on_shutdown`: Called when the application shuts down
- `on_ready_async`: Async version of on_ready
- `on_shutdown_async`: Async version of on_shutdown

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

---

## Architecture Overview

### App (Core Engine)

`App.create()` handles:

- Initializing the FastAPI application
- Applying the logging configuration
- Discovering controller modules via RouterRegistry
- Loading routes from all controller files under `app/domains`
- Registering routes via FastAPI's APIRouter
- Managing plugin lifecycles with combined lifespan

`App.enable()` handles:

- Enabling plugin instances
- Managing plugin lifecycle hooks
- Registering plugin APIs to the App.plugin namespace

---

### Routing System

- Searches for controllers inside `app/domains` folder recursively
- Automatically discovers routes based on decorators in both class and functional controllers
- Registers endpoints using FastAPI's `APIRouter`
- Supports both class-based and functional-based routing patterns

Example generated route:
```
[GET] /users/ -> UserController.list_users
```

---

### Logging System

The logger includes:

- Color-coded log levels
- Timestamps
- File and line number tracking
- Delta timing for performance monitoring

---

## Configuration

### App.create()

Accepts all FastAPI constructor arguments:

```python
App.create(
    title="My API",
    docs_url="/docs",
    lifespan=my_lifespan
)
```

---

## Contributing

Contributions are welcome!
Please open an issue or submit a pull request.

---

## License

Distributed under the MIT License.
See the `LICENSE` file for more information.
