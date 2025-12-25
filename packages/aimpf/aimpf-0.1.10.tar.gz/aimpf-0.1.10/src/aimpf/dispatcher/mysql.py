"""
MySQL-based database subscriber implementations.

This module provides database subscriber classes that interact with
MySQL-based dispatcher services.
"""
import logging
from datetime import datetime
from requests import HTTPError

from .base import DbSubscriberBase

logger = logging.getLogger(__name__)

__all__ = ["DbSubscriber", "Ctxt", "Db38", "Db41", "Db44"]


class DbSubscriber(DbSubscriberBase):
    """
    Database subscriber for MySQL-based dispatcher services.

    This class provides methods for querying resources through a
    MySQL dispatcher API. Unlike the MQTT variant, this class requires
    explicit database and table parameters for most operations.
    """

    def keywords(
        self,
        *,
        database: str | None = None,
        table: str | None = None,
        columns: str | list[str] | None = None,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> dict[str, list]:
        """
        Check the keywords being provided.

        Parameters
        ----------
        database : str, optional
            Database name.
        table : str, optional
            Table name.
        columns : str or list[str], optional
            Column name or list of column names.
        where : str, optional
            Comma-separated list of conditions.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.
        limit : int, optional
            Maximum number of records to return.

        Returns
        -------
        dict
            Dictionary of keywords.

        Raises
        ------
        requests.HTTPError
            If the request fails.
        """
        params = self._build_query_params(
            columns=columns,
            database=database,
            table=table,
            where=where,
            start=start,
            end=end,
            limit=limit,
        )
        response = self.auth.get(f"keywords{params}")
        response.raise_for_status()
        return response.json()

    def list_databases(self) -> dict:
        """
        List databases available for the resource.

        Returns
        -------
        dict
            Dictionary of databases keyed by database name.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        response = self.auth.get(f"resources/{self._label}/databases/list")
        response.raise_for_status()
        return response.json()

    def list_tables(self, database: str) -> list:
        """
        Retrieve a list of tables in the specified database.

        Parameters
        ----------
        database : str
            The name of the database.

        Returns
        -------
        list
            A list of tables in the specified database.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        response = self.auth.get(
            f"resources/{self._label}/databases/{database}/tables/list"
        )
        response.raise_for_status()
        return response.json()

    def list_columns(self, database: str, table: str) -> list:
        """
        List columns for a resource.database.table.

        Parameters
        ----------
        database : str
            The name of the database.
        table : str
            The name of the table.

        Returns
        -------
        list
            List of columns in the specified table.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        response = self.auth.get(
            f"resources/{self._label}/databases/{database}/tables/{table}/columns"
        )
        response.raise_for_status()
        return response.json()

    def distinct(
        self,
        database: str,
        table: str,
        columns: str | list[str],
        *,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> dict[str, list]:
        """
        Get distinct values for a column.

        Parameters
        ----------
        database : str
            The name of the database.
        table : str
            The name of the table.
        columns : str or list[str]
            Column name or list of column names.
        where : str, optional
            Comma-separated list of conditions. Each must match
            <col><op><value> where <col> is a column name in the table, <op>
            is a comparison operator ("=", "<", ">", "<=", ">="), and <value>
            is present in the database. WARNING: This can be quite slow as
            query sanitation can take a very long time.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.
        limit : int, optional
            Maximum number of distinct values to return.

        Returns
        -------
        dict
            Dictionary of distinct values keyed by column name.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        columns_str = self._normalize_columns(columns)
        params = self._build_query_params(
            where=where,
            start=start,
            end=end,
            limit=limit,
        )
        response = self.auth.get(
            f"resources/{self._label}/databases/{database}/"
            f"tables/{table}/distinct/{columns_str}{params}"
        )
        response.raise_for_status()
        return response.json()

    def count(
        self,
        database: str,
        table: str,
        *,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
    ) -> int:
        """
        Get the count of records.

        Parameters
        ----------
        database : str
            The name of the database.
        table : str
            The name of the table.
        where : str, optional
            Comma-separated list of conditions. Each must match
            <col><op><value> where <col> is a column name in the table, <op>
            is a comparison operator ("=", "<", ">", "<=", ">="), and <value>
            is present in the database. WARNING: This can be quite slow as
            query sanitation can take a very long time.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.

        Returns
        -------
        int
            The count of rows.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        params = self._build_query_params(
            where=where,
            start=start,
            end=end,
        )
        response = self.auth.get(
            f"resources/{self._label}/databases/{database}/"
            f"tables/{table}/count{params}"
        )
        response.raise_for_status()
        try:
            return response.json()[0][0]
        except IndexError:
            raise HTTPError("Invalid resource response.")

    def list(
        self,
        database: str,
        table: str,
        *,
        where: str | None = None,
        start: str | datetime | None = None,
        end: str | datetime | None = None,
        limit: int | None = None,
    ) -> list[str]:
        """
        Get the records.

        Parameters
        ----------
        database : str
            The name of the database.
        table : str
            The name of the table.
        where : str, optional
            Comma-separated list of conditions. Each must match
            <col><op><value> where <col> is a column name in the table, <op>
            is a comparison operator ("=", "<", ">", "<=", ">="), and <value>
            is present in the database. WARNING: This can be quite slow as
            query sanitation can take a very long time.
        start : str or datetime, optional
            Start date or time.
        end : str or datetime, optional
            End date or time.
        limit : int, optional
            Maximum number of records to return.

        Returns
        -------
        list
            List of strings representing the records.

        Raises
        ------
        ValueError
            If the label is not set.
        requests.HTTPError
            If the request fails.
        """
        self._require_label()
        params = self._build_query_params(
            where=where,
            start=start,
            end=end,
            limit=limit,
        )
        response = self.auth.get(
            f"resources/{self._label}/databases/{database}/"
            f"tables/{table}/list{params}"
        )
        response.raise_for_status()
        return response.json()


class Ctxt(DbSubscriber):
    """Subscriber for ctxt database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "ctxt"


class Db38(DbSubscriber):
    """Subscriber for db38 database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "db38"


class Db41(DbSubscriber):
    """Subscriber for db41 database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "db41"


class Db44(DbSubscriber):
    """Subscriber for db44 database."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = "db44"
