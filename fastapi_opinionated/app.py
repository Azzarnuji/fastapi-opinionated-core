from fastapi import FastAPI
from fastapi_opinionated.shared.logger import setup_logging, logger
from fastapi_opinionated.routing.registry import RouterRegistry


class App:
    @classmethod
    def create(cls, **fastapi_kwargs):
        """
        """

        # 1. Setup custom logger lebih awal
        setup_logging()
        logger.info("Custom logger initialized")

        # 2. Inisialisasi FastAPI dengan semua parameter yg dikirim user
        app = FastAPI(**fastapi_kwargs)

        # 3. Autoload semua controller
        RouterRegistry.load()

        # 4. Buat router dan include ke FastAPI
        router = RouterRegistry.as_fastapi_router()
        app.include_router(router)
        logger.info("Application started successfully")
        return app
    
    @classmethod
    def listen(cls, app, **uvicorn_kwargs):
        import uvicorn

        # If reload is enabled, app MUST be import string
        if uvicorn_kwargs.get("reload") and not isinstance(app, str):
            raise RuntimeError(
                "Reload requires passing the app as an import string, e.g. 'main:app'"
            )

        if isinstance(app, str):
            target = app  # import string
        else:
            target = app  # direct object (no reload)

        # Override log_config unless user provides one
        if "log_config" not in uvicorn_kwargs:
            uvicorn_kwargs["log_config"] = None

        uvicorn.run(target, **uvicorn_kwargs)
