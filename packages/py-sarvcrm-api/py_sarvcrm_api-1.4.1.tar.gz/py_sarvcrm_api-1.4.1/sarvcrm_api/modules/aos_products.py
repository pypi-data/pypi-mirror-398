from ._base import SarvModule
from ._mixins import UrlMixin

class Products(SarvModule, UrlMixin):
    _module_name = 'AOS_Products'
    _table_name = 'aos_products'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Products'
    _label_pr = 'محصولات'