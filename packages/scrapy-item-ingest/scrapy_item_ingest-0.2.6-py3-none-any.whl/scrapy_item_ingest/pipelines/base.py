"""
Base pipeline functionality for scrapy_item_ingest.
"""
import logging

from ..config.settings import Settings, validate_settings
from ..database.connection import DatabaseConnection
from ..database.schema import SchemaManager

logger = logging.getLogger(__name__)


class BasePipeline:
    """Base pipeline with common functionality"""

    def __init__(self, settings):
        self.settings = settings
        self.db = None
        self.schema_manager = None
        validate_settings(settings)

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline instance from crawler"""
        settings = Settings(crawler.settings)
        return cls(settings)

    def open_spider(self, spider):
        """Called when spider is opened"""
        # Get singleton database connection (reuses existing connection if already created)
        self.db = DatabaseConnection(self.settings.db_url)

        # Only initialize connection if not already connected
        if not self.db.connect():
            raise Exception("Failed to connect to database")

        # Initialize schema manager (only once)
        if not hasattr(self, 'schema_manager') or self.schema_manager is None:
            self.schema_manager = SchemaManager(self.db, self.settings)
            # Ensure tables exist
            self.schema_manager.ensure_tables_exist()

    def close_spider(self, spider):
        """Called when spider is closed"""
        # Don't close the connection here as it might be used by other spiders
        # The connection will be closed when the process ends
        pass

    def get_identifier_info(self, spider):
        """Get identifier column and value for the spider"""
        return self.settings.get_identifier_column(), self.settings.get_identifier_value(spider)
