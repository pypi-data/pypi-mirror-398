# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ..types import track_event_params
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
from ..types.track_event_response import TrackEventResponse

__all__ = ["TrackResource", "AsyncTrackResource"]


class TrackResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TrackResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#accessing-raw-response-data-eg-headers
        """
        return TrackResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TrackResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#with_streaming_response
        """
        return TrackResourceWithStreamingResponse(self)

    def event(
        self,
        *,
        token: str,
        event: str,
        default_properties: Optional[track_event_params.DefaultProperties] | Omit = omit,
        distinct_id: Optional[str] | Omit = omit,
        email: Optional[str] | Omit = omit,
        event_properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        external_id: Optional[str] | Omit = omit,
        time: Optional[float] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        user_properties: Optional[track_event_params.UserProperties] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackEventResponse:
        """Track events from your server.

        Please include at least one of: userId,
        externalId, or email. These properties help us associate events with existing
        users. For all fields, null values unset the property and undefined values do
        not unset existing properties.

        Args:
          token: The token for your Ours Privacy Source. You can find this in the Ours dashboard.

          event: The name of the event you're tracking. This must be whitelisted in the Ours
              dashboard.

          default_properties: These properties are used throughout the Ours app to pass known values onto
              destinations

          distinct_id: A unique identifier for the event. This helps prevent duplicate events.

          email: The email address of a user. We will associate this event with the user or
              create a user. Used for lookup if externalId and userId are not included in the
              request.

          event_properties: Any additional event properties you want to pass along.

          external_id: The externalId (the ID in your system) of a user. We will associate this event
              with the user or create a user. If included in the request, email lookup is
              ignored.

          time: The time at which the event occurred in milliseconds since UTC epoch. The time
              must be in the past and within the last 7 days.

          user_id: The Ours user id stored in local storage and cookies on your web properties. If
              userId is included in the request, we do not lookup the user by email or
              externalId.

          user_properties: Properties to set on the visitor. (optional) You can also update these
              properties via the identify endpoint.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/track" if self._client._base_url_overridden else "https://api.oursprivacy.com/api/v1/track",
            body=maybe_transform(
                {
                    "token": token,
                    "event": event,
                    "default_properties": default_properties,
                    "distinct_id": distinct_id,
                    "email": email,
                    "event_properties": event_properties,
                    "external_id": external_id,
                    "time": time,
                    "user_id": user_id,
                    "user_properties": user_properties,
                },
                track_event_params.TrackEventParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackEventResponse,
        )


class AsyncTrackResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTrackResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTrackResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTrackResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/with-ours/ingest-sdk-python#with_streaming_response
        """
        return AsyncTrackResourceWithStreamingResponse(self)

    async def event(
        self,
        *,
        token: str,
        event: str,
        default_properties: Optional[track_event_params.DefaultProperties] | Omit = omit,
        distinct_id: Optional[str] | Omit = omit,
        email: Optional[str] | Omit = omit,
        event_properties: Optional[Dict[str, Optional[str]]] | Omit = omit,
        external_id: Optional[str] | Omit = omit,
        time: Optional[float] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        user_properties: Optional[track_event_params.UserProperties] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TrackEventResponse:
        """Track events from your server.

        Please include at least one of: userId,
        externalId, or email. These properties help us associate events with existing
        users. For all fields, null values unset the property and undefined values do
        not unset existing properties.

        Args:
          token: The token for your Ours Privacy Source. You can find this in the Ours dashboard.

          event: The name of the event you're tracking. This must be whitelisted in the Ours
              dashboard.

          default_properties: These properties are used throughout the Ours app to pass known values onto
              destinations

          distinct_id: A unique identifier for the event. This helps prevent duplicate events.

          email: The email address of a user. We will associate this event with the user or
              create a user. Used for lookup if externalId and userId are not included in the
              request.

          event_properties: Any additional event properties you want to pass along.

          external_id: The externalId (the ID in your system) of a user. We will associate this event
              with the user or create a user. If included in the request, email lookup is
              ignored.

          time: The time at which the event occurred in milliseconds since UTC epoch. The time
              must be in the past and within the last 7 days.

          user_id: The Ours user id stored in local storage and cookies on your web properties. If
              userId is included in the request, we do not lookup the user by email or
              externalId.

          user_properties: Properties to set on the visitor. (optional) You can also update these
              properties via the identify endpoint.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/track" if self._client._base_url_overridden else "https://api.oursprivacy.com/api/v1/track",
            body=await async_maybe_transform(
                {
                    "token": token,
                    "event": event,
                    "default_properties": default_properties,
                    "distinct_id": distinct_id,
                    "email": email,
                    "event_properties": event_properties,
                    "external_id": external_id,
                    "time": time,
                    "user_id": user_id,
                    "user_properties": user_properties,
                },
                track_event_params.TrackEventParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TrackEventResponse,
        )


class TrackResourceWithRawResponse:
    def __init__(self, track: TrackResource) -> None:
        self._track = track

        self.event = to_raw_response_wrapper(
            track.event,
        )


class AsyncTrackResourceWithRawResponse:
    def __init__(self, track: AsyncTrackResource) -> None:
        self._track = track

        self.event = async_to_raw_response_wrapper(
            track.event,
        )


class TrackResourceWithStreamingResponse:
    def __init__(self, track: TrackResource) -> None:
        self._track = track

        self.event = to_streamed_response_wrapper(
            track.event,
        )


class AsyncTrackResourceWithStreamingResponse:
    def __init__(self, track: AsyncTrackResource) -> None:
        self._track = track

        self.event = async_to_streamed_response_wrapper(
            track.event,
        )
