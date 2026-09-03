import json
import os
import time
import urllib.error
import urllib.request

CANDIDATE_URL = os.environ["CANDIDATE_URL"]
PARTNER_STATE_URL = os.environ["PARTNER_STATE_URL"]
EVIDENCE_PATH = os.environ["EVIDENCE_PATH"]
BURST_EVENTS = int(os.environ["BURST_EVENTS"])
BURST_WINDOW_SECONDS = int(os.environ["BURST_WINDOW_SECONDS"])
MAX_CONCURRENT = int(os.environ["MAX_CONCURRENT_PARTNER_CALLS"])
DELIVERY_DEADLINE_SECONDS = int(os.environ["DELIVERY_DEADLINE_SECONDS"])
STARTED = time.monotonic()


def finish_scenario(status, code=None, message=None):
    result = {
        "id": "temporary-partner-failure",
        "status": status,
        "durationMs": round((time.monotonic() - STARTED) * 1000),
        "diagnostic": None if code is None else {"code": code, "message": message},
    }
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as evidence:
        json.dump(result, evidence, separators=(",", ":"))
    print(json.dumps(result, separators=(",", ":")), flush=True)
    raise SystemExit(0 if status == "passed" else 1)


burst_started = time.monotonic()
for index in range(BURST_EVENTS):
    event = {
        "eventId": f"event-prototype-102-{index}",
        "tenantId": "tenant-a",
        "orderId": f"order-{index}",
        "status": "shipped",
    }
    request = urllib.request.Request(
        CANDIDATE_URL,
        data=json.dumps(event, separators=(",", ":")).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    accepted_at = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=1) as response:
            acceptance_ms = round((time.monotonic() - accepted_at) * 1000)
            if response.status != 202:
                finish_scenario("failed", "order_not_accepted", f"expected HTTP 202, got {response.status}")
            if acceptance_ms > 250:
                finish_scenario("failed", "order_flow_blocked", f"acceptance took {acceptance_ms}ms, limit is 250ms")
    except (TimeoutError, urllib.error.URLError) as error:
        finish_scenario("failed", "candidate_unreachable", str(error))

burst_seconds = time.monotonic() - burst_started
if burst_seconds > BURST_WINDOW_SECONDS:
    finish_scenario("failed", "burst_window_exceeded", f"accepted burst in {burst_seconds:.3f}s, limit is {BURST_WINDOW_SECONDS}s")

deadline = time.monotonic() + DELIVERY_DEADLINE_SECONDS
last_state = None
while time.monotonic() < deadline:
    with urllib.request.urlopen(PARTNER_STATE_URL, timeout=1) as response:
        last_state = json.load(response)
    if last_state["deliveredCount"] == BURST_EVENTS:
        if last_state["attempts"] != BURST_EVENTS + 1:
            finish_scenario("failed", "retry_contract_mismatch", f"expected {BURST_EVENTS + 1} attempts, got {last_state['attempts']}")
        if last_state["maxConcurrent"] > MAX_CONCURRENT:
            finish_scenario("failed", "unbounded_concurrency", f"observed {last_state['maxConcurrent']} concurrent partner calls")
        finish_scenario("passed")
    if last_state["lastStatus"] == 401:
        finish_scenario("failed", "signature_rejected", "partner rejected the HMAC signature with HTTP 401")
    time.sleep(0.1)

finish_scenario("failed", "delivery_timeout", f"delivery did not complete; last partner state: {last_state}")
