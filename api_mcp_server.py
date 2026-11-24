import json
import re
import httpx

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Dynamic API Testing Server")

BASE_URL = "https://jsonplaceholder.typicode.com"


@mcp.tool()
async def test_api(path: str) -> str:

    match = re.fullmatch(
        r"/(posts|users)/([0-9]+)", path
    )

    if not match:
        return json.dumps({
            "path": path,
            "status_code": None,
            "error": "Invalid or unsupported API path"
        })

    resource, resource_id = match.groups()

    if len(resource_id) > 9:
        return json.dumps({
            "path": path,
            "status_code": None,
            "error": "Resource ID too long"
        })

    try:
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=False
        ) as client:

            response = await client.get(BASE_URL + path)

        try:
            body = response.json()
        except ValueError:
            body = response.text[:1000]

        return json.dumps({
            "path": path,
            "status_code": response.status_code,
            "body": body
        })

    except httpx.RequestError as exc:
        return json.dumps({
            "path": path,
            "status_code": None,
            "error": str(exc)
        })


if __name__ == "__main__":
    mcp.run(transport="stdio")
