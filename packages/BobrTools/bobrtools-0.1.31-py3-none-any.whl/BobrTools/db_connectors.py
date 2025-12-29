import socks
import socket
import logging
import pandas as pd
import snowflake.connector
from sqlalchemy import create_engine
from snowflake.connector.pandas_tools import write_pandas
from .helpers import get_env_variable

logger = logging.getLogger(__name__)


class ProxyManager:
    def __init__(self, proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None):
        self.default_socket = socket.socket
        self.proxy_host = proxy_host or get_env_variable("PROXY_HOST")
        self.proxy_port = proxy_port or int(get_env_variable("PROXY_PORT"))
        self.proxy_username = proxy_username or get_env_variable("PROXY_USERNAME")
        self.proxy_password = proxy_password or get_env_variable("PROXY_PASSWORD")

    def init_proxy(self):
        """
        Configures a SOCKS5 proxy for Snowflake connections.
        """
        socks.set_default_proxy(
            socks.SOCKS5,
            addr=self.proxy_host,
            port=self.proxy_port,
            username=self.proxy_username,
            password=self.proxy_password,
        )
        socket.socket = socks.socksocket

    def reset_proxy(self):
        """
        Resets the proxy settings to default.
        """
        socket.socket = self.default_socket


class SnowflakeConnector:
    def __init__(
            self, user=None, password=None, account=None, default_warehouse=None, default_database=None,
            default_schema=None, default_role=None,
            use_proxy=True, proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None
    ):
        self.user = user or get_env_variable("SNOWFLAKE_USER")
        self.password = password or get_env_variable("SNOWFLAKE_PASSWORD")
        self.account = account or get_env_variable("SNOWFLAKE_ACCOUNT")
        self.default_role = default_role or get_env_variable("SNOWFLAKE_ROLE")
        self.default_warehouse = default_warehouse or get_env_variable("SNOWFLAKE_WAREHOUSE")
        self.default_database = default_database or get_env_variable("SNOWFLAKE_DATABASE")
        self.default_schema = default_schema or get_env_variable("SNOWFLAKE_SCHEMA")
        self.use_proxy = use_proxy

        if self.use_proxy:
            self.proxy = ProxyManager(proxy_host, proxy_port, proxy_username, proxy_password)

    def connect(self, role=None, warehouse=None, database=None, schema=None):
        """
        Establishes and returns a connection to Snowflake, with optional overrides
        for warehouse, database, and schema.
        :param role: Name of the Snowflake role to override.
        :param warehouse: Name of the Snowflake warehouse to override.
        :param database: Name of the Snowflake database to override.
        :param schema: Name of the Snowflake schema to override.
        :return: Snowflake connection object.
        """
        return snowflake.connector.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            role=role or self.default_role,
            warehouse=warehouse or self.default_warehouse,
            database=database or self.default_database,
            schema=schema or self.default_schema
        )

    def upload_dataframe(
            self, dataframe, table_name, overwrite=True, auto_create_table=True, warehouse=None, database=None,
            schema=None
    ):
        """
        Uploads a Pandas DataFrame to a Snowflake table, with optional overrides
        for warehouse, database, and schema.
        Temporarily enables proxy if configured.
        :param dataframe: pandas DataFrame to upload.
        :param table_name: Name of the target table in Snowflake.
        :param overwrite: When true, and if auto_create_table is true, then it drops the table. Otherwise, it
        :param auto_create_table: When true, will automatically create a table with corresponding columns for each
            column in the passed in DataFrame. The table will not be created if it already exist
        :param warehouse: Name of the Snowflake warehouse to override.
        :param database: Name of the Snowflake database to override.
        :param schema: Name of the Snowflake schema to override.
        :return: None.
        :raises Exception: If the upload fails.
        """
        try:
            if self.use_proxy:
                self.proxy.init_proxy()

            connection = self.connect(warehouse=warehouse, database=database, schema=schema)
            try:
                success, nchunks, nrows, _ = write_pandas(
                    connection,
                    dataframe,
                    table_name,
                    overwrite=overwrite,
                    auto_create_table=auto_create_table,
                    use_logical_type=True
                )
                if success:
                    logger.info(
                        f"DataFrame successfully uploaded to table '{table_name}' in database '{database or self.default_database}' "
                        f"and schema '{schema or self.default_schema}'. Rows inserted: {nrows}")
                else:
                    raise Exception("Failed to upload DataFrame to Snowflake.")
            finally:
                connection.close()
        finally:
            if self.use_proxy:
                self.proxy.reset_proxy()

    def get_dataframe(self, query, warehouse=None, database=None, schema=None):
        try:
            if self.use_proxy:
                self.proxy.init_proxy()

            conn = self.connect(warehouse=warehouse, database=database, schema=schema)
            cursor = conn.cursor()

            queries = list(filter(lambda item: item.strip(), query.split(";")))
            for single_query in queries:
                cursor.execute(single_query)

            dataframe = pd.DataFrame(cursor.fetchall(), columns=[column[0] for column in cursor.description])
            cursor.close()
            conn.close()

            return dataframe

        finally:
            if self.use_proxy:
                self.proxy.reset_proxy()


class MysqlConnector:
    def __init__(
            self, host=None, port=None, user=None, password=None, database=None,
            use_proxy=True, proxy_host=None, proxy_port=None, proxy_username=None, proxy_password=None
    ):
        self.host = host or get_env_variable("MYSQL_HOST")
        self.port = port or get_env_variable("MYSQL_PORT")
        self.user = user or get_env_variable("MYSQL_USER")
        self.password = password or get_env_variable("MYSQL_PASSWORD")
        self.database = database or get_env_variable("MYSQL_DATABASE")
        self.use_proxy = use_proxy

        if self.use_proxy:
            self.proxy = ProxyManager(proxy_host, proxy_port, proxy_username, proxy_password)

    def connect(self):
        return create_engine(
                "mysql+pymysql://{user}:{password}@{host}:{port}/{database}".format(
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    database=self.database
                )
            )

    def get_dataframe(self, query):
        try:
            if self.use_proxy:
                self.proxy.init_proxy()

            connection = self.connect()
            dataframe = pd.read_sql(query, connection)
            return dataframe

        finally:
            if self.use_proxy:
                self.proxy.reset_proxy()
