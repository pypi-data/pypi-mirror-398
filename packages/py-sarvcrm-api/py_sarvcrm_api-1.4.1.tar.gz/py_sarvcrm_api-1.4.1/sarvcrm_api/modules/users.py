from classmods import logwrap
from typing import Any, Optional
from ._base import SarvModule
from ._mixins import UrlMixin

class Users(SarvModule, UrlMixin):
    _module_name = 'Users'
    _table_name = 'users'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Users'
    _label_pr = 'کاربران'

    @logwrap(before='Reading currnet user detail: args:{args} - kwargs:{kwargs}', after=False)
    def get_me(
            self, 
            selected_fields: Optional[list[str]] = None,
            caching: bool = False,
            expire_after: int = 300,
        ) -> dict[str, Any]:
        """
        Returns current user details.

        Args:
            selected_fields (list[str], optional): A list of fields to include in the response.
            caching (bool, optional): Whether to cache the results.
            expire_after (int, optional): The time in seconds to cache the results.
        
        Returns:
            dict: Users data
        """
        return self.read_list(
            query=f"users.user_name='{self._client._username.lower()}'",
            selected_fields=selected_fields,
            limit=1,
            caching=caching,
            expire_after=expire_after,
        )[0]