"""VersionedFileInfo class for representing parsed versioned filenames."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os
import re
from pathlib import Path

from attrs import define, field


@define
class VersionedFileInfo:
    """Represents a parsed versioned filename with instrument and version information.

    Filename format: {PREFIX}_{INSTRUMENT}_{SCENARIO}_{SOCVERSION}P{PIVERSION}.{EXT}
    Examples:
        - PTR_MAJ_S008_01_S05P01.ptx (PTR file: MAJIS, S008_01, SOC v5, PI v1)
        - ITL_SOC_S008_01_S08P00.itl (ITL file: SOC, S008_01, SOC v8, PI v0)
        - OPL_JAN_S008_01_S08P02.csv (OPL file: JANUS, S008_01, SOC v8, PI v2)
        - PTR_SOC_S008_01_SXXPYY.ptx (copy of latest for planning system)

    Attributes:
        path: Full path to the file
        prefix: File type prefix (PTR, ITL, OPL, etc.)
        instrument: Three-letter instrument code (owner of the file)
        scenario: Scenario identifier (e.g., S008_01)
        soc_version: SOC version number (None for SXXPYY files)
        pi_version: PI version number (None for SXXPYY files)
        extension: File extension

    Properties:
        owner_instrument: Same as instrument (the instrument this file belongs to)
        provider_instrument: Who delivered this version ('SOC' if pi_version==0, 
                           else owner_instrument)
        is_soc_delivery: True if this file was delivered by SOC (pi_version==0)
        is_pi_delivery: True if this file was delivered by the PI (pi_version>0)

    Note: SXXPYY files are copies of the latest version loaded by the planning
    system (PHS/MAPPS/OSVE), not templates. They should be excluded from version
    comparisons when determining the actual latest versioned file.
    """

    path: Path = field(converter=lambda x: Path(x).resolve())
    prefix: str = field()
    instrument: str = field()
    scenario: str = field()
    soc_version: int | None = field()  # None for SXXPYY files
    pi_version: int | None = field()  # None for SXXPYY files
    extension: str = field()
    filename: str = field(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, "filename", self.path.name)

    @property
    def owner_instrument(self) -> str:
        """The instrument that owns this file (from filename).
        
        This is always the instrument code from the filename, regardless of
        who delivered the file.
        """
        return self.instrument

    @property
    def provider_instrument(self) -> str:
        """The instrument that provided/delivered this version.
        
        Returns 'SOC' if pi_version is 0 (SOC delivery), otherwise returns
        the owner instrument (PI delivery).
        
        For SXXPYY files, returns the owner instrument.
        """
        if self.pi_version is None:
            # SXXPYY files - owner instrument
            return self.instrument
        if self.pi_version == 0:
            # SOC delivery
            return "SOC"
        # PI delivery
        return self.instrument

    @property
    def is_soc_delivery(self) -> bool:
        """True if this file was delivered by SOC (pi_version == 0).
        
        SOC deliveries represent files that SOC created/modified for an instrument,
        which the instrument team hasn't yet responded to.
        """
        return self.pi_version == 0

    @property
    def is_pi_delivery(self) -> bool:
        """True if this file was delivered by the PI team (pi_version > 0).
        
        PI deliveries represent responses from instrument teams to SOC deliveries.
        """
        return self.pi_version is not None and self.pi_version > 0

    @classmethod
    def from_path(
        cls,
        path: os.PathLike | str,
        prefix_pattern: str = r"[A-Z]{3}",
        extension_pattern: str = r"[a-z]+",
    ) -> VersionedFileInfo | None:
        """
        Parse a versioned filename and extract instrument and version information.

        Expected format: <PREFIX>_<INSTRUMENT>_<SCENARIO>_S<XX>P<YY>.<EXT>
        Examples:
            - PTR_MAJ_S008_01_S05P01.ptx (MAJIS, S008_01, SOC v5, PI v1)
            - ITL_SOC_S008_01_S08P00.itl (SOC, S008_01, SOC v8, PI v0)
            - OPL_JAN_S008_01_SXXPYY.csv (copy of latest for planning system)

        Args:
            path: Path to the file
            prefix_pattern: Regex pattern for the file prefix (default: 3 uppercase letters)
            extension_pattern: Regex pattern for the extension (default: 1+ lowercase letters)

        Returns:
            VersionedFileInfo if parsing succeeds, None otherwise.
        """

        path = Path(path)
        pattern = (
            rf"({prefix_pattern})_([A-Z0-9]{{3}})_S(\d{{3}})_(\d{{2}})_"
            rf"S(\d{{2}}|XX)P(\d{{2}}|YY)\.({extension_pattern})"
        )
        match = re.match(pattern, path.name)

        if not match:
            return None

        prefix, instrument, scenario_num, scenario_sub, soc_ver, pi_ver, ext = (
            match.groups()
        )

        # SXXPYY files are copies of the latest version for the planning system
        # Store as None so they can be excluded from version comparisons
        soc_version = None if soc_ver == "XX" else int(soc_ver)
        pi_version = None if pi_ver == "YY" else int(pi_ver)

        return cls(
            path=path,
            prefix=prefix,
            instrument=instrument,
            scenario=f"S{scenario_num}_{scenario_sub}",
            soc_version=soc_version,
            pi_version=pi_version,
            extension=ext,
        )

    @property
    def is_sxxpyy_copy(self) -> bool:
        """Check if this is an SXXPYY copy file (for planning system)."""
        return self.soc_version is None

    @property
    def version_tuple(self) -> tuple[int, int]:
        """Return (SOC version, PI version) tuple.

        Raises ValueError for SXXPYY files.
        """
        if self.soc_version is None or self.pi_version is None:
            msg = "SXXPYY files don't have numeric versions"
            raise ValueError(msg)
        return (self.soc_version, self.pi_version)

    def __fspath__(self) -> str:
        """Return the file system path representation.

        This makes VersionedFileInfo a PathLike object that can be used
        anywhere a path is expected (e.g., open(), Path(), etc.).
        """
        return str(self.path)

    def __str__(self) -> str:
        if self.soc_version is None:
            ver = "SXXPYY (PHS copy)"
        else:
            ver = f"S{self.soc_version:02d}P{self.pi_version:02d}"

        # Add provider info if it differs from owner
        provider_info = ""
        if self.provider_instrument != self.owner_instrument:
            provider_info = " [SOC delivery]"

        return f"{self.prefix}:{self.instrument} {ver}{provider_info}: {self.filename}"

    def _repr_html_(self) -> str:
        from .html import repr_html_file_info
        return repr_html_file_info(self)
