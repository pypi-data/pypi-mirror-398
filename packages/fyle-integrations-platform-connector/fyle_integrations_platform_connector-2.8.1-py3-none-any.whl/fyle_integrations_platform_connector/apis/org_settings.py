from .base import Base


class OrgSettings(Base):
    """
    Class for Org Settings API
    """
    def get(self) -> dict:
        """
        Get org settings
        """
        return self.connection.list(query_params={'order': 'updated_at.desc', 'limit': 1, 'offset': 0})['data']
