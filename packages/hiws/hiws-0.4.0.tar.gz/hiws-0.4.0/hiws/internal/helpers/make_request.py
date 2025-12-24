import httpx
from hiws.types.exceptions import WhatsappApiException
from typing import Dict, Optional, Any, Union, List, Tuple
try:
  from typing import Literal  # Python 3.8+
except ImportError:  # Python 3.7 fallback
  from typing_extensions import Literal

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


async def amake_cloud_api_request(
    method: HttpMethod,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Union[Dict[str, Any], List[Tuple[str, Any]]]] = None,
) -> httpx.Response:
    """Make an async HTTP request to the Cloud API.

    Supports JSON, form-encoded and multipart uploads.

    Args:
        method: HTTP method to use.
        url: Target endpoint URL.
        headers: Optional HTTP headers. Avoid setting 'Content-Type' manually when using 'files'; httpx will set it.
        query_params: URL query parameters.
        json: JSON body. Do not combine with 'data' for the same request.
        data: Form fields for application/x-www-form-urlencoded or multipart/form-data when combined with 'files'.
        files: Files for multipart/form-data. Accepts dict or list of (name, file) tuples as supported by httpx.

    Returns:
        httpx.Response
    """
    try:
      async with httpx.AsyncClient() as client:
        response = await client.request(
          method=method,
          url=url,
          headers=headers,
          params=query_params,
          json=json,
          data=data,
          files=files,
        )
    except httpx.RequestError as e:
      raise WhatsappApiException(
                message="Network error while sending payload",
                endpoint=url,
                method=method,
                payload=(
                    json if json is not None else
                    data if data is not None else
                    query_params
                ),
                details=str(e),
            ) from e
    if response.status_code < 200 or response.status_code >= 300:
      raise WhatsappApiException.from_httpx_response(
          response,
          endpoint=url,
          method=method,
          payload=(
              json if json is not None else
              data if data is not None else
              query_params
          ),
      )

    return response