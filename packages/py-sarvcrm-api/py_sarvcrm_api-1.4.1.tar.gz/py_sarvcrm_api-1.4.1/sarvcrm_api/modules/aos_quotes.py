from ._base import SarvModule
from ._mixins import UrlMixin

class Quotes(SarvModule, UrlMixin):
    _module_name = 'AOS_Quotes'
    _table_name = 'aos_quotes'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Quotes'
    _label_pr = 'پیش فاکتورها'