# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from abc import ABC, abstractmethod
from typing import Any

from lancedb.table import Table

from geneva.db import Connection
from geneva.utils.schema import alter_or_create_table


class BaseManager(ABC):
    """Abstract base class for Geneva table managers."""

    def __init__(
        self,
        genevadb: Connection,
        table_name: str | None = None,
        namespace: list[str] | None = None,
    ) -> None:
        """Initialize the manager with a database connection and table name.
           This will create the table if it does not exist, using the schema inferred
           from the provided model.

        Args:
            genevadb: The Geneva database connection
            table_name: The table name to use, or None to use the default
            from get_table_name()
            namespace: The namespace to use for the table, or None for
            database-level table
        """
        self.db = genevadb
        table_name = table_name or self.get_table_name()
        self.table = alter_or_create_table(
            genevadb,
            table_name,
            self.get_model(),
            namespace=namespace,
        )

    @abstractmethod
    def get_table_name(self) -> str:
        """Return the table name for this manager.

        Returns:
            The table name
        """

    @abstractmethod
    def get_model(self) -> Any:
        """Return the model for this manager.

        Returns:
            The model instance used to generate the schema
        """

    def get_table(self, checkout_latest: bool = False) -> Table:
        """Get the underlying Lance table.

        Args:
            checkout_latest: Whether to checkout the latest version
            for strongly consistent reads

        Returns:
            The Lance table instance
        """
        t = self.table._ltbl  # pyright: ignore[reportAttributeAccessIssue]
        if checkout_latest:
            # ensure strongly consistent reads
            t.checkout_latest()
        return t
