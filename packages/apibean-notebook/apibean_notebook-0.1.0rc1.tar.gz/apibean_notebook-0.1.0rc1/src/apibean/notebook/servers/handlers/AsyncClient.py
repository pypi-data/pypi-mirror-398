import httpx
from fastapi import APIRouter, FastAPI, Request, Response

METHODS_WITH_BODY = {"POST", "PUT", "PATCH", "DELETE"}    

def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None):
    app = FastAPI()
    app.include_router(router)
    if default_router is not None:
        app.include_router(default_router)

    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
        base_url="http://internal")  # httpx >= 0.23

    async def handler(request: Request) -> Response:
        method = request.method.upper()
        opts = dict(
            method = method,
            url = request.url.path,
            headers = dict(request.headers),
            params = dict(request.query_params),
        )
        if method in METHODS_WITH_BODY:
            body = await request.body()
            opts.update(content=body)
    
        resp = await client.request(**opts)
    
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )

    return handler
