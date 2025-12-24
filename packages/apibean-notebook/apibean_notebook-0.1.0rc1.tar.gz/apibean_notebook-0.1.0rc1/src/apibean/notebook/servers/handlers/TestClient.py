import asyncio

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import Response
from fastapi.testclient import TestClient

def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None):
    app = FastAPI()
    app.include_router(router)
    if default_router is not None:
        app.include_router(default_router)

    client = TestClient(app)

    async def handler(req: Request) -> Response:
        body = await req.body()
        headers = dict(req.headers)
        url = req.url.path

        # TestClient only sync, so run in thread pool
        def do_request():
            method = req.method.lower()
            fn = getattr(client, method)
            body_args = dict()
            if method in ['post', 'put', 'patch']:
                body_args.update(data=body)
            return fn(url, headers=headers, params=req.query_params, **body_args)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, do_request)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    return handler
