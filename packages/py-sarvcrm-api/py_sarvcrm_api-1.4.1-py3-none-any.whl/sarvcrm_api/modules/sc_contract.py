from ._base import SarvModule
from ._mixins import UrlMixin

class SupportContracts(SarvModule, UrlMixin):
    _module_name = 'sc_Contract'
    _table_name = 'sc_contract'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Support Contracts'
    _label_pr = 'قراردادهای پشتیبانی'