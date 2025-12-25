from ._base import SarvModule
from ._mixins import UrlMixin

class Calls(SarvModule, UrlMixin):
    _module_name = 'Calls'
    _table_name = 'calls'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Calls'
    _label_pr = 'تماس ها'