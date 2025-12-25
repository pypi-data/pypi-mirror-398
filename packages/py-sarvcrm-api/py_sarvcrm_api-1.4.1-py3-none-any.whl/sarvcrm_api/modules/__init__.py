from ._base import SarvModule
from .accounts import Accounts
from .acl_roles import ACLRoles
from .aos_contracts import SalesContracts
from .aos_invoices import Invoices
from .aos_pdf_templates import PDFTemplates
from .aos_product_categories import ProductCategories      
from .aos_products import Products
from .aos_quotes import Quotes
from .approval import Approvals
from .asol_project import Projects
from .branches import Branches
from .bugs import Bugs
from .calls import Calls
from .cases import Cases
from .communications import Communications
from .communications_target import CommunicationTargets      
from .communications_template import CommunicationTemplates   
from .campaigns import Campaigns
from .contacts import Contacts
from .deposits import Deposits
from .documents import Documents
from .emails import Emails
from .knowledge_base import KnowledgeBases
from .knowledge_base_categories import KnowledgeBaseCategories
from .leads import Leads
from .meetings import Meetings
from .notes import Notes
from .notifications import Notifications
from .obj_conditions import Conditions
from .obj_indicators import Indicators
from .obj_objectives import Objectives
from .opportunities import Opportunities
from .payments import Payments
from .purchase_order import PurchaseOrders
from .sc_competitor import Competitor
from .sc_contract import SupportContracts
from .sc_contract_management import Services
from .service_centers import ServiceCenters
from .tasks import Tasks
from .timesheet import Timesheets
from .users import Users
from .vendors import Vendors


__all__ = [
    'SarvModule',
    'Accounts',
    'ACLRoles',
    'SalesContracts',
    'Invoices',
    'PDFTemplates',
    'ProductCategories',
    'Products',
    'Quotes',
    'Approvals',
    'Projects',
    'Branches',
    'Bugs',
    'Calls',
    'Cases',
    'Communications',
    'CommunicationTargets',
    'CommunicationTemplates',
    'Campaigns',
    'Contacts',
    'Deposits',
    'Documents',
    'Emails',
    'KnowledgeBases',
    'KnowledgeBaseCategories',
    'Leads',
    'Meetings',
    'Notes',
    'Notifications',
    'Conditions',
    'Indicators',
    'Objectives',
    'Opportunities',
    'Payments',
    'PurchaseOrders',
    'Competitor',
    'SupportContracts',
    'Services',
    'ServiceCenters',
    'Tasks',
    'Timesheets',
    'Users',
    'Vendors',
]