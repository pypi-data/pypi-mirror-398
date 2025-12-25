# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

from typing import Optional

from lance.io import StorageOptionsProvider
from lance.namespace import LanceNamespaceStorageOptionsProvider
from lance_namespace import DescribeTableRequest
from lance_namespace import connect as namespace_connect


def get_storage_options_provider(
    namespace_impl: Optional[str],
    namespace_properties: Optional[dict[str, str]],
    table_id: Optional[list[str]],
) -> tuple[Optional[StorageOptionsProvider], Optional[dict[str, str]]]:
    """Get the storage options provider and storage options for the given namespace
     implementation and properties.

    Args:
        namespace_impl: The namespace implementation type
        namespace_properties: The namespace properties
        table_id: The list of table IDs

    Returns:
        The storage options provider and the storage options dict,
        or both None if not applicable
    """

    if namespace_impl is None or namespace_properties is None or table_id is None:
        return None, None

    namespace_client = namespace_connect(namespace_impl, namespace_properties)
    # Only set provider if namespace provides storage_options
    response = namespace_client.describe_table(DescribeTableRequest(id=table_id))
    if response.storage_options is None:
        return None, None

    return (
        LanceNamespaceStorageOptionsProvider(namespace_client, table_id),
        response.storage_options,
    )
