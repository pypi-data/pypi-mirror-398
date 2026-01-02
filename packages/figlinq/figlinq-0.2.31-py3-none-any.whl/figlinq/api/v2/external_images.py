"""Interface to Figlinq's /v2/external_images endpoints."""

import json
from figlinq.api.v2.utils import build_url, make_params, request
from figlinq import tools
from io import BytesIO
from figlinq.config import get_config

RESOURCE = "external-images"


def create(file, filename, parent_path=None, world_readable="false", is_figure=False):
    """
    Create a new external_file.

    :param file: File-like BytesIO object.
    :param filename: File name.
    :param parent_path: Parent path for the file.
    :param world_readable: If True, the file is public.
    :param is_figure: If True, the file is a figure (svg).
    :return: requests.Response
    """

    url = build_url(RESOURCE, route="upload")
    data = {"external_image": "true"}

    # Create thumbnail if the file is a figure
    if is_figure:
        data["metadata"] = json.dumps(
            {
                "svgedit": {},
            }
        )
        credentials_env = tools.get_credentials_env()
        thumb_bytes = _svg_to_thumbnail(
            file.read(),
            cookies=(
                {
                    "plotly_sess_on": credentials_env["session_token"],
                    "plotly_csrf_on": credentials_env["csrf_token"],
                }
                if "session_token" in credentials_env
                and "csrf_token" in credentials_env
                else {}
            ),
        )
        # Reset file pointer to the beginning
        file.seek(0)

        # Wrap in BytesIO and give it a .name
        thumb_file = BytesIO(thumb_bytes)
        thumb_file.name = "thumbnail.png"
        thumb_file.seek(0)

    files = {"files": (filename, file)}
    if is_figure:
        files["thumb"] = ("thumbnail.png", thumb_file, "image/png")

    headers = {
        "X-File-Name": filename,
        "plotly-world-readable": world_readable,
    }
    # Only set parent-path header if explicitly provided (not None)
    # This allows PARENT_FOLDER_ID/PARENT_FOLDER_PATH env vars to take effect
    if parent_path is not None:
        headers["plotly-parent-path"] = parent_path

    response = request("post", url, files=files, data=data, headers=headers)
    return response.json()


def content(fid, share_key=None):
    """
    Retrieve full content for the external_file

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (str) share_key: The secret key granting 'read' access if private.
    :returns: (requests.Response) Returns response directly from requests.

    """
    split_fid = fid.split(":")
    owner = split_fid[0]
    idlocal = split_fid[1]
    base_domain = get_config()["plotly_domain"]
    url = f"{base_domain}/~{owner}/{idlocal}.src"

    params = make_params(share_key=share_key)
    return request("get", url, params=params)


def retrieve(fid, share_key=None):
    """
    Retrieve an external_file.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (str) share_key: The secret key granting 'read' access if private.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid)
    params = make_params(share_key=share_key)
    return request("get", url, params=params)


# Not implemented yet
# def update(fid, body):
#     """
#     Update an external_file.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :param (dict) body: A mapping of body param names to values.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     return request("put", url, json=body)


# def trash(fid):
#     """
#     Soft-delete an external_file. (Can be undone with 'restore').

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="trash")
#     return request("post", url)


# def restore(fid):
#     """
#     Restore a trashed external_file. See 'trash'.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="restore")
#     return request("post", url)


# def permanent_delete(fid):
#     """
#     Permanently delete a trashed external_file. See 'trash'.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="permanent_delete")
#     return request("delete", url)


# def destroy(fid):
#     """
#     Permanently delete a file.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     return request("delete", url)


# def lookup(path, parent=None, user=None, exists=None):
#     """
#     Retrieve a file by path.

#     :param (str) path: The '/'-delimited path specifying the file location.
#     :param (int) parent: Parent id, an integer, which the path is relative to.
#     :param (str) user: The username to target files for. Defaults to requestor.
#     :param (bool) exists: If True, don't return the full file, just a flag.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, route="lookup")
#     params = make_params(path=path, parent=parent, user=user, exists=exists)
#     return request("get", url, params=params)


def _svg_to_thumbnail(
    svg_text: str, cookies: dict, output_width: int = 200, output_height: int = 200
) -> bytes:
    """
    Converts an SVG (with possible <image> tags requiring cookies) into a PNG thumbnail.

    Args:
        svg_text (str): The raw SVG content as a string.
        cookies (dict): Dictionary of cookies.
        output_width (int): Width of the thumbnail.
        output_height (int): Height of the thumbnail.

    Returns:
        bytes: PNG image as bytes.
    """

    import requests
    import base64
    from bs4 import BeautifulSoup
    import cairosvg

    # Prepare authenticated session
    session = requests.Session()
    for k, v in cookies.items():
        session.cookies.set(k, v)

    # Parse SVG
    soup = BeautifulSoup(svg_text, "xml")
    for img_tag in soup.find_all("image"):
        href = img_tag.get("xlink:href") or img_tag.get("href")
        if not href or href.startswith("data:"):
            continue
        try:
            response = session.get(href, verify=False)
            response.raise_for_status()
            mime = response.headers.get("Content-Type", "image/png")
            b64 = base64.b64encode(response.content).decode()
            data_uri = f"data:{mime};base64,{b64}"
            img_tag["xlink:href"] = data_uri
            if "href" in img_tag.attrs:
                img_tag["href"] = data_uri
        except requests.RequestException as e:
            print(f"Warning: Could not fetch {href}: {e}")

    updated_svg = str(soup)

    # Convert to PNG
    return cairosvg.svg2png(
        bytestring=updated_svg.encode("utf-8"),
        output_width=output_width,
        output_height=output_height,
    )
