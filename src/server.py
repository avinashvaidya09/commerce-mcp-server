"""This is the entry point for the MCP server"""

import os
import urllib.parse
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from auth_manager import AuthManager

load_dotenv()

mcp = FastMCP("commerce-mcp-server")

CAP_BASE_URL = os.getenv("CAP_BASE_URL", "http://localhost:4004").rstrip("/")
ODATA_CATALOG_ROOT = os.getenv("ODATA_CATALOG_ROOT", "/odata/v4/catalog").rstrip("/")
# Initialize the AuthManager
AuthManager.initialize_auth()


@mcp.tool
def cap_ping() -> dict:
    """Ping the CAP service to check if it's reachable."""
    try:
        auth = AuthManager.get_auth()

        response = httpx.get(
            f"{CAP_BASE_URL}{ODATA_CATALOG_ROOT}/$metadata", auth=auth, timeout=5
        )
        response.raise_for_status()
        return {"status": "success", "message": "CAP service is reachable."}
    except httpx.RequestError as e:
        return {"status": "error", "message": f"CAP service is not reachable: {str(e)}"}


@mcp.tool
def get_categories(top: int = 20) -> list[dict]:
    """Fetch top 20 product categories

    Args:
        top (int, optional): Limit. Defaults to 20.

    Returns:
        list[dict]: List of category details
    """
    try:
        query = f"$top={top}"
        path = f"Categories?{query}"

        data = _make_get_request(
            f"{CAP_BASE_URL}{ODATA_CATALOG_ROOT}", path, timeout=10
        )
        return data.get("value", [])
    except httpx.RequestError as e:
        return {"status": "error", "message": f"Failed to fetch categories: {str(e)}"}


@mcp.tool
def get_products(top: int = 20, category_id: str | None = None) -> list[dict]:
    """Fetch top 20 products

    Args:
        top (int, optional): Limit. Defaults to 20.

    Returns:
        list[dict]: List of product details
    """
    try:
        return _fetch_products(category_id=category_id, top=top)
    except httpx.RequestError as e:
        return {"status": "error", "message": f"Failed to fetch products: {str(e)}"}


@mcp.tool
def get_products_by_category_name(category_name: str, top: int = 20) -> list[dict]:
    """Fetch products by category name

    Args:
        category_name (str): Category name
        top (int, optional): Limit. Defaults to 20.

    Returns:
        list[dict]: List of product details
    """
    try:
        # First, get the category ID by name
        filt = f"contains(name, '{category_name}')"
        category_path = "Categories?$filter=" + urllib.parse.quote(filt, safe=" =$'")

        category_data = _make_get_request(
            f"{CAP_BASE_URL}{ODATA_CATALOG_ROOT}", category_path, timeout=10
        )
        categories = category_data.get("value", [])
        if not categories:
            return {
                "status": "error",
                "message": f"No category found with name: {category_name}",
            }

        category_id = categories[0]["ID"]

        # Now, fetch products for the found category ID
        return _fetch_products(top=top, category_id=category_id)

    except httpx.RequestError as e:
        return {
            "status": "error",
            "message": f"Failed to fetch products by category name: {str(e)}",
        }


def _fetch_products(category_id: str, top: int) -> list:
    """
    Helper function to fetch products based on category ID and limit.

    Args:
        category_id (str): The category ID to filter products.
        top (int): The maximum number of products to fetch.
        auth: Authentication object for the request.

    Returns:
        list: List of product details.
    """
    query = [f"$top={top}"]
    if category_id:
        # OData filter: category_ID eq '2'
        filt = f"category_ID eq '{category_id}'"
        query.append("$filter=" + urllib.parse.quote(filt, safe=" =$'"))
    path = "Products?" + "&".join(query)

    data = _make_get_request(f"{CAP_BASE_URL}{ODATA_CATALOG_ROOT}", path, timeout=10)
    return data.get("value", [])


def _make_get_request(url: str, path: str, timeout=10) -> dict:
    """
    Helper method to make an HTTP GET request.

    Args:
        path (str): The relative path to append to the base URL.
        auth: The authentication object (optional).
        timeout (int): The timeout for the request in seconds.

    Returns:
        dict: The JSON response from the server.
    """
    auth = AuthManager.get_auth()
    response = httpx.get(f"{url}/{path}", auth=auth, timeout=timeout)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Local server (STDIO)
    mcp.run()
