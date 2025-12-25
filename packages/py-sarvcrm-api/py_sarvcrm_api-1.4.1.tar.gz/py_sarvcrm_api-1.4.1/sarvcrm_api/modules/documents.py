from ._base import SarvModule
from ._mixins import UrlMixin

class Documents(SarvModule, UrlMixin):
    _module_name = 'Documents'
    _table_name = 'documents'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Documents'
    _label_pr = 'اسناد'