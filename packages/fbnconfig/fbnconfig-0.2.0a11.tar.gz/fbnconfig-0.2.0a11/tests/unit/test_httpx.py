import httpx
import respx


def test_httpx_client_with_retry_hook():
    router = respx.Router()
    router.get("http://fakeexample.com/200").mock(
        side_effect=[
            httpx.Response(429, json={"id": 1234}, headers={"Retry-after": "0.1"}),
            httpx.Response(200, json={"id": 23456}),
        ]
    )
    mock_transport = httpx.MockTransport(router.handler)

    client = httpx.Client(base_url="http://fakeexample.com", transport=mock_transport)
    retries = 0
    sleeps = []

    def sleeper(t):
        nonlocal sleeps
        sleeps.append(t)

    def response_hook(response):
        nonlocal retries
        if response.status_code == 429:
            retry_header = response.headers.get("retry-after", None)
            delay = float(retry_header) if retry_header else 1
            sleeper(delay)
            retries = 1
            retry = client.send(response.request)
            response.next_request = retry.next_request
            response.status_code = retry.status_code
            response.headers = retry.headers
            response._content = retry._content

    client.event_hooks["response"] = [response_hook]
    res = client.request("get", "/200")
    assert sleeps == [0.1]
    assert retries == 1
    assert res.status_code == 200
    assert res.json() == {"id": 23456}
    sent = router.calls.last.request
    assert sent.method == "GET"
    assert sent.url == "http://fakeexample.com/200"


def test_httpx_client_with_raise_for_status():
    router = respx.Router()
    router.post("http://fakeexample.com/test").mock(
        side_effect=[
            httpx.Response(400, json={"not found": 1234}),
            httpx.Response(200, json={"id": 23456}),
        ]
    )

    def response_hook(response):
        response.raise_for_status()

    mock_transport = httpx.MockTransport(router.handler)

    client = httpx.Client(
        base_url="http://fakeexample.com",
        transport=mock_transport,
        event_hooks={"response": [response_hook]},
    )

    try:
        client.request("post", "/test")
    except httpx.HTTPStatusError as error:
        assert error.response.status_code == httpx.codes.BAD_REQUEST
        assert error.response.json()["not found"] == 1234

    sent = router.calls.last.request
    assert sent.method == "POST"
    assert sent.url.path == "/test"

    res = client.request("post", "/test")
    assert res.status_code == 200
    assert res.json() == {"id": 23456}
    sent = router.calls.last.request
    assert sent.method == "POST"
    assert sent.url.path == "/test"
