import os
import yaml
import psycopg2
from typing import Optional, Dict, Any, List
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import DictCursor

class UniversalPostgresqlHook:
    """
    A universal PostgreSQL hook that can work in Airflow as well as standalone.
    
    When used with Airflow, connection details are fetched from Airflow Connections.
    When used standalone, these details should be loaded from a YAML file named after the connection ID.
    
    Args:
        postgres_conn_id (str, optional): The connection ID, used as Airflow connection ID or as the name for the YAML file. Defaults to None.
        config_folder (str, optional): The folder where the YAML configuration file is located. Defaults to None.
        
    Attributes:
        hook (PostgresHook, optional): The Airflow PostgresHook instance.
        conn (psycopg2.extensions.connection, optional): The psycopg2 connection instance.
        config (dict, optional): The configuration loaded from the YAML file.
    """
    
    def __init__(self, postgres_conn_id: Optional[str] = None, config_folder: Optional[str] = None):
        self.postgres_conn_id = postgres_conn_id
        self.config_folder = '' if config_folder is None else config_folder
        if self.config_folder:
            if self.postgres_conn_id is None:
                raise ValueError("postgres_conn_id must be provided when running in standalone mode")
            config_path = os.path.join(self.config_folder, f"{self.postgres_conn_id}.yaml")
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            self.conn = psycopg2.connect(
                dbname=self.config['dbname'],
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port']
            )
        else:
            self.hook = PostgresHook(postgres_conn_id=self.postgres_conn_id)
            self.conn = None

    def get_conn(self) -> Any:
        """
        Establishes a connection to the PostgreSQL database.
        
        Returns:
            A connection object that can be used to interact with the database.
        """
        if self.conn:
            return self.conn
        else:
            return self.hook.get_conn()

    def get_first(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes the SQL query and returns the first result.
        
        Args:
            sql (str): The SQL query to execute.
            params (dict, optional): The parameters to substitute into the SQL query.
        
        Returns:
            The first result from the executed SQL query as a dictionary where keys are column names and values are column values.
        """
        if self.conn:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql, params)
                result = cur.fetchone()
            return dict(result) if result else None
        else:
            return self.hook.get_first(sql, parameters=params)

    def get_all(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes the SQL query and returns all results.
        
        Args:
            sql (str): The SQL query to execute.
            params (dict, optional): The parameters to substitute into the SQL query.
        
        Returns:
            All results from the executed SQL query as a list of dictionaries where keys are column names and values are column values.
        """
        if self.conn:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql, params)
                result = cur.fetchall()
            return [dict(row) for row in result] if result else []
        else:
            return self.hook.get_records(sql, parameters=params)
