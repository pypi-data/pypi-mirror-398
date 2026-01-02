from __future__ import absolute_import
import os

import requests
import json as _json
from requests.exceptions import RequestException
# from retrying import retry

import _plotly_utils.exceptions
from figlinq import config, exceptions
from figlinq.api.utils import basic_auth
from _plotly_utils.utils import PlotlyJSONEncoder


def make_params(**kwargs):
    """
    Helper to create a params dict, skipping undefined entries.

    :returns: (dict) A params dict to pass to `request`.

    """
    return {k: v for k, v in kwargs.items() if v is not None}


def build_url(resource, id="", route=""):
    """
    Create a url for a request on a V2 resource.

    :param (str) resource: E.g., 'files', 'plots', 'grids', etc.
    :param (str) id: The unique identifier for the resource.
    :param (str) route: Detail/list route. E.g., 'restore', 'lookup', etc.
    :return: (str) The url.

    """
    base = config.get_config()["plotly_api_domain"]
    formatter = {"base": base, "resource": resource, "id": id, "route": route}

    # Add path to base url depending on the input params. Note that `route`
    # can refer to a 'list' or a 'detail' route. Since it cannot refer to
    # both at the same time, it's overloaded in this function.
    if id:
        if route:
            url = "{base}/v2/{resource}/{id}/{route}".format(**formatter)
        else:
            url = "{base}/v2/{resource}/{id}".format(**formatter)
    else:
        if route:
            url = "{base}/v2/{resource}/{route}".format(**formatter)
        else:
            url = "{base}/v2/{resource}".format(**formatter)

    return url


def validate_response(response):
    """
    Raise a helpful PlotlyRequestError for failed requests.

    :param (requests.Response) response: A Response object from an api request.
    :raises: (PlotlyRequestError) If the request failed for any reason.
    :returns: (None)

    """
    if response.ok:
        return

    content = response.content
    status_code = response.status_code
    try:
        parsed_content = response.json()
    except ValueError:
        message = content if content else "No Content"
        raise exceptions.PlotlyRequestError(message, status_code, content)

    message = ""
    if isinstance(parsed_content, dict):
        errors = parsed_content.get("errors", [])
        messages = [error.get("message") for error in errors]
        message = "\n".join([msg for msg in messages if msg])
    if not message:
        message = content if content else "No Content"

    raise exceptions.PlotlyRequestError(message, status_code, content)


def get_headers():
    """
    Using session credentials/config, get headers for a V2 API request.

    Users may have their own proxy layer and so we free up the `authorization`
    header for this purpose (instead adding the user authorization in a new
    `plotly-authorization` header). See pull #239.

    :returns: (dict) Headers to add to a requests.request call.

    """
    from plotly import version

    creds = config.get_credentials()

    headers = {
        "plotly-client-platform": "python {}".format(version),
        "content-type": "application/json",
        "HTTP_PLOTLY_CLIENT_PLATFORM": "web - figlinq - python",
    }

    plotly_auth = basic_auth(creds["username"], creds["api_key"])
    proxy_auth = basic_auth(creds["proxy_username"], creds["proxy_password"])

    if config.get_config()["plotly_proxy_authorization"]:
        headers["authorization"] = proxy_auth
        if creds["username"] and creds["api_key"]:
            headers["plotly-authorization"] = plotly_auth
    else:
        if creds["username"] and creds["api_key"]:
            headers["authorization"] = plotly_auth

    if creds["csrf_token"]:
        headers["x-csrftoken"] = creds["csrf_token"]

    # Add default parent folder headers from environment variables
    # These are used by upload endpoints (external_files, external_images, etc.)
    # PARENT_FOLDER_ID takes precedence over PARENT_FOLDER_PATH
    if os.getenv("PARENT_FOLDER_ID"):
        headers["plotly-parent"] = os.getenv("PARENT_FOLDER_ID")
    elif os.getenv("PARENT_FOLDER_PATH"):
        headers["plotly-parent-path"] = os.getenv("PARENT_FOLDER_PATH")

    return headers


def get_cookies():
    cookies = {}
    creds = config.get_credentials()
    if creds["csrf_token"]:
        cookies["plotly_csrf_on"] = creds["csrf_token"]
    if creds["session_token"]:
        cookies["plotly_sess_on"] = creds["session_token"]
    return cookies


# def should_retry(exception):
#     if isinstance(exception, exceptions.PlotlyRequestError):
#         if isinstance(exception.status_code, int) and (
#             500 <= exception.status_code < 600 or exception.status_code == 429
#         ):
#             # Retry on 5XX and 429 (image export throttling) errors.
#             return True
#         elif "Uh oh, an error occurred" in exception.message:
#             return True

#     return False


# @retry(
#     wait_exponential_multiplier=1000,
#     wait_exponential_max=16000,
#     stop_max_delay=180000,
#     retry_on_exception=should_retry,
# )
def request(method, url, **kwargs):
    """
    Central place to make any api v2 api request.

    :param (str) method: The request method ('get', 'put', 'delete', ...).
    :param (str) url: The full api url to make the request to.
    :param kwargs: These are passed along (but possibly mutated) to requests.
    :return: (requests.Response) The response directly from requests.

    """
    # Merge headers: start with defaults from get_headers(), then override with explicit headers
    # This ensures explicit headers (e.g., parent_path) take precedence over env var defaults
    merged_headers = get_headers()
    explicit_headers = kwargs.get("headers", {})
    merged_headers.update(explicit_headers)
    kwargs["headers"] = merged_headers

    if "files" in kwargs:
        kwargs["headers"].pop("content-type", None)

    cookies = kwargs.get("cookies", {})
    session_cookies = get_cookies()
    cookies.update(session_cookies)
    kwargs["cookies"] = cookies

    # Change boolean params to lowercase strings. E.g., `True` --> `'true'`.
    # Just change the value so that requests handles query string creation.
    if isinstance(kwargs.get("params"), dict):
        kwargs["params"] = kwargs["params"].copy()
        for key in kwargs["params"]:
            if isinstance(kwargs["params"][key], bool):
                kwargs["params"][key] = _json.dumps(kwargs["params"][key])

    # Inject PARENT_FOLDER_ID into json body for create requests if not already set
    # This sets a default parent folder for grids/plots when the env var is set
    parent_folder_id = os.getenv("PARENT_FOLDER_ID")
    if parent_folder_id and kwargs.get("json") is not None:
        json_body = kwargs["json"]
        if isinstance(json_body, dict):
            # Only inject if 'parent' and 'parent_path' are not already set
            if "parent" not in json_body and "parent_path" not in json_body:
                try:
                    kwargs["json"] = dict(json_body, parent=int(parent_folder_id))
                except (ValueError, TypeError):
                    pass  # Invalid PARENT_FOLDER_ID, skip injection

    # We have a special json encoding class for non-native objects.
    if kwargs.get("json") is not None:
        if kwargs.get("data"):
            raise _plotly_utils.exceptions.PlotlyError(
                "Cannot supply data and json kwargs."
            )
        kwargs["data"] = _json.dumps(
            kwargs.pop("json"), sort_keys=True, cls=PlotlyJSONEncoder
        )

    # The config file determines whether reuqests should *verify*.
    kwargs["verify"] = config.get_config()["plotly_ssl_verification"]

    try:
        response = requests.request(method, url, **kwargs)
    except RequestException as e:
        # The message can be an exception. E.g., MaxRetryError.
        message = str(getattr(e, "message", "No message"))
        response = getattr(e, "response", None)
        status_code = response.status_code if response else None
        content = response.content if response else "No content"
        raise exceptions.PlotlyRequestError(message, status_code, content)
    validate_response(response)
    return response
