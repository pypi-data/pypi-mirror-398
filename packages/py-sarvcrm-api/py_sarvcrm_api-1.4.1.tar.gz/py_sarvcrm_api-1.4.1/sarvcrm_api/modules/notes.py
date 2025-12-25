from ._base import SarvModule
from ._mixins import UrlMixin

class Notes(SarvModule, UrlMixin):
    _module_name = 'Notes'
    _table_name = 'notes'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Notes'
    _label_pr = 'یادداشت ها'