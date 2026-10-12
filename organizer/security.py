"""Browser boundary for a single-user loopback application; not user authentication."""


class LocalBrowserBoundary:
    def __init__(self, app, port):
        self.app = app
        self.host = f"127.0.0.1:{port}"
        self.origin = f"http://{self.host}"
        self.csp = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; "
            f"connect-src 'self' ws://{self.host}; "
            "object-src 'none'; frame-src 'none'; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'"
        )

    async def __call__(self, scope, receive, send):
        if scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)
        headers = {key.decode().lower(): value.decode() for key, value in scope["headers"]}
        blocked = (
            headers.get("host") != self.host
            or headers.get("origin", self.origin) != self.origin
            or headers.get("sec-fetch-site") == "cross-site"
        )
        if blocked:
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            else:
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [(b"content-type", b"text/plain")],
                    }
                )
                await send({"type": "http.response.body", "body": b"Local same-origin access only."})
            return

        async def secured_send(message):
            if message["type"] == "http.response.start":
                message = {
                    **message,
                    "headers": list(message.get("headers", []))
                    + [
                        (b"content-security-policy", self.csp.encode()),
                        (b"x-content-type-options", b"nosniff"),
                        (b"referrer-policy", b"no-referrer"),
                        (b"x-frame-options", b"DENY"),
                        (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                    ],
                }
            await send(message)

        await self.app(scope, receive, secured_send)
