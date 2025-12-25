from ._base import SarvModule
from ._mixins import UrlMixin

class Indicators(SarvModule, UrlMixin):
    _module_name = 'OBJ_Indicators'
    _table_name = 'obj_indicators'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Indicators'
    _label_pr = 'شاخص'