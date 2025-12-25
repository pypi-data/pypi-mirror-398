"""
Utilities for handling external element IDs in treqs-ng.

External IDs follow the pattern: prefix:identifier
where prefix identifies the resolver type (e.g., 'gl', 'jira', 'gh')
and identifier is the external system's ID (e.g., '#96', 'PROJ-123')

Examples:
    gl:#96      -> GitLab issue #96
    jira:PROJ-123 -> Jira ticket PROJ-123
    gh:#456     -> GitHub issue #456
"""

import re


# Pattern for external IDs: word characters followed by colon and anything
EXTERNAL_ID_PATTERN = re.compile(r"^([a-zA-Z0-9_-]+):(.+)$")


def is_external_id(uid: str) -> bool:
    """
    Check if a UID matches the external ID pattern.

    Args:
        uid: The UID to check

    Returns:
        True if the UID follows the external ID pattern (prefix:identifier)
    """
    if not uid:
        return False
    return EXTERNAL_ID_PATTERN.match(uid) is not None


def parse_external_id(uid: str) -> tuple:
    """
    Parse an external ID into its prefix and identifier components.

    Args:
        uid: The external ID to parse (e.g., 'gl:#96')

    Returns:
        Tuple of (prefix, identifier) or (None, None) if not an external ID

    Examples:
        >>> parse_external_id('gl:#96')
        ('gl', '#96')
        >>> parse_external_id('jira:PROJ-123')
        ('jira', 'PROJ-123')
        >>> parse_external_id('normal-id')
        (None, None)
    """
    match = EXTERNAL_ID_PATTERN.match(uid)
    if match:
        return match.group(1), match.group(2)
    return None, None
