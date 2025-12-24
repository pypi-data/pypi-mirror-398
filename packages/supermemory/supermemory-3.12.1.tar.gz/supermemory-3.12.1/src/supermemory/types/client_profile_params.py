# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ClientProfileParams"]


class ClientProfileParams(TypedDict, total=False):
    container_tag: Required[Annotated[str, PropertyInfo(alias="containerTag")]]
    """Tag to filter the profile by.

    This can be an ID for your user, a project ID, or any other identifier you wish
    to use to filter memories.
    """

    q: str
    """Optional search query to include search results in the response"""
