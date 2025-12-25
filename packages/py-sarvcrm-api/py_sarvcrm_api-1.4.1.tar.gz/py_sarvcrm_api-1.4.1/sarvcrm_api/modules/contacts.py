from ._base import SarvModule
from ._mixins import UrlMixin

class Contacts(SarvModule, UrlMixin):
    _module_name = 'Contacts'
    _table_name = 'contacts'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Contacts'
    _label_pr = 'افراد'