from ._base import SarvModule
from ._mixins import UrlMixin

class Notifications(SarvModule, UrlMixin):
    _module_name = 'Notifications'
    _table_name = 'notifications'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Notifications'
    _label_pr = 'نوتیفیکیشن'