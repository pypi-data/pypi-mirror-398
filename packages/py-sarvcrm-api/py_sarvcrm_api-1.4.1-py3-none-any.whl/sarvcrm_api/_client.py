import json, hashlib, requests, requests_cache, urllib.parse
from classmods import ENVMod, logwrap
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Self
from .modules import SarvModule
from ._exceptions import SarvException
from ._mixins import ModulesMixin
from ._type_hints import TimeOutputMethods, SarvLanguageType, RequestMethod, SarvGetMethods
from ._url import SarvURL, SarvFrontend


class SarvClient(ModulesMixin):
    """
    SarvClient provides methods for interacting with the SarvCRM API. 
    It supports authentication, data retrieval, and other API functionalities.
    """
    @ENVMod.register(section_name='SarvClient')
    @logwrap(before=('DEBUG','Initiating SarvClient'), after='Initiating compleated')
    def __init__(
            self,
            utype: str,
            username: str,
            password: str,
            is_password_md5: bool = False,
            url: Optional[str] = None,
            frontend_url: Optional[str] = None,
            login_type: Optional[str] = None,
            auto_login: bool = True,
            language: SarvLanguageType = 'en_US',
            caching: bool = False,
            cache_backend: Literal['memory', 'sqlite'] = 'memory',
        ) -> None:
        """
        Initialize the SarvClient.

        Args:
            utype (str): The user type for authentication.
            username (str): The username for authentication.
            password (str): The password for authentication.
            is_password_md5 (bool): Whether the password is already hashed using MD5.
            url (Optional[str]): The base URL for the SarvCRM API if you use local instance.
            frontend_url (Optional[str]): The base URL for the SarvCRM frontend if you use local instance.
            login_type (Optional[str]): The login type for authentication.
            auto_login (bool): Try to login once on status code 401, 403
            language (SarvLanguageType): The language to use, default is 'en_US'.
            caching (bool): Cache the responses from server.
            cache_backend(Literal['memory', 'sqlite']): Saving backend for cached responses.
        """
        self._utype = utype
        self._username = username
        self._password = password if is_password_md5 else self.hash_password(password)
        self._url = url or SarvURL
        self._frontend_url = frontend_url or SarvFrontend
        self._login_type = login_type
        self._auto_login = auto_login
        self._language = language
        self._caching = caching
        self._cache_backend = cache_backend

        self._token: str = ''

        self.enable_caching() if self._caching else self.disable_caching()

        super().__init__()
        self._user_id: str | None = None

    @property
    def user_id(self) -> str:
        if not self._user_id:
            self._user_id = self.Users.get_me(selected_fields=['id']).get('id', '')

        assert self._user_id, 'Unable to retrive user_id from server.'
        return self._user_id

    @logwrap(before=False, after=('DEBUG','Added Headers to Session'))
    def _add_headers(self) -> None:
        """
        Adds required sarvcrm headers to session.
        """
        self._session.headers.update({'Content-Type': 'application/json'})
        self._session.headers.update({'Accept': 'application/json'})

    @logwrap(before=False, after=('INFO', 'Enabled caching'))
    def enable_caching(self) -> None:
        """
        Enables the caching and replaces `Session` with `CachedSession` or creates it.
        """
        self._session = requests_cache.CachedSession(
            cache_name='sarv_api_cache',
            backend=self._cache_backend,
            allowable_methods=('GET', 'POST'),
            allowable_codes=(200,),
        )
        self._add_headers()

    @logwrap(before=False, after=('INFO', 'Disabled caching'))
    def disable_caching(self) -> None:
        """
        Disables the caching and replaces `CachedSession` with `Session` or creates it.
        """
        self._session = requests.Session()
        self._add_headers()

    @logwrap(before='Sending HTTP request: args:{args} - kwargs:{kwargs}', after=False)
    def _send_request(
            self, 
            request_method: RequestMethod,
            endpoint: Optional[str] = None,
            head_params: Optional[dict] = None,
            get_params: Optional[dict] = None,
            post_params: Optional[dict] = None,
            auto_login: Optional[bool] = None,
            caching: bool = False,
            expire_after: int = 300,
        ) -> Any:
        """
        Send a request to the Sarv API and return the response data.

        Args:
            request_method (RequestMethod): The HTTP method for the request ('GET', 'POST', etc.).
            head_parms (dict): The headers for the request.
            get_parms (dict): The GET parameters for the request.
            post_params (dict): The POST parameters for the request.
            auto_login (Optional(bool)): Whether to auto login on status code 401, 403.
            caching (bool, optional): Whether to cache the results.
            expire_after (int, optional): The time in seconds to cache the results.

        Returns:
            Any: The data parameter from the server response that can be `List` or `Dict`

        Raises:
            SarvException: If the server returns an error response.
        """
        head_params = head_params or {}
        get_params = get_params or {}
        post_params = post_params or {}

        head_params = {k: v for k, v in head_params.items() if v is not None} 
        get_params = {k: v for k, v in get_params.items() if v is not None}
        post_params = {k: v for k, v in post_params.items() if v is not None}

        auto_login = auto_login if auto_login is not None else self._auto_login

        if self._token:
            head_params['Authorization'] = f'Bearer {self._token}'

        kwargs = {
            'method': request_method,
            'url': urllib.parse.urljoin(self._url.rstrip('/') + '/', (endpoint or '').lstrip('/')),
            'headers': head_params,
            'params': get_params,
            'json': post_params,
            'verify': True,
        }

        if isinstance(self._session, requests_cache.CachedSession):
            ## Use cache
            if caching:
                kwargs.update({'expire_after': expire_after})
                response: requests.Response = self._session.request(**kwargs)

            ## If caching enabled but user dont want to use it
            else:
                with self._session.cache_disabled():
                    response: requests.Response = self._session.request(**kwargs)

        else:
            ## Normal request without caching
            response: requests.Response = self._session.request(**kwargs)

        # Check for Server respond
        try:
            # Deserialize sarvcrm servers response
            response_dict: dict = response.json()

        # This is for quirky responses from Sarvcrm servers
        # Sometimes servers send other content types instead of json
        except json.decoder.JSONDecodeError:
            if 'MySQL Error' in response.text:
                raise SarvException(
                    'There are Errors in the database\n'
                    'if you are sending raw SQL Query to server\n'
                    'please check syntax and varible names'
                )
            else:
                raise SarvException(
                    'Unkhown error from Server while parsing json'
                )

        try:
            response.raise_for_status()

        except requests.HTTPError as e:
            if not (auto_login and response.status_code in (401, 403)):
                raise e

            head_params.pop('Authorization', None)
            self.login()

            return self._send_request(
                request_method=request_method,
                endpoint=endpoint,
                head_params=head_params,
                get_params=get_params,
                post_params=post_params,
                auto_login=False,
                caching=False,
            )

        return response_dict.get('data', {})

    @logwrap(before=('INFO', 'Logging to Sarvcrm'), after=False)
    def login(self) -> str:
        """
        Authenticate the user and retrieve an access token.

        Returns:
            str: The access token for authenticated requests.
        """
        post_params = {
            'utype': self._utype,
            'user_name': self._username,
            'password': self._password,
            'login_type': self._login_type,
            'language': self._language,
        }

        response: Dict[str, Any] = self._send_request(
            request_method='POST',
            get_params=self._create_get_params('Login'), 
            post_params=post_params,
            caching=False,
            auto_login=False,
        )

        self._token = response['token']

        return self._token

    @logwrap(before=('INFO', 'Logging out from Sarvcrm'), after=False)
    def logout(self) -> None:
        """
        Clears the access token from the instance.

        This method should be called to invalidate the session.
        """
        if self._token:
            self._token = ''

    @logwrap(before='Searching by number: args:{args} - kwargs:{kwargs}', after=False)
    def search_by_number(
            self,
            number: str,
            module: Optional[SarvModule | str] = None,
            caching: bool = False,
            expire_after: int = 300,
        ) -> List[Dict[str, Any]]:
        """
        Search the CRM by phone number and retrieve the module item.

        Args:
            number (str): The phone number to search for.
            module (Optional[SarvModule | str]): The module to search in.
            caching (bool, optional): Whether to cache the results.
            expire_after (int, optional): The time in seconds to cache the results.

        Returns:
            dict: The data related to the phone number if found.
        """
        return self._send_request(
            request_method = 'GET',
            get_params = self._create_get_params(
                'SearchByNumber', 
                sarv_module = module, 
                number = number,
                caching = caching,
                expire_after = expire_after,
            ),
        )

    @staticmethod
    def _create_get_params(
            sarv_get_method: Optional[SarvGetMethods] = None,
            sarv_module: Optional[SarvModule | str] = None,
            **addition
        ) -> Dict[str, Any]:
        """
        Create the GET parameters with the method and module.

        Args:
            sarv_get_method (SarvGetMethods): The API method to call.
            sarv_module (Optional[SarvModule | str]): The module name or object.
            addition: Additional parameters to include in the GET request.

        Returns:
            dict: The constructed GET parameters.
        """
        module_name = None

        if sarv_module is not None:
            if isinstance(sarv_module, SarvModule):
                module_name = sarv_module._module_name
            elif isinstance(sarv_module, str):
                module_name = sarv_module
            else:
                raise TypeError(f'Module type must be instance of SarvModule or str not {sarv_module.__class__.__name__}')

        get_parms = {
            'method': sarv_get_method,
            'module': module_name,
        }

        if addition:
            get_parms.update(**addition)

        return get_parms

    @staticmethod
    def iso_time_output(
            output_method: TimeOutputMethods,
            dt: datetime | timedelta,
        ) -> str:
        """
        Generate a formatted string from a datetime or timedelta object.

        These formats are compliant with the SarvCRM API time standards.

        Args:
            output_method (TimeOutputMethods): Determines the output format ('date', 'datetime', or 'time').
            dt (datetime | timedelta): A datetime or timedelta object.

        Returns:
            str: A string representing the date, datetime, or time.
                - date: "YYYY-MM-DD"
                - datetime: "YYYY-MM-DDTHH:MM:SS+HH:MM"
                - time: "HH:MM:SS"
        """
        if isinstance(dt, timedelta):
            dt = datetime.now(timezone.utc) + dt

        if output_method == 'date':
            return dt.date().isoformat()

        elif output_method == 'datetime':
            return dt.astimezone().isoformat(timespec="seconds")

        elif output_method == 'time':
            return dt.time().isoformat(timespec="seconds")

        else:
            raise TypeError(f'Invalid output method: {output_method}')

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Returns the acceptable hash for SarvCRM Login

        Args:
            password(str): your password
        
        Returns:
            str: md5 hashed password
        """
        return hashlib.md5(password.encode('utf-8')).hexdigest()

    @logwrap(before='Starting SarvClient context.', after=('DEBUG', 'SarvClient context started.'))
    def __enter__(self) -> Self:
        """Basic Context Manager for clean code execution"""
        if not self._token:
            self.login()

        return self

    @logwrap(before='Closing SarvClient context.', after=('DEBUG', 'SarvClient context closed.'))
    def __exit__(self, exc_type, exc_value, traceback):
        """Basic Context Manager for clean code execution"""
        self.logout()

    def __repr__(self):
        """
        Provides a string representation for debugging purposes.

        Returns:
            str: A string containing the class name and key attributes.
        """
        return f'{self.__class__.__name__}(utype={self._utype}, username={self._username})'

    def __str__(self) -> str:
        """
        Provides a human-readable string representation of the instance.

        Returns:
            str: A simplified string representation of the instance.
        """
        return f'<SarvClient {self._utype}-{self._username}>'