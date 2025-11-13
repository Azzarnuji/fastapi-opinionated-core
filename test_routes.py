from fastapi_opinionated.decorators.routing import Controller, Get, Post
from fastapi_opinionated.routing.registry import RouterRegistry
@Controller("/users")
class UserController:

    @Get("/")
    def list(self):
        return ["john", "budi"]

    @Post("/create")
    def create(self):
        return {"ok": True}


if __name__ == "__main__":
    routes = RouterRegistry.get_routes()
    for r in routes:
        print(f"[{r['http_method']}] {r['path']} -> {r['handler']}")