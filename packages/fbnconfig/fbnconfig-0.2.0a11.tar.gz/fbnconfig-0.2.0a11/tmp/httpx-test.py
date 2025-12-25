import os

import httpx


def raise_on_4xx_5xx(response):
    return response.raise_for_status()


def main():
    client = httpx.Client(
        base_url="https://fbn-qa.lusid.com",
        headers={"authorization": "Bearer " + os.getenv("FBN_ACCESS_TOKEN", "")},
        event_hooks={"response": [raise_on_4xx_5xx]},
    )
    try:
        client.get(url="/drive/api/folders/fb7225b61b864752aa03ba37872fe8e8")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(e.response.reason_phrase)
            print("identifier already exists")
        print(e.response)


main()
