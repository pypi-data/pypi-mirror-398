from secrets import token_hex

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from pushikoo.api.spa import router as sparouter
from pushikoo.api.v1 import oauth_router as v1_oauth_router
from pushikoo.api.v1 import router as v1_router
from pushikoo.util.setting import settings

apirouter = APIRouter(prefix="/api")
apirouter.include_router(v1_oauth_router)
apirouter.include_router(v1_router)

app = FastAPI()
app.include_router(apirouter)
app.include_router(sparouter)


def _get_session_secret() -> str:
    """
    Get a secret key for session middleware.

    - In local environment: use "dev-secret" for convenience
    - In other environments: use SSO_CLIENT_SECRET or generate a random key
      (random key means sessions won't survive restarts, but it's secure)
    """
    if settings.ENVIRONMENT == "local":
        return settings.SSO_CLIENT_SECRET or "dev-secret"
    if settings.SSO_CLIENT_SECRET:
        return settings.SSO_CLIENT_SECRET
    # Generate a random secret - sessions won't persist across restarts but it's secure
    return token_hex(32)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=_get_session_secret(),
)


@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )
