from typing import Self

from ._consts import JF_USERNAME
from ._consts import JF_PASSWORD
from ._consts import JF_ACTIVATION_CODE
from ._consts import JF_ID
from ._consts import JF_EMAIL
from ._consts import JF_ACCESS_TOKEN
from ._consts import JF_REFRESH_TOKEN
from ._consts import JF_EXPIRATION

from ._curli import Curli
from ._decorators import deprecated
from ._utils import to_datetime, get_now

class Agent:
    """The Agent object class wraps some of the operations of authenticating users and 
    switching between these accounts during interactions.

    Properties:
    - `ACCOUNT_AUTH_FIELDS`: The names of the fields containing user authentication
        information of an account.
        In which:

        * id: Unique identifier of the user in the system (usually a UUID code).
        * email: Unique email address of the user, this is also the login name.
        * access_token: Access code according to the JWT protocol.
        * refresh_token: Secret code used to refresh the access_token.
        * expiration: Time when the access_token code expires. The access_token must
            be refreshed before this time.
    """

    ACCOUNT_AUTH_FIELDS = [JF_ID, JF_EMAIL, JF_ACCESS_TOKEN, JF_REFRESH_TOKEN, JF_EXPIRATION]

    def __init__(self, curli: Curli):
        self._curli = curli

    def as_account(self, *args, **kwargs) -> Self:
        self._curli.as_account(*args, **kwargs)
        return self

    def in_session(self, *args, **kwargs) -> Self:
        self._curli.in_session(*args, **kwargs)
        return self

    @property
    def _account(self):
        return getattr(self._curli, "_account")

    @property
    def _session(self):
        return getattr(self._curli, "_session")

    def is_authenticated(self) -> bool:
        for required_field in [JF_ACCESS_TOKEN, JF_REFRESH_TOKEN, JF_EXPIRATION]:
            if required_field not in self._account:
                return False
        return True

    def is_still_valid(self) -> bool | None:
        if not self.is_authenticated():
            return None
        expires = to_datetime(self._account.get(JF_EXPIRATION))
        if expires <= get_now():
            return False
        return True

    @deprecated
    def auth(self, *args, **kwargs):
        return self.login(*args, **kwargs)

    def login(self, username = None, password = None, json = None, url:str = "auth/login", **kwargs):
        body = json if isinstance(json, dict) else dict()

        if username:
            body[JF_USERNAME] = username
        if password:
            body[JF_PASSWORD] = password

        kwargs = dict(filter(lambda item: item[0] != 'json', kwargs.items()))
        kwargs.update(access_token=None)

        r = self._curli.post(url, json = body, **kwargs)

        if r.is_success:
            self.as_account(**self._extract_cached(r))

        return r

    def _extract_cached(self, r):
        body = r.json()
        params = {key: body[key] for key in self.ACCOUNT_AUTH_FIELDS if key in body}
        for field_name in [JF_ID, JF_ACCESS_TOKEN]:
            self._check_available(params, field_name)
        return params

    def _check_available(self, data, field_name):
        if field_name not in data:
            raise RuntimeError(f"{ field_name } not found")
        field_value = data.get(field_name)
        if field_value is None:
            raise RuntimeError(f"{ field_name } is null")
        if not field_value:
            raise RuntimeError(f"{ field_name } is empty")

    def change_password(self, current_password, new_password, url:str = "auth/change-password", **kwargs):
        return self._curli.post(url,
                json=dict(current_password=current_password, new_password=new_password),
                **kwargs)

    def refresh_token(self, url:str = "auth/refresh-token", **kwargs):
        email = self._account.get(JF_EMAIL)
        if not email:
            raise RuntimeError(f"{ JF_EMAIL } not found")

        refresh_token = self._account.get(JF_REFRESH_TOKEN)
        if not refresh_token:
            raise RuntimeError(f"{ JF_REFRESH_TOKEN } not found")

        r = self._curli.post(url, json=dict(email=email, refresh_token=refresh_token), **kwargs)

        if r.is_success:
            self.as_account(**self._extract_cached(r))

        return r

    def logout(self, url:str = "auth/logout", **kwargs):
        r = self._curli.get(url, **kwargs)
        if r.is_success:
            self.as_account(access_token = None)
        return r

    def activate_user_id(self, user_id, password = None, url:str = "auth/activate", **kwargs):
        """Any user excepts anon & root could use this API to activate his account
        """
        backup_profile = self._account.profile
        user_response = self._curli.as_account("root").get("user/" + user_id)
        self._curli.as_account(backup_profile)
        activation_code = user_response.json().get(JF_ACTIVATION_CODE)
        return self.activate(activation_code, password, url=url, **kwargs)

    def activate(self, activation_code, password = None, url:str = "auth/activate", **kwargs):
        r = self._curli.post(url, json = dict(activation_code=activation_code, password=password),
                access_token=None, **kwargs)
        return r
