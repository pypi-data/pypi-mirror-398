from gatling.utility.http_fetch_fctns import sync_fetch_http, async_fetch_http, fwrap
import asyncio

target_url = "https://httpbin.org/get"
print("--- Synchronous request ---")
result, status, size = sync_fetch_http(target_url, rtype="json")
print(status, size, result)

print("--- Asynchronous request ---")
result, status, size = asyncio.run(fwrap(async_fetch_http, target_url=target_url, rtype="json"))
print(status, size, result)
