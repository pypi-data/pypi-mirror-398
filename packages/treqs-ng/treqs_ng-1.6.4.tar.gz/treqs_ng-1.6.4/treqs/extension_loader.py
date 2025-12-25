"""
Extension loader for treqs-ng

Discovers and loads resolver callbacks from installed treqsext packages
via Python entry points.

Extensions register resolvers using the entry point group 'treqs.resolvers'.
This allows external packages to provide element resolution without
modifying treqs core.

Example entry point in an extension's setup.py:
    entry_points={
        'treqs.resolvers': [
            'gl = treqsext_gitlab:resolve_element',
        ],
    }

The entry point name should match the prefix used in external IDs.
For example, an entry point named 'gl' handles external IDs like 'gl:#96'.

Resolvers accept external ID strings like 'gl:#96' or 'jira:PROJ-123'.
"""

import logging

from treqs.external_id_utils import parse_external_id

try:
    from importlib.metadata import entry_points
except ImportError:
    # Python < 3.8 compatibility
    from importlib_metadata import entry_points


def load_resolver_callback():
    """
    Discover and load element resolvers from extensions.

    Extensions register resolvers via entry point group
    'treqs.resolvers'. Returns a callback function that dispatches to
    the appropriate resolver based on the external ID prefix.

    Each resolver should have signature:
        def resolver(external_id: str) -> dict or None:
            # external_id is an external ID like 'gl:project#96' or
            # 'jira:PROJ-123'
            prefix, identifier = parse_external_id(external_id)
            if prefix != "my-type":
                return None

            # Resolve using identifier...
            # Fetch data from external system...

            return {
                'uid': str,            # Element UID (required)
                'text': str,           # Resolved element text (required)
                'label': str,          # Resolved label (optional)
                'type': str,           # Element type (optional)
                'attributes': dict,    # Additional attributes (optional)
            }

    Returns:
        Callable or None: Composite resolver callback that tries all
                         registered resolvers, or None if no
                         resolvers found
    """
    logger = logging.getLogger("treqs-on-git.treqs-ng")

    try:
        eps = entry_points()

        # Handle different versions of importlib.metadata API
        if hasattr(eps, "select"):
            # Python 3.10+ API
            discovered = eps.select(group="treqs.resolvers")
        elif hasattr(eps, "get"):
            # Python 3.9 API
            discovered = eps.get("treqs.resolvers", [])
        else:
            # Python 3.8 API (dict-like)
            discovered = eps.get("treqs.resolvers", [])

        # Load all registered resolvers and build type mapping
        type_map = {}  # Maps external_type -> (name, resolver)

        for ep in discovered:
            try:
                resolver = ep.load()
                # Use entry point name as type hint
                # Extensions should name their entry point after the
                # type they want to handle
                type_hint = ep.name
                type_map[type_hint] = (type_hint, resolver)
                logger.log(
                    10,
                    f"Loaded resolver '{type_hint}' from extension",
                )
            except Exception as e:
                logger.log(
                    30,
                    f"Failed to load resolver '{ep.name}': {e}",
                )

        if not type_map:
            logger.log(10, "No external resolvers found")
            return None

        # Return an optimized composite resolver with type mapping
        def composite_resolver(external_id):
            """
            Resolve element using type mapping for efficiency.

            Accepts an external ID string like 'gl:#96'.

            First tries resolver registered for the ID prefix,
            then falls back to trying all resolvers if no match.
            """
            # Parse external ID to get type prefix
            external_type, identifier = parse_external_id(external_id)

            # Fast path: Direct type mapping lookup
            if external_type and external_type in type_map:
                name, resolver = type_map[external_type]
                try:
                    result = resolver(external_id)
                    if result is not None:
                        logger.log(
                            10,
                            f"External ID '{external_id}' resolved by "
                            f"'{name}' (direct match)",
                        )
                        return result
                except Exception as e:
                    logger.log(
                        30,
                        f"Resolver '{name}' failed for '{external_id}': {e}",
                    )

            # Fallback: Try all other resolvers
            # (in case entry point name doesn't match prefix)
            for type_hint, (name, resolver) in type_map.items():
                # Skip the one we already tried
                if type_hint == external_type:
                    continue

                try:
                    result = resolver(external_id)
                    if result is not None:
                        logger.log(
                            10,
                            f"External ID '{external_id}' resolved by "
                            f"'{name}' (fallback search)",
                        )
                        return result
                except Exception as e:
                    # Silently continue - expected for wrong type
                    continue

            # No resolver handled this element
            logger.log(
                10,
                f"No resolver found for external ID '{external_id}'",
            )
            return None

        return composite_resolver

    except Exception as e:
        logger.log(30, f"Error discovering resolvers: {e}")
        return None
