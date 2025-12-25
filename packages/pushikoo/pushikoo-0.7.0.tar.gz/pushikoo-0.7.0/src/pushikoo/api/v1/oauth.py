from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from pushikoo.api.security import create_access_token
from pushikoo.util.setting import settings

router = APIRouter(prefix="/v1/oauth", tags=["oauth_v1"])
_oauth: OAuth | None = None


def _get_oauth() -> OAuth:
    global _oauth
    if _oauth is None:
        _oauth = OAuth()
        if not settings.SSO_ISSUER_URL:
            return _oauth
        _oauth.register(
            name="sso",
            client_id=settings.SSO_CLIENT_ID,
            client_secret=settings.SSO_CLIENT_SECRET,
            server_metadata_url=f"{settings.SSO_ISSUER_URL.rstrip('/')}/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    return _oauth


@router.get("/login")
async def sso_login(request: Request):
    if not (
        settings.SSO_CLIENT_ID
        and settings.SSO_CLIENT_SECRET
        and settings.SSO_ISSUER_URL
    ):
        raise HTTPException(status_code=503, detail="SSO not configured")
    oauth = _get_oauth()
    client = oauth.create_client("sso")
    if client is None:
        raise HTTPException(status_code=503, detail="SSO client init failed")

    sso_redirect_url = "{}/api/v1/oauth/callback".format(
        settings.BACKEND_BASE_HOST.rstrip("/")
    )
    return await client.authorize_redirect(request, sso_redirect_url)


@router.get("/callback")
async def sso_callback(request: Request):
    if not (
        settings.SSO_CLIENT_ID
        and settings.SSO_CLIENT_SECRET
        and settings.SSO_ISSUER_URL
    ):
        raise HTTPException(status_code=503, detail="SSO not configured")
    oauth = _get_oauth()
    client = oauth.create_client("sso")
    if client is None:
        raise HTTPException(status_code=503, detail="SSO client init failed")

    token = await client.authorize_access_token(request)
    userinfo = token.get("userinfo", {})

    email = userinfo.get("email")
    sub = userinfo.get("sub")

    # TODO:
    # preferred_username = userinfo.get("preferred_username")
    preferred_username = None

    identifier = email or sub or preferred_username
    if not identifier:
        raise HTTPException(status_code=400, detail="Missing user identity from IdP")

    admin_set = {i.strip().lower() for i in settings.ADMIN_USERS}
    allowed = False
    if email and email.lower() in admin_set:
        allowed = True
    if sub and sub.lower() in admin_set:
        allowed = True
    if not allowed:
        raise HTTPException(status_code=403, detail="User not allowed")

    access_token = create_access_token({"sub": identifier, "email": email or ""})

    redirect_url = f"{settings.FRONTEND_BASE_HOST}/login?token={access_token}"
    return RedirectResponse(url=redirect_url)
