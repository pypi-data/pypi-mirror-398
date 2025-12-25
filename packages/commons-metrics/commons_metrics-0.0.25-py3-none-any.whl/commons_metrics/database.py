import psycopg2
from .repositories import ComponentRepository
from .util import Util

class DatabaseConnection:
    """
    Class to handle PostgreSQL database connections
    using AWS Secrets Manager credentials
    """
    
    def __init__(self):
        self.connection = None

    def connect(self, credentials):
        """Establishes database connection using credentials"""
        try:
            self.connection = psycopg2.connect(
                host=credentials['host'],
                port=credentials['port'],
                database=credentials['dbname'],
                user=credentials['username'],
                password=credentials['password'],
                connect_timeout=30
            )
        except Exception as e:
            raise Exception(f"Database connection error: {str(e)}")

    def close(self):
        """Closes the database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def commit_transaction(self):
        """Commits pending transactions"""
        if self.connection and not self.connection.closed:
            self.connection.commit()

    def rollback_transaction(self):
        """Rolls back pending transactions in case of error"""
        if self.connection and not self.connection.closed:
            self.connection.rollback()

    def get_connection_database_from_secret(secret_name: str, logger: str, aws_region: str) -> ComponentRepository:
        """
        Retrieve connection database from AWS secrets manager
        """
        secret_json = Util.get_secret_aws(secret_name, logger, aws_region)
        db_connection = DatabaseConnection()
        db_connection.connect({
            'host': secret_json["host"],
            'port': secret_json["port"],
            'dbname': secret_json["dbname"],
            'username': secret_json["username"],
        'password': secret_json["password"]
        })
        return ComponentRepository(db_connection)