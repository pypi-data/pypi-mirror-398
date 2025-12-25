from ._base import SarvModule
from ._mixins import UrlMixin

class Opportunities(SarvModule, UrlMixin):
    _module_name = 'Opportunities'
    _table_name = 'opportunities'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Opportunities'
    _label_pr = 'فرصت ها'