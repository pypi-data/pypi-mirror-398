from ._base import SarvModule
from ._mixins import UrlMixin

class Campaigns(SarvModule, UrlMixin):
    _module_name = 'Campaigns'
    _table_name = 'campaigns'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Campaigns'
    _label_pr = 'کمپین ها'