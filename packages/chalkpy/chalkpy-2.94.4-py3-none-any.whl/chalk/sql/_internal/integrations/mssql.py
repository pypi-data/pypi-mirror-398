from __future__ import annotations

import os
import struct
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Union

from chalk.integrations.named import create_integration_variable, load_integration_variable
from chalk.sql._internal.sql_source import BaseSQLSource, SQLSourceKind, TableIngestMixIn
from chalk.sql.protocols import SQLSourceWithTableIngestProtocol
from chalk.utils.missing_dependency import missing_dependency_exception

if TYPE_CHECKING:
    from sqlalchemy.engine import URL

_MSSQL_HOST_NAME = "MSSQL_HOST"
_MSSQL_TCP_PORT_NAME = "MSSQL_TCP_PORT"
_MSSQL_DATABASE_NAME = "MSSQL_DATABASE"
_MSSQL_USER_NAME = "MSSQL_USER"
_MSSQL_PWD_NAME = "MSSQL_PWD"
_MSSQL_CLIENT_ID_NAME = "MSSQL_CLIENT_ID"
_MSSQL_CLIENT_SECRET_NAME = "MSSQL_CLIENT_SECRET"
_MSSQL_TENANT_ID_NAME = "MSSQL_TENANT_ID"


class MSSQLSourceImpl(BaseSQLSource, TableIngestMixIn, SQLSourceWithTableIngestProtocol):
    kind = SQLSourceKind.mssql

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[Union[int, str]] = None,
        db: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        name: Optional[str] = None,
        engine_args: Optional[Dict[str, Any]] = None,
        async_engine_args: Optional[Dict[str, Any]] = None,
        integration_variable_override: Optional[Mapping[str, str]] = None,
    ):
        try:
            import pyodbc
        except ImportError:
            raise missing_dependency_exception("chalkpy[mssql]")
        del pyodbc

        self.name = name
        self.host = host or load_integration_variable(
            integration_name=name, name=_MSSQL_HOST_NAME, override=integration_variable_override
        )
        self.port = (
            int(port)
            if port is not None
            else load_integration_variable(
                integration_name=name, name=_MSSQL_TCP_PORT_NAME, parser=int, override=integration_variable_override
            )
        )
        self.db = db or load_integration_variable(
            integration_name=name, name=_MSSQL_DATABASE_NAME, override=integration_variable_override
        )
        self.user = user or load_integration_variable(
            integration_name=name,
            name=_MSSQL_USER_NAME,
            override=integration_variable_override,
        )
        self.password = password or load_integration_variable(
            integration_name=name,
            name=_MSSQL_PWD_NAME,
            override=integration_variable_override,
        )
        self.client_id = client_id or load_integration_variable(
            integration_name=name,
            name=_MSSQL_CLIENT_ID_NAME,
            override=integration_variable_override,
        )
        self.client_secret = client_secret or load_integration_variable(
            integration_name=name,
            name=_MSSQL_CLIENT_SECRET_NAME,
            override=integration_variable_override,
        )
        self.tenant_id = tenant_id or load_integration_variable(
            integration_name=name,
            name=_MSSQL_TENANT_ID_NAME,
            override=integration_variable_override,
        )
        self.ingested_tables: Dict[str, Any] = {}

        if engine_args is None:
            engine_args = {}
        if async_engine_args is None:
            async_engine_args = {}

        if name:
            engine_args_from_ui = self._load_env_engine_args(name, override=integration_variable_override)
            for k, v in engine_args_from_ui.items():
                engine_args.setdefault(k, v)
                async_engine_args.setdefault(k, v)

        chalk_default_engine_args = {
            "pool_size": 20,
            "max_overflow": 60,
            "pool_recycle": 90,
        }
        for k, v in chalk_default_engine_args.items():
            engine_args.setdefault(k, v)
            async_engine_args.setdefault(k, v)

        # Set isolation level for read-only operations
        engine_args.setdefault("isolation_level", os.environ.get("CHALK_SQL_ISOLATION_LEVEL", "AUTOCOMMIT"))
        async_engine_args.setdefault("isolation_level", os.environ.get("CHALK_SQL_ISOLATION_LEVEL", "AUTOCOMMIT"))

        BaseSQLSource.__init__(self, name=name, engine_args=engine_args, async_engine_args=async_engine_args)

        # Register event listener for managed identity token injection
        if not self.client_id and not self.user:
            from sqlalchemy import event

            event.listens_for(self.get_engine(), "do_connect")(self._inject_azure_token)

    def _inject_azure_token(self, _dialect: Any, _conn_rec: Any, _cargs: Any, cparams: Dict[str, Any]) -> None:
        """SQLAlchemy event handler to inject Azure AD token on each connection."""
        try:
            from azure.identity import DefaultAzureCredential
        except ImportError:
            raise missing_dependency_exception("chalkpy[mssql]")

        try:
            credential = DefaultAzureCredential()
            token = credential.get_token("https://database.windows.net/.default")
        except Exception as e:
            raise Exception(f"Failed to acquire Azure AD token for MSSQL connection: {e}") from e

        token_bytes = token.token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        cparams["attrs_before"] = {1256: token_struct}  # SQL_COPT_SS_ACCESS_TOKEN

    def get_sqlglot_dialect(self) -> str | None:
        return "tsql"

    def local_engine_url(self) -> "URL":
        from sqlalchemy.engine.url import URL

        if self.client_id and self.client_secret and self.tenant_id:
            # Service Principal authentication
            # Use pyodbc driver for Azure AD support
            return URL.create(
                drivername="mssql+pyodbc",
                username=self.client_id,
                password=self.client_secret,
                host=self.host,
                port=self.port,
                database=self.db,
                query={
                    "driver": "ODBC Driver 18 for SQL Server",
                    "Authentication": "ActiveDirectoryServicePrincipal",
                },
            )
        elif self.user and self.password:
            # SQL authentication
            return URL.create(
                drivername="mssql+pyodbc",
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.db,
                query={"driver": "ODBC Driver 18 for SQL Server"},
            )
        else:
            # Managed Identity: token injected via event listener
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={self.host},{self.port};DATABASE={self.db}"
            )
            return URL.create(
                drivername="mssql+pyodbc",
                query={"odbc_connect": connection_string},
            )

    def _recreate_integration_variables(self) -> dict[str, str]:
        return {
            k: v
            for k, v in [
                create_integration_variable(_MSSQL_HOST_NAME, self.name, self.host),
                create_integration_variable(_MSSQL_TCP_PORT_NAME, self.name, self.port),
                create_integration_variable(_MSSQL_DATABASE_NAME, self.name, self.db),
                create_integration_variable(_MSSQL_USER_NAME, self.name, self.user),
                create_integration_variable(_MSSQL_PWD_NAME, self.name, self.password),
                create_integration_variable(_MSSQL_CLIENT_ID_NAME, self.name, self.client_id),
                create_integration_variable(_MSSQL_CLIENT_SECRET_NAME, self.name, self.client_secret),
                create_integration_variable(_MSSQL_TENANT_ID_NAME, self.name, self.tenant_id),
            ]
            if v is not None
        }
