"""Interface to Figlinq's /v2/jupyter-notebooks endpoints."""

from figlinq.api.v2.utils import build_url, make_params, request

RESOURCE = "jupyter-notebooks"


def create(
    content,
    filename,
    parent_path=None,
    world_readable="false",
):
    """
    Create a new file.

    :param file: File-like object (e.g., open(...) or BytesIO).
    :param filename: File name.
    :param parent_path: Parent path for the file.
    :param world_readable: If True, the file is public.
    :return: requests.Response
    """

    url = build_url(RESOURCE, route="upload")
    data = content

    headers = {
        "X-File-Name": filename,
        "plotly-world-readable": world_readable,
    }
    # Only set parent-path header if explicitly provided (not None)
    # This allows PARENT_FOLDER_ID/PARENT_FOLDER_PATH env vars to take effect
    if parent_path is not None:
        headers["plotly-parent-path"] = parent_path

    response = request("post", url, json=data, headers=headers)
    return response.json()


def content(fid, share_key=None):
    """
    Retrieve full content

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (str) share_key: The secret key granting 'read' access if private.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid, route="content")
    params = make_params(share_key=share_key)
    return request("get", url, params=params)


# def retrieve(fid, share_key=None):
#     """
#     Retrieve a text file.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :param (str) share_key: The secret key granting 'read' access if private.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     params = make_params(share_key=share_key)
#     return request("get", url, params=params)


# def update(fid, body):
#     """
#     Update an file.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :param (dict) body: A mapping of body param names to values.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid)
#     return request("put", url, json=body)


# def trash(fid):
#     """
#     Soft-delete an file. (Can be undone with 'restore').

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="trash")
#     return request("post", url)


# def restore(fid):
#     """
#     Restore a trashed file. See 'trash'.

#     :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
#     :returns: (requests.Response) Returns response directly from requests.

#     """
#     url = build_url(RESOURCE, id=fid, route="restore")
#     return request("post", url)


# def permanent_delete(fid):
#     """
#     Permanently delete a trashed file. See 'trash'.

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
