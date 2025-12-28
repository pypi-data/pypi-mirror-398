r"""A Python Client for the API of ONCat, the ORNL Neutron Catalog.

This package provides several convenience classes and methods which will
help to more easily interact with the ONCat API from Python.

For a complete description of this module, please see the documentation
hosted at https://oncat.ornl.gov.
"""

from __future__ import annotations

import functools
import getpass
import json
import os
import pathlib
import warnings
import weakref
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Literal
from urllib.parse import quote

import oauthlib.oauth2
import requests
import requests_oauthlib
import urllib3
from oauthlib.oauth2 import rfc6749
from urllib3.exceptions import InsecureRequestWarning

from pyoncat.reduction import ReductionFileBuilder

__version__ = "2.4"

# Constant for autoreduction user
AUTOREDUCTION_USER = "auto"

__all__ = [
    "AUTOREDUCTION_USER",
    "FileSystemTokenStore",
    "ONCat",
    "ONCatObject",
    "PyONCatError",
    "ReductionFileBuilder",
    "prompt_user_for_login",
]


########################################################################
# Client
########################################################################


FlowType = Literal[
    "client_credentials",
    "resource_owner",
]
CLIENT_CREDENTIALS_FLOW: FlowType = "client_credentials"
RESOURCE_OWNER_CREDENTIALS_FLOW: FlowType = "resource_owner"


assert isinstance(CLIENT_CREDENTIALS_FLOW, str)


class ONCat:
    """The ONCat API client.

    This class is the main entry point for interacting with the ONCat
    API.  It aims to provide a slightly higher level of abstraction than
    simply making raw GET, POST, PUT, and DELETE requests to the API,
    and also wraps the relatively complex authentication logic that is
    required to interact with most of the API.

    Once instantiated correctly, the client object provides a set of
    standardized sub-objects that represent the various resources that
    are available in the API and the actions that can be taken on them.

    Calling actions on a resource takes the following form:

        client.Resource.action()

    For example, to list all the facilities in the API, you would call:

        client.Facility.list()

    The client will automatically handle the authentication and
    authorization required to make the request, and will raise an
    exception if the request is not successful.

    Various parameters can be passed to the actions to modify the
    behaviour of the underlying request, such as query parameters, data
    to be sent in the body of the request, etc.

    A more complex example would be to return a list of each run title
    contained in all the raw NeXus files acquired at ARCS:

        oncat.Datafile.list(
            facility="SNS",
            instrument="ARCS",
            projection=["metadata.entry.title"],
            tags=["type/raw"],
            exts=[".nxs.h5"],
        )

    A full explanation of each resource and the actions that can be
    taken on them can be found in the ONCat API documentation.


    Arguments:
    ---------
        url: str
            The base URL of the ONCat API.

        client_id: str | None
            The client ID for the OAuth client, required if you are
            using an OAuth flow to authenticate.

        client_secret: str | None
            The client secret for the OAuth client, which may be
            required alongside the client ID if you are using one.

        token_getter: Callable[[], dict | None] | None
            An optional function that will be used to load the current
            OAuth token if one exists, else `None`.

        token_setter: Callable[[dict | None], None] | None
            An optional function that will be used to save the current
            OAuth token, to be retrieved later by the `token_getter`.

        login_prompt: Callable[[], Tuple[str, str]] | None
            An optional function that will prompt the user for their
            username and password when appropriate, as per the OAuth
            flow being used.

        api_token: str | None
            An optional API token that can be used by select clients to
            authenticate requests to the API as an alternative to OAuth.

        flow: FlowType | None
            The OAuth "flow" to use for authentication.  Required if you
            are using OAuth.

        scopes: List[str] | None
            The OAuth scopes that this client should have access to.
            If using OAuth and a scope is not provided, then will
            default server-side to `"api:read"`.  Please see the ONCat
            API documentation for more information on the scopes that
            are required for each resource.

        verify: bool
            Whether or not to verify the SSL certificate of the server
            when making requests.  `True` by default and absolutely
            required in production, setting this to `False` can be
            useful for development or testing purposes.

        timeout: int | None
            The number of seconds to wait for a response from the server
            before timing out.  `None` by default, which means that the
            client will wait indefinitely for a response, as per the
            underlying behavior of the `requests` module.

    """

    if TYPE_CHECKING:
        Facility: Facility
        Instrument: Instrument
        Experiment: Experiment
        Run: Run
        Scan: Scan
        Sample: Sample
        Group: Group
        Grouping: Grouping
        Mapping: Mapping
        Proposal: Proposal
        Item: Item
        Archive: Archive
        Cycle: Cycle
        Datafile: Datafile
        Reduction: Reduction
        Simulation: Simulation
        User: User
        Task: Task
        Info: Info
        CacheEntry: CacheEntry
        UsageEntry: UsageEntry
        Template: Template

    def __init__(
        self,
        url: str,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_getter: Callable[[], dict | None] | None = None,
        token_setter: Callable[[dict | None], None] | None = None,
        login_prompt: Callable[[], tuple[str, str]] | None = None,
        api_token: str | None = None,
        flow: FlowType | None = None,
        scopes: list[str] | None = None,
        verify: bool = True,
        timeout: int | None = None,
    ):
        if not url:
            msg = "A URL must be provided."
            raise ValueError(msg)

        using_oauth = (
            client_id is not None
            or client_secret is not None
            or token_getter is not None
            or token_setter is not None
            or login_prompt is not None
            or flow is not None
            or scopes is not None
        )

        if using_oauth:
            if not flow:
                msg = "A flow must be provided when using OAuth."
                raise ValueError(msg)
            if not client_id:
                msg = "A client ID must be provided when using OAuth."
                raise ValueError(msg)
            if api_token:
                msg = "An API token cannot be used when using OAuth."
                raise ValueError(msg)
            if client_secret and not client_id:
                msg = "A client secret must be paired with a client ID."
                raise ValueError(msg)
            if token_getter and not token_setter:
                msg = "A token getter must be paired with a token setter."
                raise ValueError(msg)
            if token_setter and not token_getter:
                msg = "A token setter must be paired with a token getter."
                raise ValueError(msg)

        self._token_getter = token_getter
        self._token_setter = token_setter
        self._login_prompt = login_prompt
        self._api_token = api_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._url = url
        self._flow = flow
        self._scopes: list[Any] | None = scopes
        self._verify = verify
        self._timeout = timeout

        self._token = None
        self._oauth_client = None

        for resource_cls in _ONCatMixinMeta.REGISTERED_RESOURCES:
            setattr(self, resource_cls.__name__, resource_cls(self))

    def _get(self, url: str, **kwargs):
        return self._call_method("get", url, None, **kwargs)

    def _put(self, url: str, data: Any, **kwargs):
        result = self._call_method("put", url, data, **kwargs)

        # Not all resources will return a confirmation representation.
        return result if result != "" else None

    def _post(self, url: str, data: Any, **kwargs):
        return self._call_method("post", url, data, **kwargs)

    def _delete(self, url: str, **kwargs):
        self._call_method("delete", url, None, **kwargs)

    def _call_method(self, method, url, data, **kwargs):
        url = quote(url)
        full_url = (
            self._url + url if url.startswith("/") else self._url + "/" + url
        )

        def send_request():
            if self._client_id:
                response = getattr(self._load_oauth_client(), method)(
                    full_url,
                    params=kwargs,
                    json=data,
                    verify=self._should_verify(),
                    timeout=self._timeout,
                )
            else:
                response = getattr(requests, method)(
                    full_url,
                    params=kwargs,
                    json=data,
                    verify=self._should_verify(),
                    headers={"Authorization": "Bearer " + self._api_token}
                    if self._api_token
                    else None,
                    timeout=self._timeout,
                )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as error:
                if error.response.status_code == 400:
                    msg = "Bad request"
                    raise BadRequestError(msg) from error
                if error.response.status_code == 401:
                    msg = f'Not authorized to access "{full_url}"'
                    raise UnauthorizedError(msg) from error
                if error.response.status_code == 404:
                    msg = f'Could not find resource at "{full_url}"'
                    raise NotFoundError(msg) from error
                msg = f'Error: "{error!s}"'
                raise PyONCatError(msg) from error

            try:
                return response.json()
            except ValueError:
                return response.text

        try:
            return send_request()
        except rfc6749.errors.InvalidGrantError as error:
            if (
                self._flow == RESOURCE_OWNER_CREDENTIALS_FLOW
                and "(invalid_grant)" in str(error)
                and "unknown, invalid, or expired refresh token" in str(error)
            ):
                self._save_token(None)
                if self._login_prompt:
                    self.login()
                    return send_request()
                msg = (
                    "It looks like you've tried to use a refresh token "
                    "that has expired.  Not to worry -- this is part of "
                    "the normal OAuth workflow when using refresh tokens, "
                    "since by default (and on a client-by-client basis) "
                    "they are set to expire after a certain length of "
                    "time.  You should be catching this error in your "
                    "client code and then re-prompting the user for their "
                    "username and password so that you may proceed with "
                    "your calls to the ONCat API.\n\n"
                )
                raise InvalidRefreshTokenError(msg) from error
            msg = f'Error: "{error!s}"'
            raise PyONCatError(msg) from error
        except oauthlib.oauth2.TokenExpiredError as error:
            if self._flow == CLIENT_CREDENTIALS_FLOW:
                self.login()
                return send_request()
            msg = f'Error: "{error!s}"'
            raise PyONCatError(msg) from error

    def _load_oauth_client(self):
        if not self._oauth_client:
            self.login()

        return self._oauth_client

    def _load_token(self):
        if self._token_getter is not None:
            return self._token_getter()

        return self._token

    def _save_token(self, token):
        if self._token_setter is not None:
            self._token_setter(token)
        else:
            self._token = token

    def _should_verify(self):
        if not self._verify:
            return False

        if (
            "localhost" in self._url
            or "load-balancer" in self._url
            or "proxy" in self._url
        ):
            # Ignore invalid certs and lack of SSL for OAuth if
            # deploying locally.
            urllib3.disable_warnings(InsecureRequestWarning)
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        return (
            "localhost" not in self._url
            and "load-balancer" not in self._url
            and "proxy" not in self._url
        )

    def login(self, username=None, password=None):
        """Login to the ONCat API as part of an appropriate OAuth flow.

        This method is no longer strictly necessary to call manually,
        since if you have specified a login prompt callback or you are
        using the "client credentials" flow, then the client will login
        automatically when it needs to.

        However, if you are using the "resource owner credentials" flow
        and you have not provided a login prompt callback (or have not
        previously logged in and stored a token which is still active),
        then you will need to call this method manually to login.

        Arguments:
        ---------
            username: str | None
                The username to use when logging in.

            password: str | None
                The password to use when logging in.

        """
        if self._flow == CLIENT_CREDENTIALS_FLOW:
            self._login_client_credentials()
        elif self._flow == RESOURCE_OWNER_CREDENTIALS_FLOW:
            if self._login_prompt:
                while True:
                    try:
                        if self._load_token() is not None:
                            self._login_resource_owner_credentials(None, None)
                        else:
                            username, password = self._login_prompt()
                            self._login_resource_owner_credentials(
                                username, password
                            )
                        break
                    except InvalidUserCredentialsError:
                        self._save_token(None)
            else:
                self._login_resource_owner_credentials(username, password)
        else:
            raise AssertionError

    def _login_client_credentials(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            assert self._client_id
            self._oauth_client = requests_oauthlib.OAuth2Session(
                client=oauthlib.oauth2.BackendApplicationClient(
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    scope=self._scopes,
                ),
                scope=self._scopes,
            )
        try:
            token = self._oauth_client.fetch_token(
                self._url + "/oauth/token",
                client_id=self._client_id,
                client_secret=self._client_secret,
                include_client_id=True,
                verify=self._should_verify(),
                scope=self._scopes,
                timeout=self._timeout,
            )

        except rfc6749.errors.InvalidClientError as error:
            msg = (
                "You seem to have provided some invalid client "
                "credentials.  Are you sure they are correct?"
            )
            raise InvalidClientCredentialsError(msg) from error

        self._save_token(token)

    def _login_resource_owner_credentials(self, username, password):
        if not username or not password:
            token = self._load_token()
            if not token:
                msg = (
                    "A username and/or password was not provided when logging "
                    "in."
                )
                raise LoginRequiredError(msg)
        else:
            assert self._client_id
            initial_oauth_client = requests_oauthlib.OAuth2Session(
                client=oauthlib.oauth2.LegacyApplicationClient(
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                )
            )

            try:
                token = initial_oauth_client.fetch_token(
                    self._url + "/oauth/token",
                    username=username,
                    password=password,
                    client_id=self._client_id,
                    client_secret=self._client_secret,
                    include_client_id=True,
                    verify=self._should_verify(),
                    scope=self._scopes,
                    timeout=self._timeout,
                )
                self._save_token(token)
            except rfc6749.errors.InvalidClientError as error:
                msg = (
                    "You seem to have provided some invalid client "
                    "credentials.  Are you sure they are correct?"
                )
                raise InvalidClientCredentialsError(msg) from error
            except rfc6749.errors.InvalidGrantError as error:
                if "(invalid_grant)" in str(
                    error
                ) and "username & password" in str(error):
                    msg = (
                        "The user seems to have provided an invalid "
                        "username and/or password.  They should be shown "
                        "an appropriate error message and prompted to try "
                        "again."
                    )
                    raise InvalidUserCredentialsError(msg) from error

                raise
        auto_refresh_kwargs = {
            "client_id": self._client_id,
            "verify": self._should_verify(),
        }
        if self._client_secret:
            auto_refresh_kwargs["client_secret"] = self._client_secret

        self._oauth_client = requests_oauthlib.OAuth2Session(
            self._client_id,
            token=token,
            scope=self._scopes,
            auto_refresh_url=self._url + "/oauth/token",
            auto_refresh_kwargs=auto_refresh_kwargs,
            token_updater=self._save_token,
        )


class ONCatObject:
    """A representation of a JSON object returned from the ONCat API.

    Note that in practice, this class should probably not be
    instantiated directly, but rather should only be returned by the
    ONCat client after a request is made to the API.

    This class is a convenience wrapper around a dictionary that
    represents a JSON object returned from the ONCat API.  All objects
    from the API are wrapped in this class before being returned.

    The class provides a way to access top-level fields as if they were
    attributes of the underlying dictionary, ways to access nested
    fields using dot-delimited string notation, as well as a way to list
    all the "nodes" in the (possibly nested) dictionary.

    For a complete description of this class, including example usage,
    please see the documentation on the ONCat website.

    Arguments:
    ---------
        content: A dictionary

    Attributes:
    ----------
        object: str
            The type of object that this represents (e.g. "facility",
            "experiment", etc.).

        id: Any
            The unique identifier for this object.

    """

    def __init__(self, content: dict | None = None):
        # TODO: Consider a better way to represent a `None` ONCat object
        # because not all responses will return a representation.
        self._content = content or {}

    def __repr__(self):
        # https://stackoverflow.com/a/2626364/778572
        ident_parts = [
            type(self).__name__,
            "object={}".format(self._content.get("object")),
            "id={}".format(self._content.get("id")),
        ]

        return "<{} at {}> JSON: {}".format(
            " ".join(ident_parts),
            hex(id(self)),
            str(self),
        )

    def __str__(self):
        return json.dumps(self._content, sort_keys=True, indent=4)

    def __getattr__(self, k) -> Any:
        if k[0] == "_":
            raise AttributeError(k)

        try:
            return self._content[k]
        except KeyError as e:
            raise AttributeError(*e.args) from e

    def __getitem__(self, key) -> Any:
        elements = key.split(".")
        current = elements[0]
        remainder = elements[1:] if len(elements) > 1 else None
        if isinstance(self._content[current], dict):
            value = ONCatObject(content=self._content[current])

            if remainder:
                remainder = ".".join(remainder)
                return value.__getitem__(remainder)
        elif remainder:
            raise KeyError(".".join(remainder))
        else:
            value = self._content[current]

        return value

    def to_dict(self) -> dict:
        """Return the underlying dictionary representation of the
        ONCatObject."""
        return self._content

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the ONCatObject.

        This method is similar to the `get` method of a dictionary, but
        it allows for dot-delimited string notation to access nested
        fields, e.g., `item.get("nested.field")` is roughly equivalent
        to `item.get("nested").get("field")` or
        `item["nested"]["field"]`.

        Arguments:
        ---------
            key: str
                The key to access in the ONCatObject.

            default: Any
                The value to return if the key is not found.

        Returns:
        -------
            The value of the key in the ONCatObject, or the default value
            if the key is not found.

        """
        try:
            return self[key]
        except KeyError:
            return default

    def nodes(
        self, root: str | None = None, include_branches: bool = False
    ) -> list[str]:
        """List all the "nodes" in the ONCatObject.

        This method returns a list of all the full paths that exist in
        the ONCatObject, which can be used to access the values that are
        contained within it.

        If a `root` is provided, only the keys that start with that
        string will be returned.

        If `include_branches` is set to `True`, then the keys that are
        dictionaries will also be returned, else only the keys that are
        not dictionaries (i.e., "leaves") will be returned.

        Arguments:
        ---------
            root: str
                The dot-delimited root path to filter the nodes by.

            include_branches: bool
                Whether or not to include the branch nodes.

        """
        result = sorted(_yield_nodes(self._content, None, include_branches))

        if root:
            # TODO: Not the most performant way of doing this...
            return [key for key in result if key.startswith(root)]
        return result


# Alias name for backwards compatibility.
ONCatRepresentation = ONCatObject


########################################################################
# Mixins
########################################################################


class _ONCatMixinMeta(type):
    REGISTERED_RESOURCES: ClassVar[list] = []

    def __init__(cls, *args):
        super().__init__(args)
        if not cls.__name__.startswith("_"):
            _ONCatMixinMeta.REGISTERED_RESOURCES.append(cls)


class _ONCatResource(metaclass=_ONCatMixinMeta):
    _NAMESPACE: str
    _RESOURCE_ENDPOINT: str

    def __init__(self, parent_oncat: ONCat):
        self._parent_oncat_weakref = weakref.ref(parent_oncat)

    @property
    def _parent(self) -> ONCat:
        parent = self._parent_oncat_weakref()
        if parent is None:
            msg = "ONCat client was garbage-collected"
            raise ReferenceError(msg)
        return parent

    def retrieve(self, identifier, **kwargs):
        oncat = self._parent

        identifier = identifier.removeprefix("/")

        path = f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}/{identifier}"

        return ONCatObject(content=oncat._get(path, **kwargs))


class _ListableONCatMixin(_ONCatResource):
    def list(self, **kwargs):
        oncat = self._parent

        path = f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}"

        return [
            ONCatObject(content=content)
            for content in oncat._get(path, **kwargs)
        ]


class _UpdatableONCatMixin(_ONCatResource):
    def place(self, identifier: str, data: Any, **kwargs):
        oncat = self._parent

        identifier = identifier.removeprefix("/")

        path = f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}/{identifier}"

        return ONCatObject(content=oncat._put(path, data, **kwargs))


class _CreatableONCatMixin(_ONCatResource):
    def create(self, data, **kwargs):
        oncat = self._parent

        path = f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}"

        return ONCatObject(content=oncat._post(path, data, **kwargs))


class _RemovableONCatMixin(_ONCatResource):
    def remove(self, identifier: str, **kwargs):
        oncat = self._parent

        identifier = identifier.removeprefix("/")

        path = f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}/{identifier}"

        oncat._delete(path, **kwargs)


class _ControllerONCatMixin(_ONCatResource):
    def __getattr__(self, k):
        if k[0] == "_":
            raise AttributeError(k)

        return functools.partial(self._controller, k)

    def _controller(self, name, *args, **kwargs):
        if len(args) == 0 or len(args) > 2:
            raise TypeError
        if len(args) == 1:
            if isinstance(args[0], str):
                identifier = args[0]
                data = None
            else:
                identifier = None
                data = args[0]
        elif len(args) == 2:
            if not isinstance(args[0], str):
                raise TypeError
            identifier = args[0]
            data = args[1]

        if identifier is not None and identifier.startswith("/"):
            identifier = identifier[1:]

        oncat = self._parent

        if identifier is not None:
            path = (
                f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}/"
                + f"{identifier}/{name}"
            )
        else:
            path = f"{self._NAMESPACE}/{self._RESOURCE_ENDPOINT}/{name}"

        return ONCatObject(content=oncat._post(path, data, **kwargs))


########################################################################
# Resources
########################################################################


class Facility(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "facilities"
    _NAMESPACE = "api"


class Instrument(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "instruments"
    _NAMESPACE = "api"


class Experiment(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "experiments"
    _NAMESPACE = "api"


class Run(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "runs"
    _NAMESPACE = "api"


class Scan(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "scans"
    _NAMESPACE = "api"


class Sample(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "samples"
    _NAMESPACE = "api"


class Group(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "groups"
    _NAMESPACE = "experimental"


class Grouping(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "groupings"
    _NAMESPACE = "api"


class Mapping(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "mappings"
    _NAMESPACE = "settings"


class Proposal(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "proposals"
    _NAMESPACE = "api"


class Item(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "items"
    _NAMESPACE = "api"


class Archive(
    _ListableONCatMixin, _RemovableONCatMixin, _ControllerONCatMixin
):
    _RESOURCE_ENDPOINT = "archives"
    _NAMESPACE = "api"


class Cycle(_ListableONCatMixin, _ControllerONCatMixin):
    _RESOURCE_ENDPOINT = "cycles"
    _NAMESPACE = "api"


class Datafile(
    _ControllerONCatMixin,
    _CreatableONCatMixin,
    _ListableONCatMixin,
    _RemovableONCatMixin,
):
    _RESOURCE_ENDPOINT = "datafiles"
    _NAMESPACE = "api"


class Reduction(
    _ControllerONCatMixin,
    _CreatableONCatMixin,
    _ListableONCatMixin,
    _RemovableONCatMixin,
):
    _RESOURCE_ENDPOINT = "reductions"
    _NAMESPACE = "api"


class Simulation(_ControllerONCatMixin, _ListableONCatMixin):
    _RESOURCE_ENDPOINT = "simulations"
    _NAMESPACE = "api"


class User(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "users"
    _NAMESPACE = "api"


class Task(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "tasks"
    _NAMESPACE = "api"


########################################################################


class Info(_ONCatResource):
    _RESOURCE_ENDPOINT = "info"
    _NAMESPACE = "data"


########################################################################


class CacheEntry(_UpdatableONCatMixin):
    _RESOURCE_ENDPOINT = "cache"
    _NAMESPACE = "admin"


class UsageEntry(_ListableONCatMixin):
    _RESOURCE_ENDPOINT = "usage"
    _NAMESPACE = "admin"


########################################################################


class Template(
    _CreatableONCatMixin, _ListableONCatMixin, _RemovableONCatMixin
):
    _RESOURCE_ENDPOINT = "templates"
    _NAMESPACE = "settings"


########################################################################
# Summary Resources
########################################################################


class ExperimentSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "experiment"
    _NAMESPACE = "summary"


class GroupingSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "grouping"
    _NAMESPACE = "summary"


class InstrumentSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "instrument"
    _NAMESPACE = "summary"


class ReductionSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "reduction"
    _NAMESPACE = "summary"


class RunSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "run"
    _NAMESPACE = "summary"


class SampleSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "sample"
    _NAMESPACE = "summary"


class ScanSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "scan"
    _NAMESPACE = "summary"


class SessionSummary(_ONCatResource):
    _RESOURCE_ENDPOINT = "session"
    _NAMESPACE = "summary"


########################################################################
# Misc Tools
########################################################################


class _InMemoryTokenStore:
    """A token store that persists OAuth tokens in memory only.

    This kind of store is only really useful for testing or as an
    example of the interface a token store should provide; in its
    current form it does not offer anything that the `ONCat` client
    itself does not already provide when leaving the getter and setter
    parameters empty.
    """

    def __init__(self):
        self._token = None

    def set_token(self, token: dict | None):
        self._token = token

    def get_token(self) -> dict | None:
        return self._token


class FileSystemTokenStore:
    """A token store that persists OAuth tokens to a file on disk.

    The file is created if it doesn't already exist, including any
    necessary parent directories. You must have write permissions to
    the parent directory else an exception will be raised.

    This kind of store may be useful for long-lived applications where
    you need to persist the token across uses of the client, and it is
    an instance of an application that is run by a single user.  This
    kind of store is not suitable for applications that have the
    expectation of being able to manage sessions for multiple users.

    Arguments:
    ---------
        path: str
            The path to the file where the token will be stored.

    """

    def __init__(self, path: str):
        self.path = path

    def read_token(self) -> dict | None:
        """Read the token from the file on disk, if it exists.

        Return:
        ------
            The token if it exists, else `None`.

        """
        if not os.path.exists(self.path):
            return None

        with open(self.path) as storage:
            return json.load(storage)

    def write_token(self, token: dict | None):
        """Write the token to the file on disk.

        Arguments:
        ---------
            token: str | None
                The token to write to the file, or `None` to clear the
                token.

        """
        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(self.path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(self.path, "w") as storage:
            json.dump(token, storage)


def prompt_user_for_login() -> tuple[str, str]:
    """Prompt the user for their login credentials via the command line."""
    print("Enter UCAMS / XCAMS...")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    return username, password


class _UserConfigFile:
    """Subject to change and NOT recommended for use by end-users."""

    def __init__(self, client_name, path=None):
        self._client_name = client_name
        self.path = (
            os.path.join(os.path.expanduser("~"), ".oncatrc")
            if path is None
            else path
        )

    def _content(self):
        with open(self.path) as user_config_file:
            return json.load(user_config_file)

    def client_id(self):
        return self._content()[self._client_name]["client_id"]

    def client_secret(self):
        return self._content()[self._client_name]["client_secret"]

    def token_getter(self):
        return self._content()[self._client_name].get("current_token", None)

    def token_setter(self, token):
        content = self._content()
        content[self._client_name]["current_token"] = token

        pathlib.Path(self.path).write_text(
            json.dumps(content, indent=4, sort_keys=True)
        )


########################################################################
# Helpers
########################################################################


def _yield_nodes(d, path, include_branches):
    for node in d:
        node_path = f"{path}.{node}" if path else node
        if isinstance(d[node], dict):
            if include_branches:
                yield node_path
            yield from _yield_nodes(d[node], node_path, include_branches)
        else:
            yield node_path


########################################################################
# Exceptions
########################################################################


class PyONCatError(Exception):
    """A base exception for all errors that may be raised by PyONCat."""


class UnauthorizedError(PyONCatError):
    """An error that is raised when the client is not authorized to
    access a resource.
    """


class InvalidClientCredentialsError(PyONCatError):
    """An error that is raised when the client credentials provided are
    invalid.
    """


class InvalidUserCredentialsError(PyONCatError):
    """An error that is raised when the user credentials provided are
    invalid.
    """


class InvalidRefreshTokenError(PyONCatError):
    """An error that is raised when the refresh token provided is
    invalid.
    """


class LoginRequiredError(PyONCatError):
    """An error that is raised when a login is required to access a
    resource.
    """


class NotFoundError(PyONCatError):
    """An error that is raised when a resource cannot be found."""


class BadRequestError(PyONCatError):
    """An error that is raised when a bad request is made to the API.

    Check your input and try again.
    """
