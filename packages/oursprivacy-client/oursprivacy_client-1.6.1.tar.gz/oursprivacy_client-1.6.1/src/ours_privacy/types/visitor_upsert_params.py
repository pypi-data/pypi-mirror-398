# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["VisitorUpsertParams", "UserProperties", "DefaultProperties"]


class VisitorUpsertParams(TypedDict, total=False):
    token: Required[str]
    """The token for your Ours Privacy Source.

    You can find this in the Ours dashboard.
    """

    user_properties: Required[Annotated[UserProperties, PropertyInfo(alias="userProperties")]]
    """User properties to associate with this user.

    The existing user properties will be updated. And all future events will have
    these properties associated with them.
    """

    default_properties: Annotated[Optional[DefaultProperties], PropertyInfo(alias="defaultProperties")]
    """
    These properties are used throughout the Ours app to pass known values onto
    destinations
    """

    email: Optional[str]
    """The email address of a user.

    We will associate this event with the user or create a user. Used for lookup if
    externalId and userId are not included in the request.
    """

    external_id: Annotated[Optional[str], PropertyInfo(alias="externalId")]
    """The externalId (the ID in your system) of a user.

    We will associate this event with the user or create a user. If included in the
    request, email lookup is ignored.
    """

    user_id: Annotated[Optional[str], PropertyInfo(alias="userId")]
    """The Ours user id stored in local storage and cookies on your web properties.

    If userId is included in the request, we do not lookup the user by email or
    externalId.
    """


class UserProperties(TypedDict, total=False):
    """User properties to associate with this user.

    The existing user properties will be updated. And all future events will have these properties associated with them.
    """

    ad_id: Optional[str]

    adset_id: Optional[str]

    alart: Optional[str]

    aleid: Optional[str]

    basis_cid: Optional[str]

    campaign_id: Optional[str]

    city: Optional[str]

    clickid: Optional[str]

    clid: Optional[str]

    company_name: Optional[str]

    consent: Optional[Dict[str, Optional[str]]]

    country: Optional[str]

    custom_properties: Optional[Dict[str, Optional[str]]]

    date_of_birth: Optional[str]

    dclid: Optional[str]

    email: Optional[str]

    epik: Optional[str]

    external_id: Optional[str]

    fbc: Optional[str]

    fbclid: Optional[str]

    fbp: Optional[str]

    first_name: Optional[str]

    gad_source: Optional[str]

    gbraid: Optional[str]

    gclid: Optional[str]

    gender: Optional[str]

    im_ref: Optional[str]

    ip: Optional[str]
    """The IP address of the user"""

    irclickid: Optional[str]

    is_bot: Optional[str]

    job_title: Optional[str]

    last_name: Optional[str]

    li_fat_id: Optional[str]

    msclkid: Optional[str]

    ndclid: Optional[str]

    phone_number: Optional[str]

    qclid: Optional[str]

    rdt_cid: Optional[str]

    referrer: Optional[str]

    referring_domain: Optional[str]

    sacid: Optional[str]

    sccid: Optional[str]

    sid: Optional[str]

    state: Optional[str]

    ttclid: Optional[str]

    twclid: Optional[str]

    user_agent: Optional[str]

    user_agent_full_list: Optional[str]

    utm_campaign: Optional[str]

    utm_content: Optional[str]

    utm_medium: Optional[str]

    utm_name: Optional[str]

    utm_source: Optional[str]

    utm_term: Optional[str]

    wbraid: Optional[str]

    zip: Optional[str]


class DefaultProperties(TypedDict, total=False):
    """
    These properties are used throughout the Ours app to pass known values onto destinations
    """

    active_duration: Annotated[Optional[float], PropertyInfo(alias="activeDuration")]
    """The active time in milliseconds that the user had this tab active"""

    ad_id: Optional[str]
    """The ad id for detected in the session.

    This is set by the web sdk automatically.
    """

    adset_id: Optional[str]
    """The adset id for detected in the session.

    This is set by the web sdk automatically.
    """

    alart: Optional[str]
    """The AppLovin alart query parameter. Ex: alart123"""

    aleid: Optional[str]
    """The AppLovin aleid query parameter. Ex: aleid123"""

    basis_cid: Optional[str]
    """The Basis DSP Click ID. Ex: basis_cid123"""

    browser_language: Optional[str]
    """The language of the browser. Ex: en-US"""

    browser_name: Optional[str]
    """The name of the browser. Ex: Chrome"""

    browser_version: Optional[str]
    """The version of the browser. Ex: 114.0"""

    campaign_id: Optional[str]
    """The campaign id for detected in the session.

    This is set by the web sdk automatically.
    """

    clickid: Optional[str]
    """The Click ID. Ex: clickid123"""

    clid: Optional[str]
    """The Generic Click ID. Ex: clid123"""

    cpu_architecture: Optional[str]
    """The architecture of the CPU. Ex: x64"""

    current_url: Optional[str]
    """The full url (including query params) of the current page"""

    dclid: Optional[str]
    """The DoubleClick Click ID. Ex: dclid123"""

    device_model: Optional[str]
    """The model of the device. Ex: iPhone 13"""

    device_type: Optional[str]
    """The type of device the user is using. Ex: mobile"""

    device_vendor: Optional[str]
    """The vendor of the device. Ex: Apple"""

    duration: Optional[float]
    """The time in milliseconds since the page was loaded // script was loaded"""

    encoding: Optional[str]
    """The browsers encoding. Ex: UTF-8"""

    engine_name: Optional[str]
    """The name of the browser engine. Ex: Blink"""

    engine_version: Optional[str]
    """The version of the browser engine. Ex: 114.0"""

    epik: Optional[str]
    """The Pinterest Click ID. Ex: epik456"""

    fbc: Optional[str]
    """Facebook Click ID with prefix format for Conversions API tracking.

    Ex: fb.1.1554763741205.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
    """

    fbclid: Optional[str]
    """Raw Facebook Click ID query parameter without prefix from ad clicks.

    Ex: AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
    """

    fbp: Optional[str]
    """Facebook Browser ID parameter for identifying browsers and attributing events.

    Ex: fb.1.1554763741205.1098115397
    """

    fv: Optional[bool]
    """Deprecated"""

    gad_source: Optional[str]
    """The Google Ad Source. Ex: google"""

    gbraid: Optional[str]
    """The Google Braid ID. Ex: gbraid123"""

    gclid: Optional[str]
    """The Google Click ID. Ex: gclid123"""

    host: Optional[str]
    """The host of the current page. Ex: example.com"""

    iframe: Optional[bool]
    """Whether the user is in an iframe. Ex: true"""

    im_ref: Optional[str]
    """The Impact Click ID reference. Ex: im_ref123"""

    ip: Optional[str]
    """The IP address of the user. Ex: 127.0.0.1"""

    irclickid: Optional[str]
    """The Impact Click ID. Ex: irclickid123"""

    is_bot: Optional[str]
    """Whether we have detected that the user is a bot.

    This is set automatically by the Ours server primarily for events tracked
    through the web SDK.
    """

    li_fat_id: Optional[str]
    """The LinkedIn Click ID. Ex: li_fat_id123"""

    msclkid: Optional[str]
    """The Microsoft Click ID. Ex: msclkid123"""

    ndclid: Optional[str]
    """The NextDoor Click ID. Ex: ndclid123"""

    new_s: Optional[bool]
    """Deprecated"""

    os_name: Optional[str]
    """The name of the operating system. Ex: Windows"""

    os_version: Optional[str]
    """The version of the operating system. Ex: 10.0"""

    page_hash: Optional[float]
    """A random set of numbers for the page load"""

    pathname: Optional[str]
    """The pathname of the current page. Ex: /home"""

    qclid: Optional[str]
    """The Quora Click ID. Ex: qclid123"""

    rdt_cid: Optional[str]
    """The Reddit Click ID. Ex: rdt_cid123"""

    received_at: Optional[str]
    """The time the event was received by an Ours server in ISO format"""

    referrer: Optional[str]
    """The referrer URL of the current page"""

    referring_domain: Optional[str]
    """The referring domain of the current page"""

    sacid: Optional[str]
    """The StackAdapt Tracking ID. Ex: sacid123"""

    sccid: Optional[str]
    """The SnapChat Click ID. Ex: sccid123"""

    screen_height: Optional[float]
    """The height of the screen. Ex: 1080"""

    screen_width: Optional[float]
    """The width of the screen. Ex: 1920"""

    session_count: Annotated[Optional[float], PropertyInfo(alias="sessionCount")]
    """The number of sessions the user has had. Ex: 3"""

    sid: Optional[str]
    """The session ID as assigned automatically by the web SDK.

    This is required for session replay
    """

    sr: Optional[str]

    title: Optional[str]
    """The title of the current page"""

    ttclid: Optional[str]
    """The TikTok Click ID. Ex: ttclid123"""

    twclid: Optional[str]
    """The Twitter Click ID. Ex: twclid123"""

    uafvl: Optional[str]
    """User agent as a full list of strings."""

    user_agent: Optional[str]
    """The user agent of the browser"""

    utm_campaign: Optional[str]
    """The UTM Campaign.

    The web SDK automatically captures this from the query params.
    """

    utm_content: Optional[str]
    """The UTM Content. The web SDK automatically captures this from the query params."""

    utm_medium: Optional[str]
    """The UTM Medium. The web SDK automatically captures this from the query params."""

    utm_name: Optional[str]
    """The UTM Name. The web SDK automatically captures this from the query params."""

    utm_source: Optional[str]
    """The UTM Source. The web SDK automatically captures this from the query params."""

    utm_term: Optional[str]
    """The UTM Term. The web SDK automatically captures this from the query params."""

    version: Optional[str]
    """The version of the web SDK"""

    wbraid: Optional[str]
    """The WBRAID Identifier.

    The web SDK automatically captures this from the query params.
    """

    webview: Optional[bool]
    """Whether the user is in a webview. Ex: true"""
