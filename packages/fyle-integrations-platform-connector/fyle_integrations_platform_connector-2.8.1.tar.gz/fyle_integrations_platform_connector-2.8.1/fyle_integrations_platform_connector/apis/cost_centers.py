import logging
from datetime import datetime, timezone
from .base import Base

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class CostCenters(Base):
    """Class for Cost Centers APIs."""

    def __init__(self):
        Base.__init__(self, attribute_type='COST_CENTER', query_params={'is_enabled': 'eq.true'})

    def sync(self, sync_after: datetime = None):
        """
        Syncs the latest API data to DB.
        :param sync_after: Sync after timestamp for incremental sync
        """
        try:
            generator = self.get_all_generator(sync_after)

            for items in generator:
                cost_center_attributes = []

                for cost_center in items['data']:
                    if self.attribute_is_valid(cost_center):
                        cost_center_attributes.append({
                            'attribute_type': self.attribute_type,
                            'display_name': self.attribute_type.replace('_', ' ').title(),
                            'value': cost_center['name'],
                            'active': cost_center['is_enabled'],
                            'source_id': cost_center['id']
                        })

                self.bulk_create_or_update_expense_attributes(cost_center_attributes, True)

        except Exception as e:
            logger.exception(e)
