from .base import Base
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
logger.level = logging.INFO

class Projects(Base):
    """Class for Projects APIs."""

    def __init__(self):
        Base.__init__(self, attribute_type='PROJECT')


    def sync(self, sync_after: datetime = None):
        """
        Syncs the latest API data to DB.
        :param sync_after: Sync after timestamp for incremental sync
        """
        try:
            generator = self.get_all_generator(sync_after)

            for items in generator:
                project_attributes = []

                for project in items['data']:
                    if self.attribute_is_valid(project):
                        if project['sub_project']:
                            project['name'] = '{0} / {1}'.format(project['name'], project['sub_project'])

                        project_attributes.append({
                            'attribute_type': self.attribute_type,
                            'display_name': self.attribute_type.replace('_', ' ').title(),
                            'value': project['name'],
                            'active': project['is_enabled'],
                            'source_id': project['id']
                        })

                self.bulk_create_or_update_expense_attributes(project_attributes, True)

        except Exception as exception:
            logger.exception(exception)
