# FastAPI Opinionated Core

**FastAPI Opinionated Core** is the foundational engine of an opinionated framework built on top of FastAPI.  
It provides structured routing, decorator-based controllers, automatic controller discovery, and enhanced logging.

⚠️ **Important:**  
This package contains only the **core framework logic**.  
If you want a ready-to-use application template (with complete folder structure, examples, and boilerplate),  
use the official starter project:

👉 https://github.com/Azzarnuji/fastapi-opinionated-starter

The starter repository is built on top of this core package.

---

## Features

- **Decorator-based routing** (`@Controller`, `@Get`, `@Post`, etc.)
- **Automatic controller discovery** from domain folders
- **Enhanced logging** (colors, timestamps, PID, file references, delta timing)
- **Opinionated project structure** for consistent FastAPI development
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

@Controller("/users")
class UserController:

    @Get("/")
    def list_users(self):
        return ["john", "jane", "bob"]

    @Post("/create")
    def create_user(self):
        return {"message": "User created successfully"}
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
        yield
        # Shutdown code here
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

---

## Decorators

The routing system provides the following decorators:

- `@Controller(base_path)` – Marks a class as a controller
- `@Get(path)` – Defines a GET route
- `@Post(path)` – Defines a POST route
- `@Http(method, path)` – Defines custom HTTP methods

All decorated methods are discovered and registered automatically.

---

## Architecture Overview

### App (Core Engine)

`App.create()` handles:

- Initializing the FastAPI application
- Applying the custom logging configuration
- Discovering controller modules
- Registering routes via FastAPI

`App.listen()` [Not Completed] handles:

- Starting the Uvicorn server
- Passing through all Uvicorn configuration parameters

---

### Routing System

- Searches for controllers inside domain folders
- Automatically discovers routes based on decorators
- Registers endpoints using FastAPI’s `APIRouter`

Example generated route:

```
[GET] /users/ -> UserController.list_users
```

---

### Logging System

The custom logger includes:

- Color-coded log levels
- Process ID (PID)
- Timestamps
- Delta time measurement
- File and line number tracking

Ideal for debugging and profiling.

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

### App.listen() [Not Completed]

Accepts all Uvicorn parameters:

```python
App.listen(app, reload=True, host="0.0.0.0", port=8000)
```

---

## Contributing

Contributions are welcome!  
Please open an issue or submit a pull request.

---

## License

Distributed under the MIT License.  
See the `LICENSE` file for more information.
