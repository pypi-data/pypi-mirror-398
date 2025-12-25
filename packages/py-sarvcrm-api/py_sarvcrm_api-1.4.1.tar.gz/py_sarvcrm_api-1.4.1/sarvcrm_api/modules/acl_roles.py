from ._base import SarvModule
from ._mixins import UrlMixin

class ACLRoles(SarvModule, UrlMixin):
    _module_name = 'ACLRoles'
    _table_name = 'acl_roles'
    _assigned_field = ''
    _label_en = 'ACL Roles'
    _label_pr = 'نقش ها'