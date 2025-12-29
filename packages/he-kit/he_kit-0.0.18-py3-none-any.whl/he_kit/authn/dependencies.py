from fastapi import Depends, HTTPException, Request, status

from .base import AuthContext, AuthProvider


async def get_auth_provider(request: Request) -> AuthProvider:
    """Return the active auth backend."""
    auth_provider = request.app.state.auth_provider
    return auth_provider


async def get_auth_context(
    request: Request, auth_provider: AuthProvider = Depends(get_auth_provider)
) -> AuthContext:
    """Verify the request's Bearer token using the active auth backend and
    return the auth context.

    """
    token = await auth_provider.get_token(request)

    try:
        return await auth_provider.verify_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


get_auth = get_auth_context
