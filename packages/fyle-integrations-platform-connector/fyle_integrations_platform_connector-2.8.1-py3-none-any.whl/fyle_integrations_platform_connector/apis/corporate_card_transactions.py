from .base import Base


class CorporateCardTransactions(Base):
    """Class for Corporate Card Transactions APIs."""

    def get_transaction_by_id(self, transaction_id: int):
        """
        Get a transaction by ID
        """
        return self.connection.list({
            'id': 'eq.{}'.format(transaction_id),
            'offset': 0,
            'limit': 1,
            'order': 'updated_at.desc'
        })['data']

        
