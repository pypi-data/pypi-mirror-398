from ._base import SarvModule
from ._mixins import UrlMixin

class Conditions(SarvModule, UrlMixin):
    _module_name = 'OBJ_Conditions'
    _table_name = 'obj_conditions'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Conditions'
    _label_pr = 'شرایط شاخص'