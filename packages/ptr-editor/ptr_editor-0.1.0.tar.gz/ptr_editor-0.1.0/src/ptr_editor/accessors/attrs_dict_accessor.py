"""Dictionary accessor for attrs-based classes with cached, flattened dot-notation paths."""

from __future__ import annotations

from typing import Any

import attrs
from loguru import logger as log


class AttrsDictAccessor:
    """Provides a dict-like interface to attrs objects with flattened dot-notation paths.
    
    This accessor allows read/write access to nested attrs attributes using
    dot-separated paths like "metadata.planning.observations.designer".
    
    Lists are not supported. Circular references are detected and skipped.
    By default, attributes starting with underscore are not accessible.
    
    Example:
        class MyBlock(TimeSegmentMixin):
            metadata: Metadata = field(factory=Metadata)
            
            @property
            def __ts_metadata__(self):
                return AttrsDictAccessor(self)
        
        block = MyBlock()
        block["metadata.planning.designer"] = "John"
        print(block["metadata.planning.designer"])  # "John"
    """

    def __init__(
        self,
        root_obj: Any,
        *,
        allow_private: bool = False,
        skip_names: list[str] | None = None,
        include_names: list[str] | None = None,
    ):
        """Initialize the accessor with a root attrs object.
        
        Args:
            root_obj: The root attrs object to provide access to
            allow_private: If False (default), skip attributes starting with underscore
            skip_names: List of attribute names or paths to skip entirely.
                Can be simple names like "parent" or full paths like "metadata.parent"
            include_names: List of non-attrs attribute names to include (e.g., properties).
                These will be accessible even though they're not attrs fields.
                Can be simple names like "duration" or full paths like "metadata.computed_value"
        """
        self._root = root_obj
        self._allow_private = allow_private
        self._skip_names = set(skip_names) if skip_names else set()
        self._include_names = set(include_names) if include_names else set()

    def _get_all_paths(self) -> dict[str, Any]:
        """Get all accessible paths by traversing the attrs object tree.
        
        Returns:
            Dictionary mapping dot-separated paths to their values
        """
        paths: dict[str, Any] = {}
        visited: set[int] = set()  # Track visited objects by id to prevent cycles

        def _traverse(obj: Any, prefix: str = "") -> None:
            """Recursively traverse attrs objects and build path->value mappings."""
            if not attrs.has(obj.__class__):
                # Not an attrs object, store the value
                if prefix:
                    paths[prefix.rstrip(".")] = obj
                return

            # Check for circular reference
            obj_id = id(obj)
            if obj_id in visited:
                log.debug(f"Circular reference detected at {prefix}, skipping")
                return

            visited.add(obj_id)

            # Get all attrs fields
            for field in attrs.fields(obj.__class__):
                field_name = field.name

                # Skip private attributes if not allowed
                if not self._allow_private and field_name.startswith("_"):
                    log.debug(f"Skipping private attribute: {field_name}")
                    continue

                current_path = f"{prefix}{field_name}"

                # Skip if name or path is in skip list
                if field_name in self._skip_names or current_path in self._skip_names:
                    log.debug(f"Skipping configured skip name/path: {current_path}")
                    continue

                try:
                    value = getattr(obj, field_name)
                except Exception as e:
                    log.debug(f"Could not access {current_path}: {e}")
                    continue

                # Skip None values
                if value is None:
                    paths[current_path] = None
                    continue

                # Skip lists (not supported)
                if isinstance(value, list):
                    log.debug(f"Skipping list at {current_path}")
                    continue

                # Store the value at this level
                paths[current_path] = value

                # Recursively traverse if it's an attrs object
                if attrs.has(value.__class__):
                    _traverse(value, f"{current_path}.")

            # Remove from visited when done (allow revisiting in different branches)
            visited.discard(obj_id)

            # Process included non-attrs attributes
            for include_name in self._include_names:
                # Check if this is a simple name or a path
                if "." in include_name:
                    # It's a path - only process if it starts with current prefix
                    expected_prefix = prefix.rstrip(".")
                    if include_name.startswith(expected_prefix + "." if expected_prefix else ""):
                        # Extract the remaining part after the current prefix
                        if expected_prefix:
                            remaining = include_name[len(expected_prefix) + 1:]  # +1 for the dot
                        else:
                            remaining = include_name

                        # Only process if this is the final attribute in the path
                        if "." not in remaining:
                            attr_name = remaining
                            if hasattr(obj, attr_name):
                                current_path = f"{prefix}{attr_name}"
                                try:
                                    value = getattr(obj, attr_name)
                                    paths[current_path] = value
                                    log.debug(f"Added included attribute: {current_path}")
                                except Exception as e:
                                    log.debug(f"Could not access included attribute {current_path}: {e}")
                # Simple name - add at root level only
                elif not prefix and hasattr(obj, include_name):
                    try:
                        value = getattr(obj, include_name)
                        paths[include_name] = value
                        log.debug(f"Added included attribute: {include_name}")
                    except Exception as e:
                        log.debug(f"Could not access included attribute {include_name}: {e}")

        _traverse(self._root)
        return paths

    def _get_nested_attr(self, path: str) -> Any:
        """Get a nested attribute value by dot-separated path.
        
        Args:
            path: Dot-separated path like "metadata.planning.designer"
            
        Returns:
            The value at the specified path
            
        Raises:
            AttributeError: If path doesn't exist or contains private attributes
        """
        parts = path.split(".")
        obj = self._root

        # Check for private attributes in path
        if not self._allow_private:
            for part in parts:
                if part.startswith("_"):
                    raise AttributeError(
                        f"Access to private attribute '{part}' in path '{path}' is not allowed",
                    )

        for part in parts:
            if not hasattr(obj, part):
                raise AttributeError(f"Path '{path}' not found at '{part}'")
            obj = getattr(obj, part)

        return obj

    def _set_nested_attr(self, path: str, value: Any) -> None:
        """Set a nested attribute value by dot-separated path.
        
        Args:
            path: Dot-separated path like "metadata.planning.designer"
            value: Value to set
            
        Raises:
            AttributeError: If path doesn't exist or contains private attributes
        """
        parts = path.split(".")

        # Check for private attributes in path
        if not self._allow_private:
            for part in parts:
                if part.startswith("_"):
                    raise AttributeError(
                        f"Access to private attribute '{part}' in path '{path}' is not allowed",
                    )

        obj = self._root

        # Navigate to the parent object
        for part in parts[:-1]:
            if not hasattr(obj, part):
                raise AttributeError(f"Path '{path}' not found at '{part}'")
            obj = getattr(obj, part)

            # Create intermediate attrs objects if they're None
            if obj is None:
                raise AttributeError(
                    f"Cannot set '{path}': intermediate object at '{part}' is None",
                )

        # Set the final attribute
        final_attr = parts[-1]
        if not hasattr(obj, final_attr):
            raise AttributeError(
                f"Path '{path}' not found: no attribute '{final_attr}'",
            )

        setattr(obj, final_attr, value)

    def __getitem__(self, key: str) -> Any:
        """Get value by dot-separated path.
        
        Args:
            key: Dot-separated path
            
        Returns:
            Value at the path
            
        Raises:
            KeyError: If path not found
        """
        try:
            return self._get_nested_attr(key)
        except AttributeError as e:
            raise KeyError(str(e)) from e

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value by dot-separated path.
        
        Args:
            key: Dot-separated path
            value: Value to set
            
        Raises:
            KeyError: If path not found
        """
        try:
            self._set_nested_attr(key, value)
        except AttributeError as e:
            raise KeyError(str(e)) from e

    def __contains__(self, key: str) -> bool:
        """Check if a path exists in the accessible paths.
        
        Args:
            key: Dot-separated path
            
        Returns:
            True if path exists and is accessible, False otherwise
        """
        # Check if the key is in the accessible paths (respects skip_names, allow_private, etc.)
        paths = self._get_all_paths()
        return key in paths

    def keys(self) -> list[str]:
        """Get all available paths.
        
        Returns:
            List of all dot-separated paths
        """
        paths = self._get_all_paths()
        return list(paths.keys())

    def values(self) -> list[Any]:
        """Get all values.
        
        Returns:
            List of all values
        """
        paths = self._get_all_paths()
        return list(paths.values())

    def items(self) -> list[tuple[str, Any]]:
        """Get all path-value pairs.
        
        Returns:
            List of (path, value) tuples
        """
        paths = self._get_all_paths()
        return list(paths.items())

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with a default fallback.
        
        Args:
            key: Dot-separated path
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __repr__(self) -> str:
        """String representation showing available paths."""
        paths = self._get_all_paths()
        return f"<AttrsDictAccessor with {len(paths)} paths>"

    def __len__(self) -> int:
        """Number of available paths."""
        paths = self._get_all_paths()
        return len(paths)
