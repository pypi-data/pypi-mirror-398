import time

import httpx


# Throw an exception whenever the response code is 4xx or 5xx
def response_hook(response: httpx.Response) -> None:
    if response.is_error:
        response.read()
        response.raise_for_status()


class RetryTransport(httpx.BaseTransport):
    def __init__(self, **kwargs):
        self._wrapper = httpx.HTTPTransport(**kwargs)

    def handle_request(self, request):
        response = self._wrapper.handle_request(request)
        if response.status_code == 429:
            retry_header = response.headers.get("retry-after", None)
            delay = int(retry_header) if retry_header else 0.5
            time.sleep(delay)
            return self.handle_request(request)
        return response

    def close(self):
        self._wrapper.close()


def create_client(lusid_url: str, token: str) -> httpx.Client:
    if token is None or lusid_url is None:
        raise (RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set"))

    return httpx.Client(
        base_url=lusid_url,
        timeout=60,
        headers={
            "authorization": "Bearer " + token,
            "accept": "application/json",
            "content-type": "application/json",
            "X-LUSID-Application": "fbnconfig",
        },
        event_hooks={"response": [response_hook]},
        transport=RetryTransport(),
    )
