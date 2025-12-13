from src.data_processing.database_manager import DatabaseManager
from src.data_processing.data_processor import DataProcessor

def get_db_manager():
    """Dependency to get DatabaseManager instance"""
    return DatabaseManager()

def get_data_processor():
    """Dependency to get DataProcessor instance"""
    return DataProcessor()
