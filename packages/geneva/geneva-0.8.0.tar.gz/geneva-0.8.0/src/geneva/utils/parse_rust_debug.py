# SPDX-License-Identifier: PROPRIETARY
# SPDX-FileCopyrightText: Copyright The Geneva Authors

import lance

__all__ = ["extract_field_ids"]


def extract_subfield_ids(field) -> list[int]:
    """Extract field id from a LanceField and all its children."""
    ids = [field.id()]
    for child in field.children():
        ids.extend(extract_subfield_ids(child))
    return ids


def extract_field_ids(schema: lance.lance.LanceSchema, field_name: str) -> list[int]:
    """Gets the field id of the specified field name and its children if they
    are a compound type or nested compound type.

    Parameters
    ----------
    schema : lance.lance.LanceSchema
        The Lance schema to search in.
    field_name : str
        The name of the field to search for.

    Raises
    ------
    ValueError
        If the field is not found in the schema.
    """
    for field in schema.fields():
        if field.name() == field_name:
            return extract_subfield_ids(field)
    else:
        raise ValueError("Field not found in schema: " + field_name)
