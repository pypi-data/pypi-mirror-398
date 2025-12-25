from ._base import SarvModule
from ._mixins import UrlMixin

class Cases(SarvModule, UrlMixin):
    _module_name = 'Cases'
    _table_name = 'cases'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Cases'
    _label_pr = 'سرویس ها'