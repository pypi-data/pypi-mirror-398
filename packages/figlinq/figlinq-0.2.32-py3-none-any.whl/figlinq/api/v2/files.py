"""Interface to Plotly's /v2/files endpoints."""
from __future__ import absolute_import

from figlinq.api.v2.utils import build_url, make_params, request

RESOURCE = "files"


def retrieve(fid, share_key=None):
    """
    Retrieve a general file from Plotly.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (str) share_key: The secret key granting 'read' access if private.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid)
    params = make_params(share_key=share_key)
    return request("get", url, params=params)


def update(fid, body):
    """
    Update a general file from Plotly.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (dict) body: A mapping of body param names to values.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid)
    return request("put", url, json=body)


def trash(fid):
    """
    Soft-delete a general file from Plotly. (Can be undone with 'restore').

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid, route="trash")
    return request("post", url)


def restore(fid):
    """
    Restore a trashed, general file from Plotly. See 'trash'.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid, route="restore")
    return request("post", url)


def permanent_delete(fid):
    """
    Permanently delete a trashed, general file from Plotly. See 'trash'.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, id=fid, route="permanent_delete")
    return request("delete", url)


def lookup(path, parent=None, user=None, exists=None):
    """
    Retrieve a general file from Plotly without needing a fid.

    :param (str) path: The '/'-delimited path specifying the file location.
    :param (int) parent: Parent id, an integer, which the path is relative to.
    :param (str) user: The username to target files for. Defaults to requestor.
    :param (bool) exists: If True, don't return the full file, just a flag.
    :returns: (requests.Response) Returns response directly from requests.

    """
    url = build_url(RESOURCE, route="lookup")
    params = make_params(path=path, parent=parent, user=user, exists=exists)
    return request("get", url, params=params)


def create_revision(fid, related_operation_id=None):
    """
    Create a new revision of a file. This should be called after all changes
    to a file have been made. It creates a snapshot of the current file state.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :param (str) related_operation_id: Optional ID to link revisions of related
        files (e.g., a plot and its associated grid) so they can be reverted together.
    :returns: (requests.Response) Returns response directly from requests.
        Returns 201 if revision created, 204 if file unchanged since last revision.

    """
    url = build_url(RESOURCE, id=fid, route="revisions")
    body = {}
    if related_operation_id is not None:
        body["related_operation_id"] = related_operation_id
    return request("post", url, json=body if body else None)


def list_revisions(fid):
    """
    List all revisions of a file.

    :param (str) fid: The `{username}:{idlocal}` identifier. E.g. `foo:88`.
    :returns: (requests.Response) Returns response directly from requests.
        Response contains a list of revision objects with fields:
        - id: Revision ID
        - size: Size of the revision in bytes
        - creation_time: Timestamp when revision was created
        - related_operation_id: ID linking related file revisions
        - user_username: Username of the revision creator

    """
    url = build_url(RESOURCE, id=fid, route="revisions")
    return request("get", url)
