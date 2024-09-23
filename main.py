import ast
import json
import math
from typing import Any, Callable, Awaitable

RESPONSE = lambda body: {
    "type": "http.response.body",
    "body": str.encode(body),
    "more_body": False
}

HTTP_404_HEADER = {
    "type": "http.response.start",
    "status": 404,
    "headers": [
        [b"content-type", b"text/plain"]
    ]
}

HTTP_404_RESPONSES = [HTTP_404_HEADER, RESPONSE("404 Not Found")]

HTTP_422_HEADER = {
    "type": "http.response.start",
    "status": 422,
    "headers": [
        [b"content-type", b"text/plain"]
    ]
}

HTTP_422_RESPONSES = [HTTP_422_HEADER, RESPONSE("422 Unprocessable Entity")]

HTTP_400_HEADER = {
    "type": "http.response.start",
    "status": 400,
    "headers": [
        [b"content-type", b"text/plain"]
    ]
}

HTTP_400_RESPONSES = [HTTP_400_HEADER, RESPONSE("400 Bad Request")]

HTTP_200_HEADER = {
    "type": "http.response.start",
    "status": 200,
    "headers": [
        [b"content-type", b"text/plain"]
    ]
}


async def app(scope: dict[str, Any], receive: Callable[[], Awaitable[dict[str, Any]]],
              send: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    if "method" not in scope or scope["method"] != "GET" or "path" not in scope:
        await send_responses(send, HTTP_404_RESPONSES)
        return
    path = str(scope["path"])
    responses: list[dict[str, Any]]
    if path == "/factorial":
        if "query_string" not in scope:
            responses = HTTP_422_RESPONSES
        else:
            print(bytes.decode(scope["query_string"]))
            responses = await factorial(bytes.decode(scope["query_string"]))
    elif path == "/mean":
        t = await receive()
        if "body" not in t:
            responses = HTTP_422_RESPONSES
        else:
            if t["body"] == b"":
                responses = HTTP_422_RESPONSES
            else:
                body = ast.literal_eval(bytes.decode(t["body"]))
                print(body)
                if isinstance(body, list):
                    if len(body) == 0:
                        responses = HTTP_400_RESPONSES
                    elif all(map(lambda x: isinstance(x, float) or isinstance(x, int), body)):
                        responses = await mean(body)
                    else:
                        responses = HTTP_422_RESPONSES
                else:
                    responses = HTTP_422_RESPONSES
    elif path.startswith("/fibonacci"):
        responses = await fibonacci(path)
    else:
        responses = HTTP_404_RESPONSES

    await send_responses(send, responses)


async def send_responses(send: Callable[[dict[str, Any]], Awaitable[None]], responses: list[dict[str, Any]]) -> None:
    for response in responses:
        await send(response)


async def factorial(query: str) -> list[dict[str, Any]]:
    processed_query = list(filter(lambda x: x[0] == "n", map(lambda x: x.split("="), query.split("&"))))
    if len(processed_query) == 0:
        return HTTP_422_RESPONSES
    n_pair = processed_query[0]
    if len(n_pair) < 2:
        return HTTP_422_RESPONSES
    n_value = n_pair[1]
    if str.isdigit(n_value):
        n_value_int = int(n_value)
    elif str.startswith(n_value, "-") and str.isdigit(n_value[1:]):
        return HTTP_400_RESPONSES
    else:
        return HTTP_422_RESPONSES
    result = math.factorial(n_value_int)
    return [HTTP_200_HEADER, RESPONSE(json.dumps({"result": result}))]


async def mean(arr: list[float]) -> list[dict[str, Any]]:
    if len(arr) == 0:
        return HTTP_400_RESPONSES
    result = sum(arr) / len(arr)
    return [HTTP_200_HEADER, RESPONSE(json.dumps({"result": result}))]


async def fibonacci(path: str) -> list[dict[str, Any]]:
    path_splitted = path.split('/')
    if len(path_splitted) < 3:
        return HTTP_422_RESPONSES
    n_value = path_splitted[2]
    if str.isdigit(n_value):
        n_value_int = int(n_value)
    elif str.startswith(n_value, "-") and str.isdigit(n_value[1:]):
        return HTTP_400_RESPONSES
    else:
        return HTTP_422_RESPONSES
    a, b = 0, 1
    for _ in range(n_value_int):
        a, b = b, a + b
    return [HTTP_200_HEADER, RESPONSE(json.dumps({"result": b}))]
