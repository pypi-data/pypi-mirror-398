from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

import logging
_logger = logging.getLogger(__name__)

class PrettyJSONMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Chỉ xử lý nếu có header yêu cầu pretty JSON
        if request.headers.get("X-Pretty-Json-Response"):
            _logger.debug("Header[X-Pretty-Json-Response] is effected")
            _logger.debug(f"Type of response: {type(response)}")

            # Chỉ xử lý nếu Content-Type là JSON
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:

                # Đọc body hiện tại từ response
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                _logger.debug(f"Response body has read")

                try:
                    # Parse JSON → format lại → encode lại
                    raw_data = json.loads(body)
                    pretty_body = json.dumps(raw_data, indent=4, ensure_ascii=False)
                    new_body = pretty_body.encode("utf-8")
                    _logger.debug(f"Parsing body is ok")
                except Exception as exc:
                    # Nếu không phải JSON hoặc lỗi parse → giữ nguyên
                    _logger.debug(f"Parsing body error: {exc}")
                    return response

                # Trả lại response mới với body đã format
                _logger.debug(f"Return new formatted Response")
                return Response(
                    content=new_body,
                    status_code=response.status_code,
                    headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
                    media_type="application/json"
                )

        return response
