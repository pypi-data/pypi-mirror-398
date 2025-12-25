# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import uuid


def generate_entity_id() -> str:
    """Return a new unique identifier for a platform entity.

    :returns: A unique identifier -- a hex string representation of a UUID.
    :rtype: str
    """
    return uuid.uuid4().hex


def null_id() -> str:
    """Return a special identifier signifying that the identity of an entity is not
    important. Used for entities that are "owned" by another entity that has a non-null
    identifier.

    :returns: The null identifier -- a hex string representation of a UUID.
    :rtype: str
    """
    return uuid.UUID(int=0).hex


def namespaced_id(namespace_id: str, entity_name: str) -> str:
    """Return an ID for a named entity whose name is unique within a namespace
    corresponding to another entity ID.

    This is used to model "child" resources that exist within the context of
    a "parent".

    :param namespace_id: The ID of the namespace.
    :type namespace_id: str
    :param entity_name: A name that is unique in the context of the namespace.
    :type entity_name: str
    :returns: The unique identifier of this (namespace, name)
        combination -- a hex string representation of a UUID.
    :rtype: str
    """
    return uuid.uuid5(uuid.UUID(hex=namespace_id), entity_name).hex


def replication_id(evaluation_id: str, replication_index: int) -> str:
    """Return a unique identifier for a replication within an evaluation. Replications
    in different evaluations will have different identifiers, so datasets from different
    evaluations can be combined without worrying about collisions.

    :param evaluation_id: The ID of the Evaluation.
    :type evaluation_id: str
    :param replication_index: The integer index of the replication, in [0...n).
    :type replication_index: int
    :returns: The unique identifier of this (evaluation, replication)
        combination -- a hex string representation of a UUID.
    :rtype: str
    """
    return namespaced_id(evaluation_id, str(replication_index))
