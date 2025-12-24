from fastapi import APIRouter, Request

HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

default_router = APIRouter()

@default_router.api_route("/{full_path:path}", methods=HTTP_METHODS, include_in_schema=False)
async def default_handler(request: Request, full_path: str, handler_name: str = "default"):
    try:
        body = await request.json()
    except:
        body = None
    return dict(
        handler_name=handler_name,
        path=full_path,
        method=request.method,
        query=dict(request.query_params),
        headers=dict(request.headers),
        body=body
    )

from .handlers.AsyncClient import create_handler_from_router as create_handler_from_router_ac
from .handlers.RawResponder import create_handler_from_router as create_handler_from_router_rr
from .handlers.TestClient import create_handler_from_router as create_handler_from_router_tc

def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None, use_httpx: bool = True):
    if use_httpx:
        return create_handler_from_router_ac(router, default_router=default_router)
    else:
        return create_handler_from_router_tc(router, default_router=default_router)
