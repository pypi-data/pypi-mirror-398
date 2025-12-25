from ._base import SarvModule
from ._mixins import UrlMixin

class PurchaseOrders(SarvModule, UrlMixin):
    _module_name = 'Purchase_Order'
    _table_name = 'purchase_order'
    _assigned_field = 'assigned_user_id'
    _label_en = 'Purchase Order'
    _label_pr = 'سفارش خرید'