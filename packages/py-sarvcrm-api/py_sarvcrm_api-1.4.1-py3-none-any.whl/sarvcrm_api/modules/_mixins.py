from typing import Any, Optional


class UrlMixin:
    """
    Class Mixin for Managing URL Generation in this module
    """
    _client: Any
    _module_name: str

    def get_url_edit_view(self, pk: Optional[str] = None) -> str:
        """
        Returns Edit View of the Module or Create View of the Module.
        if pk is not provided returns Create View.
        
        Args:
            pk (Optional[str]): The unique identifier (ID) of the item for URL creation.
        
        Returns:
            specified URL.
        """
        return f"{self._client._frontend_url}?utype={self._client._utype}&module={self._module_name}&action=EditView{'&record=' + pk if pk else ''}"

    def get_url_list_view(self) -> str:
        """
        Returns List View of the Module.
        
        Returns:
            specified URL.
        """
        return f'{self._client._frontend_url}?utype={self._client._utype}&module={self._module_name}&action=ListView'

    def get_url_detail_view(self, pk: str) -> str:
        """
        Returns the Detail View of the specified record with ID.

        Args:
            pk (str): The unique identifier (ID) of the item for URL creation.
        
        Returns:
            specified URL.
        """
        return f'{self._client._frontend_url}?utype={self._client._utype}&module={self._module_name}&action=DetailView&record={pk}'
