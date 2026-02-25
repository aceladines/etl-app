from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging_config import setup_logging

# Explicit workflow imports — triggers @register_workflow decorators
import app.workflows.definitions.contracts_outbound  # noqa: F401
import app.workflows.definitions.purchase_order_outbound  # noqa: F401
import app.workflows.definitions.example_reference  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="ETL App", version="0.1.0", lifespan=lifespan)

    from app.api.v1.router import v1_router
    application.include_router(v1_router)

    return application


app = create_app()
