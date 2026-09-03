import hashlib
import hmac
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = b"prototype-secret"
state = {
    "attempts": 0,
    "deliveredCount": 0,
    "active": 0,
    "maxConcurrent": 0,
    "lastStatus": None,
}
lock = threading.Lock()


class PartnerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            return self.respond(200)
        if self.path == "/state":
            body = json.dumps(state, separators=(",", ":")).encode()
            return self.respond(200, body, "application/json")
        return self.respond(404)

    def do_POST(self):
        if self.path != "/webhooks":
            return self.respond(404)

        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        timestamp = self.headers.get("X-Inside-Webhook-Timestamp", "")
        actual = self.headers.get("X-Inside-Webhook-Signature", "")
        expected = "v1=" + hmac.new(
            SECRET, timestamp.encode() + b"." + body, hashlib.sha256
        ).hexdigest()

        with lock:
            state["attempts"] += 1
            state["active"] += 1
            state["maxConcurrent"] = max(state["maxConcurrent"], state["active"])
            attempt = state["attempts"]

        time.sleep(0.05)
        with lock:
            state["active"] -= 1
            if not hmac.compare_digest(actual, expected):
                state["lastStatus"] = 401
                return self.respond(401)
            if attempt == 1:
                state["lastStatus"] = 503
                return self.respond(503)
            state["deliveredCount"] += 1
            state["lastStatus"] = 204
        return self.respond(204)

    def respond(self, status, body=b"", content_type="text/plain"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


ThreadingHTTPServer(("0.0.0.0", 8080), PartnerHandler).serve_forever()
