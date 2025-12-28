import random
import time
import traceback
import unittest
import json

from tqdm import trange

from gatling.utility.http_fetch_fctns import sync_fetch_http


def log_response(name, url, method, rtype, status, size, result):
    """
    Unified logging helper for test results.
    Prints a concise summary of each request and response.

    :param name: Test name or label.
    :param url: Target URL.
    :param method: HTTP method used (GET, POST, etc.).
    :param rtype: Expected return type ('text', 'json', or 'bytes').
    :param status: HTTP response status code.
    :param size: Response body size in bytes.
    :param result: Response content.
    """
    print(f"\n[{name}]")
    print(f"  URL: {url}")
    print(f"  Method: {method}")
    print(f"  Return type: {rtype}")
    print(f"  Status: {status}")
    print(f"  Size: {size} bytes")

    # Show a short preview of the response content
    if isinstance(result, (bytes, bytearray)):
        preview = result[:50]  # limit byte preview length
        print(f"  Preview (bytes): {preview!r}")
    elif isinstance(result, (dict, list)):
        snippet = json.dumps(result, ensure_ascii=False)[:100]
        print(f"  Preview (json): {snippet!r}")
    else:
        print(f"  Preview (text): {str(result)[:100]!r}")


@unittest.skip("Skipping all tests in this class temporarily")
class TestSyncFetchHttp(unittest.TestCase):
    """
    Unit tests for sync_fetch_http().
    Covers both GET and POST requests with 'text', 'json', and 'bytes' response types.
    """

    def try_request(self, url, method, rtype, retries: int = 10, **kwargs):
        """Helper: retry N times with random delay 0–1s."""
        last_exception = None
        for i in trange(retries):
            try:
                result, status, size = sync_fetch_http(url, method=method, rtype=rtype, **kwargs)
                if status == 200:
                    log_response(f"{method} {rtype}", url, method, rtype, status, size, result)
                    return result, status, size
            except Exception as e:
                last_exception = e
                print(traceback.format_exc())
            time.sleep(random.random())  # random wait 0.0 ~ 1.0 sec
        if last_exception:
            raise last_exception
        self.fail(f"Request to {url} failed after {retries} retries")

    def test_get_text(self):
        """GET request returning HTML text."""
        url = "https://httpbin.org/html"
        self.try_request(url, "GET", "text", retries=10)

    def test_get_json(self):
        """GET request returning JSON data."""
        url = "https://httpbin.org/get"
        self.try_request(url, "GET", "json", retries=10)

    def test_get_bytes(self):
        """GET request returning binary data (PNG image)."""
        url = "https://httpbin.org/image/png"
        self.try_request(url, "GET", "bytes", retries=10)

    def test_post_text(self):
        """POST request returning text (form-encoded)."""
        url = "https://httpbin.org/post"
        self.try_request(url, "POST", "text", data={"k": "v"}, retries=10)

    def test_post_json(self):
        """POST request returning JSON response."""
        url = "https://httpbin.org/post"
        data = json.dumps({"a": 1, "b": 2})
        headers = {"Content-Type": "application/json"}
        self.try_request(url, "POST", "json", data=data, headers=headers, retries=10)

    def test_post_bytes(self):
        """POST request returning binary response."""
        url = "https://httpbin.org/post"
        payload = b"test-binary-data"
        self.try_request(url, "POST", "bytes", data=payload, retries=10)


if __name__ == "__main__":
    pass
    unittest.main(verbosity=2)
