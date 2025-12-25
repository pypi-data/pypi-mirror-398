# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import visitor_upsert_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.visitor_upsert_response import VisitorUpsertResponse

__all__ = ["VisitorResource", "AsyncVisitorResource"]


class VisitorResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> VisitorResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#accessing-raw-response-data-eg-headers
        """
        return VisitorResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> VisitorResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#with_streaming_response
        """
        return VisitorResourceWithStreamingResponse(self)

    def upsert(
        self,
        *,
        token: str,
        user_properties: visitor_upsert_params.UserProperties,
        default_properties: Optional[visitor_upsert_params.DefaultProperties] | Omit = omit,
        email: Optional[str] | Omit = omit,
        external_id: Optional[str] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VisitorUpsertResponse:
        """Define visitor properties on an existing visitor or create a new visitor.

        Note:
        This does not fire an event. If you want to fire an event, use the track method
        and include properties for the visitor.

        Args:
          token: The token for your Ours Privacy Source. You can find this in the Ours dashboard.

          user_properties: User properties to associate with this user. The existing user properties will
              be updated. And all future events will have these properties associated with
              them.

          default_properties: These properties are used throughout the Ours app to pass known values onto
              destinations

          email: The email address of a user. We will associate this event with the user or
              create a user. Used for lookup if externalId and userId are not included in the
              request.

          external_id: The externalId (the ID in your system) of a user. We will associate this event
              with the user or create a user. If included in the request, email lookup is
              ignored.

          user_id: The Ours user id stored in local storage and cookies on your web properties. If
              userId is included in the request, we do not lookup the user by email or
              externalId.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/identify" if self._client._base_url_overridden else "https://api.oursprivacy.com/api/v1/identify",
            body=maybe_transform(
                {
                    "token": token,
                    "user_properties": user_properties,
                    "default_properties": default_properties,
                    "email": email,
                    "external_id": external_id,
                    "user_id": user_id,
                },
                visitor_upsert_params.VisitorUpsertParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VisitorUpsertResponse,
        )


class AsyncVisitorResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncVisitorResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncVisitorResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncVisitorResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#with_streaming_response
        """
        return AsyncVisitorResourceWithStreamingResponse(self)

    async def upsert(
        self,
        *,
        token: str,
        user_properties: visitor_upsert_params.UserProperties,
        default_properties: Optional[visitor_upsert_params.DefaultProperties] | Omit = omit,
        email: Optional[str] | Omit = omit,
        external_id: Optional[str] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> VisitorUpsertResponse:
        """Define visitor properties on an existing visitor or create a new visitor.

        Note:
        This does not fire an event. If you want to fire an event, use the track method
        and include properties for the visitor.

        Args:
          token: The token for your Ours Privacy Source. You can find this in the Ours dashboard.

          user_properties: User properties to associate with this user. The existing user properties will
              be updated. And all future events will have these properties associated with
              them.

          default_properties: These properties are used throughout the Ours app to pass known values onto
              destinations

          email: The email address of a user. We will associate this event with the user or
              create a user. Used for lookup if externalId and userId are not included in the
              request.

          external_id: The externalId (the ID in your system) of a user. We will associate this event
              with the user or create a user. If included in the request, email lookup is
              ignored.

          user_id: The Ours user id stored in local storage and cookies on your web properties. If
              userId is included in the request, we do not lookup the user by email or
              externalId.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/identify" if self._client._base_url_overridden else "https://api.oursprivacy.com/api/v1/identify",
            body=await async_maybe_transform(
                {
                    "token": token,
                    "user_properties": user_properties,
                    "default_properties": default_properties,
                    "email": email,
                    "external_id": external_id,
                    "user_id": user_id,
                },
                visitor_upsert_params.VisitorUpsertParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=VisitorUpsertResponse,
        )


class VisitorResourceWithRawResponse:
    def __init__(self, visitor: VisitorResource) -> None:
        self._visitor = visitor

        self.upsert = to_raw_response_wrapper(
            visitor.upsert,
        )


class AsyncVisitorResourceWithRawResponse:
    def __init__(self, visitor: AsyncVisitorResource) -> None:
        self._visitor = visitor

        self.upsert = async_to_raw_response_wrapper(
            visitor.upsert,
        )


class VisitorResourceWithStreamingResponse:
    def __init__(self, visitor: VisitorResource) -> None:
        self._visitor = visitor

        self.upsert = to_streamed_response_wrapper(
            visitor.upsert,
        )


class AsyncVisitorResourceWithStreamingResponse:
    def __init__(self, visitor: AsyncVisitorResource) -> None:
        self._visitor = visitor

        self.upsert = async_to_streamed_response_wrapper(
            visitor.upsert,
        )
