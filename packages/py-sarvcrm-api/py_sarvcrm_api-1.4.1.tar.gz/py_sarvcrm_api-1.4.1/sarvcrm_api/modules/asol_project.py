from ._base import SarvModule
from ._mixins import UrlMixin

class Projects(SarvModule, UrlMixin):
    _module_name = 'asol_Project'
    _table_name = 'asol_project'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Project'
    _label_pr = 'پروژه'