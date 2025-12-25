from datetime import datetime, timezone
import logging

from .base import Base
from typing import List

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class Merchants(Base):
    """
    Class for Merchants API
    """
    def __init__(self):
        Base.__init__(self, attribute_type='MERCHANT', query_params={'column_name':'eq.merchant'})

    def get(self):
        generator = self.get_all_generator()
        for items in generator:
            merchants = items['data'][0]

        return merchants

    def post(self, payload: List[str], skip_existing_merchants: bool = False, delete_merchants: bool = False):
        """
        Post data to Fyle
        """
        logger.info("Merchant Payload received from Integration for Workspace: %s with payload %s", self.workspace_id, payload)
        logger.info("Merchant Payload received from Integration for Workspace: %s with count: %s", self.workspace_id, len(payload))
        generator = self.get_all_generator()
        for items in generator:
            merchants = items['data'][0]
            logger.info("Fyle Merchant Count: %s in Workspace: %s", len(merchants['options']), self.workspace_id)
            if delete_merchants:
                merchants['options'] = list(set(merchants['options']) - set(payload))
            else:
                if skip_existing_merchants:
                    merchants['options'] = payload
                else:
                    merchants['options'].extend(payload)
                merchants['options'] = list(set(merchants['options']))

            logger.info("Posting Merchant Payload for Workspace: %s with count: %s", self.workspace_id, len(merchants['options']))

            merchant_payload = {
                'id': merchants['id'],
                'field_name': merchants['field_name'],
                'type': 'SELECT',
                'options': merchants['options'],
                'placeholder': merchants['placeholder'],
                'category_ids': merchants['category_ids'],
                'is_enabled': merchants['is_enabled'],
                'is_custom': merchants['is_custom'],
                'is_mandatory': merchants['is_mandatory'],
                'code': merchants['code'],
                'default_value': merchants['default_value'] if merchants['default_value'] else '',
            }

            if len(merchant_payload['options']) == 0:
                logger.error("Merchant Payload is empty for Workspace: %s", self.workspace_id)
                return

        return self.connection.post({'data': merchant_payload})

    def sync(self):
        """
        Syncs the latest API data to DB.
        """
        try:
            generator = self.get_all_generator()
            for items in generator:
                merchants = items['data'][0]

                logger.info("Fyle Merchant Count: %s in Workspace: %s", len(merchants['options']), self.workspace_id)

                merchant_attributes = []

                for option in merchants['options']:
                    merchant_attributes.append({
                        'attribute_type': 'MERCHANT',
                        'display_name': 'Merchant',
                        'value': option,
                        'active': True,
                        'source_id': merchants['id'],
                    })

                self.bulk_create_or_update_expense_attributes(merchant_attributes, True)

        except Exception as e:
            logger.exception(e)

    def get_count(self):
        """
        Get the count of merchants
        """
        generator = self.get_all_generator()
        for items in generator:
            return len(items['data'][0]['options'])

        return 0
