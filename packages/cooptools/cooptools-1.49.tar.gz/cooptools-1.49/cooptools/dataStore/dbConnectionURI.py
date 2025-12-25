from cooptools.coopEnum import CoopEnum
from dataclasses import dataclass
from cooptools. cnxn_info import Creds
import urllib.parse

class DataBaseType(CoopEnum):
    MYSQL = 'mssql'
    SQLSERVER = 'mssql'
    MONGODB = 'mongodb'

class DataBaseConnector(CoopEnum):
    PYODBC = 'pyodbc'
    SRV = 'srv'

@dataclass(frozen=True, slots=True, kw_only=True)
class DbConnectionArgs:
    db_type: DataBaseType
    db_connector: DataBaseConnector
    server_name: str
    creds: Creds
    port: int = None

    def server_txt(self):
        return f"{self.server_name}:{self.port}" if self.port else f"{self.server_name}"

    def cnxn_txt(self):
        return f"{self.db_type.value}+{self.db_connector.value}"
@dataclass(frozen=True, slots=True, kw_only=True)
class SqlDBConnectionArgs(DbConnectionArgs):
    trusted_connection: bool = True
    driver: str = "ODBC+Driver+17+for+SQL+Server"
    db_name: str

    def creds_string(self):
        trusted_txt = ""
        up_txt = ""

        if not self.trusted_connection:
            if self.user is None or self.pw is None:
                raise ValueError("User and password cannot be None when it is not a trusted connection")
            u = urllib.parse.quote(self.creds.user)
            p = urllib.parse.quote(self.creds.pw)
            up_txt = f"&User ID={u}&Password={p}"
        else:
            trusted_txt = 'trusted_connection=' + ('yes' if self.trusted_connection else 'no')

        return f"{trusted_txt}{up_txt}"

    def connection_string(self):

        driver = self.driver.replace(" ", "+")
        args = [
            self.creds_string(),
            f"driver={driver}"
        ]

        args_txt = '&'.join(args)
        conn_str = f'{self.cnxn_txt()}://@{self.server_txt()}/{self.db_name}?{args_txt}'
        return conn_str
@dataclass(frozen=True, slots=True, kw_only=True)
class MongoDBConnectionArgs(DbConnectionArgs):
    retry_writes: bool = True
    uuidRepresentation: str = 'standard'
    w: str = 'majority'

    def connection_string(self):
        args = [
            'retryWrites=' + ('true' if self.retry_writes else 'false'),
            f'w={self.w}',
            f'uuidRepresentation={self.uuidRepresentation}'
        ]

        args_txt = '&'.join(args)
        u = urllib.parse.quote(self.creds.user)
        p = urllib.parse.quote(self.creds.pw)
        return f"{self.cnxn_txt()}://{u}:{p}@{self.server_txt()}/?{args_txt}"

