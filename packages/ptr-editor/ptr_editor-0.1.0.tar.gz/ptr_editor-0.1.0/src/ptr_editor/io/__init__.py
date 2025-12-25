from copy import deepcopy
import os
from pathlib import Path
from typing import cast, Union

from loguru import logger as log

from ptr_editor.elements.doc import Prm
from ptr_editor.elements.timeline import Timeline, TimelineSourceMetadata
from ptr_editor.services.quick_access import get_elements_registry


def read_ptr(source: Union[os.PathLike, str], *, drop_slews: bool = True) -> Timeline:
    """Read a PTR timeline from either a file path or XML string.

    Automatically detects whether the source is an XML string or file path.
    Strings starting with '<' are treated as XML content, otherwise as file paths.

    Args:
        source: Either a file path (str or PathLike) or XML string content
        drop_slews: If True (default), remove slew blocks from the timeline

    Returns:
        Timeline object parsed from the PTR file or XML string

    Raises:
        FileNotFoundError: If source is a file path that doesn't exist
        ValueError: If no timeline data could be loaded from the XML

    Example:
        >>> # From file
        >>> timeline = read_ptr(
        ...     "path/to/file.ptx"
        ... )
        >>> # From XML string
        >>> xml = '<timeline><block ref="OBS">...</block></timeline>'
        >>> timeline = read_ptr(
        ...     xml
        ... )
    """
    # Determine if source is XML content or file path
    # Strings starting with '<' are treated as XML
    is_xml_string = isinstance(source, str) and source.lstrip().startswith("<")

    if is_xml_string:
        # Parse XML string directly
        xml_content = source
        source_file = None
        log.debug("Reading PTR from XML string")
    else:
        # Treat as file path
        file_path = Path(source).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"PTR file not found: {file_path}")

        log.info(f"Reading PTR from {file_path}")
        xml_content = file_path.read_text(encoding="utf-8")
        source_file = file_path

    # Parse XML content
    log.debug("Parsing PTR XML content")
    ptr = get_elements_registry()

    # Speed up loading by temporarily disabling resolution and defaults
    # XML content should be self-contained, not relying on context defaults
    from ptr_editor.context import get_defaults_config
    from ptr_editor.services import get_resolution_registry

    registry = get_resolution_registry()
    defaults = get_defaults_config()

    with registry.disabled(), defaults.disabled():
        prm: Prm = cast(Prm, ptr.from_xml(xml_content, cls=Prm))

    # Validate that timeline data was loaded
    if not prm or not hasattr(prm, "timeline") or prm.timeline is None:
        source_desc = f"file {source_file}" if source_file else "XML string"
        log.error(f"No timeline data found in PTR {source_desc}")
        raise ValueError(f"No timeline data found in PTR {source_desc}")

    timeline = prm.timeline

    # Set source file metadata only if loaded from a file
    if source_file:
        # Ensure source metadata exists
        if timeline.source is None:
            timeline.source = TimelineSourceMetadata()
        timeline.source.source_file = source_file

    # Remove slew blocks if requested
    if drop_slews:
        timeline.drop_slews()

    return timeline


def save_ptr(
    timeline: Timeline | Prm,
    file_path: os.PathLike,
    *,
    warn_on_overwrite: bool = True,
) -> None:
    """Save the pointing timeline to an XML file.

    It automatically wraps the timeline in a Prm element for saving.

    Args:
        timeline: Timeline or Prm element to save
        file_path: Destination file path
        warn_on_overwrite: If True (default), log a warning when file exists
            and will be overwritten. If False, skip the warning.
    """

    file_path = Path(file_path).resolve()

    if isinstance(timeline, Timeline):
        prm = timeline.as_prm()

    elif isinstance(timeline, Prm):
        prm = timeline

    # Warn if the file already exists and the user wants a warning
    if file_path.exists() and warn_on_overwrite:
        log.warning(f"Overwriting existing PTR file at {file_path}.")

    # Write to a temporary file and atomically replace to avoid partial writes
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    # Ensure the destination directory exists
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"Saving PTR file to {file_path}")
    # Write to temporary file using Path.open
    with tmp_path.open("w", encoding="utf-8") as f:
        f.write(prm.xml)
    # Atomically move into place
    tmp_path.replace(file_path)
