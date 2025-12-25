from .base import Base

class Reports(Base):

    def bulk_mark_as_paid(self, data):

        payload = {
            'data': data
        }

        return self.connection.bulk_mark_as_paid(payload)
