from ._base import SarvModule
from ._mixins import UrlMixin

class Bugs(SarvModule, UrlMixin):
    _module_name = 'Bugs'
    _table_name = 'bugs'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Bug Tracker'
    _label_pr = 'پیگیری ایرادهای محصول'