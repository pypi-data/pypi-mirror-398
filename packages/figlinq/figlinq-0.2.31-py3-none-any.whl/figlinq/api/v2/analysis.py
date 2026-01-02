"""Interface to Figlinq's unified /v2/analysis endpoints."""

from __future__ import annotations

from typing import Any, Dict, Optional

from figlinq.api.v2.utils import build_url, make_params, request

RESOURCE = "analysis"


def list(fid: Optional[str] = None, analysis_type: Optional[str] = None, **query):
    """List analysis records for the authenticated user."""

    params = make_params(fid=fid, type=analysis_type, **query)
    url = build_url(RESOURCE)
    return request("get", url, params=params)


def create(body: Dict[str, Any]):
    """Create a new statistical analysis via the unified endpoint."""

    url = build_url(RESOURCE)
    return request("post", url, json=body)


def destroy(analysis_id: str):
    """Delete an existing analysis record."""

    url = build_url(RESOURCE, id=str(analysis_id))
    return request("delete", url)


__all__ = ["list", "create", "destroy"]
