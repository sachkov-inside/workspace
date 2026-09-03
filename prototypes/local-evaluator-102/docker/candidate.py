import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PARTNER_URL = os.environ["PARTNER_URL"]
FIXTURE_MODE = os.environ.get("PROTOTYPE_FIXTURE_MODE", "pass")
executor = ThreadPoolExecutor(max_workers=int(os.environ["MAX_CONCURRENT_PARTNER_CALLS"]))


def deliver(event):
    body = json.dumps(event, separators=(",", ":")).encode()
    secret = b"wrong-secret" if FIXTURE_MODE == "bad-signature" else b"prototype-secret"
    for attempt in range(2):
        timestamp = str(int(time.time()))
        signature = "v1=" + hmac.new(
            secret, timestamp.encode() + b"." + body, hashlib.sha256
        ).hexdigest()
        request = urllib.request.Request(
            PARTNER_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Inside-Webhook-Timestamp": timestamp,
                "X-Inside-Webhook-Signature": signature,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=1) as response:
                status = response.status
        except urllib.error.HTTPError as error:
            status = error.code
        except (TimeoutError, urllib.error.URLError):
            status = 503

        if status == 204 or status < 500:
            return
        if attempt == 0:
            time.sleep(0.2)


class CandidateHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            return self.respond(200)
        return self.respond(404)

    def do_POST(self):
        if self.path != "/orders/status":
            return self.respond(404)
        event = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        executor.submit(deliver, event)
        return self.respond(202)

    def respond(self, status):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *_):
        pass


ThreadingHTTPServer(("0.0.0.0", 8081), CandidateHandler).serve_forever()
