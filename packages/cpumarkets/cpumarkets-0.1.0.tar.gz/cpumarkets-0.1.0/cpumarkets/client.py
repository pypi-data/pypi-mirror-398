import json
import time
import hmac
import hashlib
import urllib.request
import urllib.error


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class CPUMarketsClient:
    def __init__(self, base_url, api_key, api_secret, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    def _sign_headers(self, method, path, body):
        timestamp = str(int(time.time()))
        body_json = canonical_json(body) if body else ""
        base = "|".join([method, path, timestamp, body_json])
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            base.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-SDK-Key": self.api_key,
            "X-SDK-Timestamp": timestamp,
            "X-SDK-Signature": signature,
        }
        return headers, body_json

    def _request(self, method, path, body=None):
        headers, body_json = self._sign_headers(method, path, body)
        data = body_json.encode("utf-8") if body else None
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as err:
            raw = err.read().decode("utf-8") if err.fp else ""
            try:
                data = json.loads(raw)
                raise RuntimeError(data.get("error", raw))
            except json.JSONDecodeError:
                raise RuntimeError(raw or f"HTTP {err.code}")
        except urllib.error.URLError as err:
            raise RuntimeError(f"Network error: {err}")

    def list_listings(self):
        data = self._request("GET", "/api/sdk/listings")
        return data.get("listings", [])

    def submit_job(self, listing_id, task_type, payload, requested_cores, requested_seconds, priority=0):
        body = {
            "listing_id": listing_id,
            "task_type": task_type,
            "payload": payload,
            "requested_cores": requested_cores,
            "requested_seconds": requested_seconds,
            "priority": priority,
        }
        data = self._request("POST", "/api/sdk/jobs", body=body)
        return data.get("job_id") or data.get("id")

    def submit_direct_job(self, task_type, payload, requested_cores, requested_seconds, priority=0):
        body = {
            "task_type": task_type,
            "payload": payload,
            "requested_cores": requested_cores,
            "requested_seconds": requested_seconds,
            "priority": priority,
        }
        data = self._request("POST", "/api/sdk/jobs/direct", body=body)
        return data.get("job_id") or data.get("id")

    def get_job(self, job_id):
        data = self._request("GET", f"/api/sdk/jobs/{job_id}")
        return data.get("job", {})

    def get_result(self, job_id):
        return self._request("GET", f"/api/sdk/jobs/{job_id}/result")

    def wait_for_result(self, job_id, poll_interval=2, timeout=120):
        start = time.time()
        while True:
            job = self.get_job(job_id)
            status = job.get("status")
            if status == "completed":
                return self.get_result(job_id)
            if status == "failed":
                raise RuntimeError("Job failed")
            if time.time() - start > timeout:
                raise TimeoutError("Timed out waiting for job result")
            time.sleep(poll_interval)
