from fastapi import FastAPI, Request
from fastapi.routing import APIRouter
from starlette.responses import Response
from starlette.types import Receive, Scope, Send
from typing import Callable, Awaitable


def create_handler_from_router(router: APIRouter) -> Callable[[Request], Awaitable[Response]]:
    # Gắn router vào một FastAPI app tạm thời
    temp_app = FastAPI()
    temp_app.include_router(router)

    async def handler(req: Request) -> Response:
        # Tạo response container
        send_buffer = {}

        async def send(message):
            send_buffer["message"] = message

        # Run app
        responder = temp_app  # FastAPI app là một ASGI app
        await responder(req.scope, req.receive, send)

        # Trích response từ message
        message = send_buffer.get("message")
        if message is None:
            return Response("No response", status_code=500)

        # Nếu là response start, thì ok
        if message["type"] == "http.response.start":
            # Nội dung thực sẽ được gửi qua "http.response.body"
            body_msg = send_buffer.get("body_message")
            body = body_msg["body"] if body_msg else b""
            return Response(content=body, status_code=message["status"])
        elif message["type"] == "http.response.body":
            return Response(content=message["body"], status_code=200)

        return Response("Unhandled response", status_code=500)

    return handler
