from ._base import SarvModule
from ._mixins import UrlMixin

class Leads(SarvModule, UrlMixin):
    _module_name = 'Leads'
    _table_name = 'leads'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Leads'
    _label_pr = 'سرنخ'