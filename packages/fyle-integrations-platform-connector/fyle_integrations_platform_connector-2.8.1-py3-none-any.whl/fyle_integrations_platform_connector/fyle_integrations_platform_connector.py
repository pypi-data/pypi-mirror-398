import logging
import os
from datetime import datetime

from fyle.platform import Platform
from fyle.platform.exceptions import InvalidTokenError

from apps.workspaces.models import FyleCredential, FeatureConfig
from fyle_accounting_mappings.models import FyleSyncTimestamp
from .apis import Expenses, Employees, Categories, Projects, CostCenters, ExpenseCustomFields, CorporateCards, \
    Reimbursements, TaxGroups, Merchants, Files, DependentFields, Departments, Subscriptions, Reports, CorporateCardTransactions, OrgSettings

logger = logging.getLogger(__name__)
logger.level = logging.INFO


RESOURCE_NAME_MAP = {
    'employees': 'employee',
    'categories': 'category',
    'projects': 'project',
    'cost_centers': 'cost_center',
    'expense_custom_fields': 'expense_field',
    'corporate_cards': 'corporate_card',
    'dependent_fields': 'dependent_field',
    'tax_groups': 'tax_group',
}


def get_resource_timestamp(fyle_sync_timestamp: FyleSyncTimestamp, resource_name: str) -> datetime:
    """
    Get timestamp for a particular resource from FyleSyncTimestamp
    :param fyle_sync_timestamp: FyleSyncTimestamp object
    :param resource_name: Resource name (e.g., 'employees', 'categories', etc.)
    :return: timestamp or None
    """
    return getattr(fyle_sync_timestamp, f'{resource_name}_synced_at', None)


class PlatformConnector:
    """The main class creates a connection with Fyle Platform APIs using OAuth2 authentication
    (refresh token grant type).

    Parameters:
    fyle_credential (str): Fyle Credential instance.
    """

    def __init__(self, fyle_credentials: FyleCredential):
        server_url = '{}/platform/v1'.format(fyle_credentials.cluster_domain)
        self.workspace_id = fyle_credentials.workspace_id
        try:
            self.connection = Platform(
                server_url=server_url,
                token_url=os.environ.get('FYLE_TOKEN_URI'),
                client_id=os.environ.get('FYLE_CLIENT_ID'),
                client_secret=os.environ.get('FYLE_CLIENT_SECRET'),
                refresh_token=fyle_credentials.refresh_token
            )
            
        except Exception as e:
            logger.error('Invalid Refresh token for workspace_id %s with exception %s', self.workspace_id, str(e))
            raise InvalidTokenError('Invalid refresh token')

        self.expenses = Expenses()
        self.employees = Employees()
        self.categories = Categories()
        self.projects = Projects()
        self.cost_centers = CostCenters()
        self.expense_custom_fields = ExpenseCustomFields()
        self.corporate_cards = CorporateCards()
        self.reimbursements = Reimbursements()
        self.tax_groups = TaxGroups()
        self.merchants = Merchants()
        self.files = Files()
        self.departments = Departments()
        self.dependent_fields = DependentFields()
        self.subscriptions = Subscriptions()
        self.reports = Reports()
        self.corporate_card_transactions = CorporateCardTransactions()
        self.org_settings = OrgSettings()
        self.set_connection()
        self.set_workspace_id()

    def set_connection(self):
        """Set connection with Fyle Platform APIs."""
        self.expenses.set_connection(self.connection.v1.admin.expenses)
        self.employees.set_connection(self.connection.v1.admin.employees)
        self.categories.set_connection(self.connection.v1.admin.categories)
        self.projects.set_connection(self.connection.v1.admin.projects)
        self.cost_centers.set_connection(self.connection.v1.admin.cost_centers)
        self.expense_custom_fields.set_connection(self.connection.v1.admin.expense_fields)
        self.corporate_cards.set_connection(self.connection.v1.admin.corporate_cards)
        self.reimbursements.set_connection(self.connection.v1.admin.reimbursements)
        self.tax_groups.set_connection(self.connection.v1.admin.tax_groups)
        self.merchants.set_connection(self.connection.v1.admin.expense_fields)
        self.files.set_connection(self.connection.v1.admin.files)
        self.departments.set_connection(self.connection.v1.admin.departments)
        self.dependent_fields.set_connection(
            self.connection.v1.admin.dependent_expense_field_values,
            self.connection.v1.admin.expense_fields
        )
        self.subscriptions.set_connection(self.connection.v1.admin.subscriptions)
        self.reports.set_connection(self.connection.v1.admin.reports)
        self.corporate_card_transactions.set_connection(self.connection.v1.admin.corporate_card_transactions)
        self.expenses.corporate_card_transactions = self.corporate_card_transactions
        self.org_settings.set_connection(self.connection.v1.admin.org_settings)

    def set_workspace_id(self):
        """Set workspace ID for Fyle Platform APIs."""
        self.expenses.set_workspace_id(self.workspace_id)
        self.employees.set_workspace_id(self.workspace_id)
        self.categories.set_workspace_id(self.workspace_id)
        self.projects.set_workspace_id(self.workspace_id)
        self.cost_centers.set_workspace_id(self.workspace_id)
        self.expense_custom_fields.set_workspace_id(self.workspace_id)
        self.corporate_cards.set_workspace_id(self.workspace_id)
        self.reimbursements.set_workspace_id(self.workspace_id)
        self.tax_groups.set_workspace_id(self.workspace_id)
        self.merchants.set_workspace_id(self.workspace_id)
        self.files.set_workspace_id(self.workspace_id)
        self.departments.set_workspace_id(self.workspace_id)
        self.dependent_fields.set_workspace_id(self.workspace_id)
        self.reports.set_workspace_id(self.workspace_id)
        self.corporate_card_transactions.set_workspace_id(self.workspace_id)
        self.org_settings.set_workspace_id(self.workspace_id)

    def import_fyle_dimensions(self, import_taxes: bool = False, import_dependent_fields: bool = False, is_export: bool = False, skip_dependent_field_ids: list = []):
        """Import Fyle Platform dimension."""
        apis = ['employees', 'categories', 'projects', 'cost_centers', 'expense_custom_fields', 'corporate_cards']
        fyle_sync_timestamp = None

        if is_export:
            apis = ['employees', 'cost_centers', 'expense_custom_fields', 'corporate_cards']

        if import_dependent_fields:
            apis.append('dependent_fields')

        if import_taxes:
            apis.append('tax_groups')

        fyle_webhook_sync_enabled = FeatureConfig.get_feature_config(workspace_id=self.workspace_id, key='fyle_webhook_sync_enabled')
        if fyle_webhook_sync_enabled:
            fyle_sync_timestamp = FyleSyncTimestamp.objects.get(workspace_id=self.workspace_id)

        for api in apis:
            dimension = getattr(self, api)
            try:
                if api == 'dependent_fields':
                    dimension.sync(skip_dependent_field_ids)
                else:
                    sync_after = None
                    resource_name = RESOURCE_NAME_MAP.get(api, api)
                    if fyle_webhook_sync_enabled and fyle_sync_timestamp:
                        sync_after = get_resource_timestamp(fyle_sync_timestamp, resource_name)
                        logger.debug(f'Syncing {api} for workspace_id {self.workspace_id} with webhook mode | sync_after: {sync_after}')
                    else:
                        logger.debug(f'Syncing {api} for workspace_id {self.workspace_id} with full sync mode')
                    dimension.sync(sync_after=sync_after)

                    if fyle_webhook_sync_enabled and fyle_sync_timestamp:
                        fyle_sync_timestamp.update_sync_timestamp(self.workspace_id, resource_name)
            except Exception as e:
                logger.exception(f'Error syncing {api} for workspace_id {self.workspace_id}: {e}')
