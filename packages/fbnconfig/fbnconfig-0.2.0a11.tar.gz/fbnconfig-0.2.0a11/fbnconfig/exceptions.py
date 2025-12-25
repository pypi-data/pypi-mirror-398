import functools
from typing import Any

import httpx


class QueryError(RuntimeError):  # has to be runtime for backward compat
    def __init__(self, status_str: str, status_resp: Any):
        self.status_str = status_str
        self.status_resp = status_resp
        super().__init__(self._get_message())

    def _get_message(self) -> str:
        info = []
        summary = ""
        if self.status_resp:
            if self.status_resp.get("feedback"):
                info = [
                    f"{k}: {v}"
                    for k, v in self.status_resp["feedback"][-1].items()
                    if k in ["executionId", "sessionId"]
                ]
            if self.status_resp.get("progress", None):
                summary = self.status_resp["progress"].split("Dependency & Execution details:")[-1]
                summary = (" " * 8).join(summary.splitlines(True))
        return "\n".join([f"Error, query {self.status_str}"] + info + [summary])

    def __str__(self) -> str:
        return self._get_message()


class ApiError(Exception):
    pass


class ApiStatusError(Exception):
    def __init__(self, http_exception: httpx.HTTPStatusError):
        self.http_exception = http_exception
        super().__init__(self._get_message())

    def _get_message(self) -> str:
        exc = self.http_exception
        # build the detail
        status = exc.response.status_code
        base_msg = " ".join(
            [
                f"The server responded with {exc.response.status_code}",
                f"while requesting {exc.request.method} {exc.request.url!r}",
            ]
        )
        if exc.response.is_server_error:
            detail = [exc.response.text]
        elif status == 401:
            detail = [
                "Unauthorized: The user making the request could not be identified.",
                "This may indicate that the provided access token is invalid or expired."
            ]
        elif status == 403:
            detail = [
                "Access Denied",
                "User does not have permission to perform the requested action"
            ]
        else:
            detail = []
        # build the subdetail if it's a finbourne problem detail
        if "application/problem+json" in exc.response.headers.get("content-type", "").split(";"):
            problem = exc.response.json()
            subdetail = [
                f"{k}: {v}"
                 for k, v in problem.items()
                 if k in ["title", "detail", "instance"]
            ]
            if problem.get("errors", None):
                subdetail = subdetail + ["errors: " + str(problem["errors"].get("Name", ""))]
        else:
            subdetail = [f"detail {exc.response.text}"]
        return "\n".join([base_msg] + detail + subdetail)

    def __str__(self) -> str:
        return self._get_message()


def api_exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        # deal with errors that do not send a response
        except httpx.RequestError as exc:
            msg = " ".join([
                f"An error occurred while requesting {exc.request.url!r} ",
                f"before we got a response - {exc}"
            ])
            raise ApiError(msg) from exc
        # errors from the server with a response
        except httpx.HTTPStatusError as exc:
            raise ApiStatusError(exc) from exc

    return wrapper
