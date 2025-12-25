"""Generic File Manager for organizing and querying versioned files by instrument and version.

Supports PTR, ITL, OPL, and other files following the JUICE versioning schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os
from collections import Counter
from pathlib import Path

from attrs import define, field
from loguru import logger as log

from .file_info import VersionedFileInfo

# mapping of instrument shortnames
# TODO(luca.penasa@inaf.it) not used currently, and incomplete. Probably can be removed.
JUICE_INSTRUMENTS_SHORTNAMES = {
    "MAJ": "MAJIS",
    "UVS": "UVS",
    "SOC": "SOC",
    "JAN": "JANUS",
    "SWI": "SWI",
    "PEL": "PEP-Low",
    "PEH": "PEP-High",
}


@define
class VersionedFileManager:
    """Manages a collection of versioned files with querying capabilities.
    
    Supports PTR, ITL, OPL, and other files following the JUICE versioning schema.
    """

    files: list[VersionedFileInfo] = field(factory=list)
    scenario: str | None = field(default=None)
    prefix: str | None = field(default=None)
    unmatched_files: list[Path] = field(factory=list)
    max_soc_version: int | None = field(default=None)

    def __attrs_post_init__(self):
        """Auto-detect scenario and prefix if not provided."""
        if self.scenario is None:
            object.__setattr__(self, "scenario", self._infer_scenario())
        if self.prefix is None:
            object.__setattr__(self, "prefix", self._infer_prefix())

    def _infer_scenario(self) -> str | None:
        """Infer the most common scenario from the file collection."""
        if not self.files:
            return None

        scenario_counts = Counter(f.scenario for f in self.files)
        return scenario_counts.most_common(1)[0][0]

    def _infer_prefix(self) -> str | None:
        """Infer the most common file prefix from the collection."""
        if not self.files:
            return None

        prefix_counts = Counter(f.prefix for f in self.files)
        return prefix_counts.most_common(1)[0][0]

    @classmethod
    def from_directory(
        cls,
        directory: os.PathLike | str,
        pattern: str = "*_*_S*_*_S*P*.*",
        scenario: str | None = None,
        recursive: bool = False,
        prefix: str | None = None,
        prefix_pattern: str = r"[A-Z]{3}",
        extension_pattern: str = r"[a-z]+",
        max_soc_version: int | None = None,
    ) -> VersionedFileManager:
        """
        Load all versioned files from a directory.

        Args:
            directory: Path to the directory containing files
            pattern: Glob pattern for matching files (default matches all versioned files)
            scenario: Optional scenario identifier; auto-detected if not provided
            recursive: If True, search recursively in subdirectories using rglob
            prefix: Optional file prefix filter (e.g., 'PTR', 'ITL', 'OPL')
            prefix_pattern: Regex pattern for the file prefix (default: 3 uppercase letters)
            extension_pattern: Regex pattern for the extension (default: 1+ lowercase letters)
            max_soc_version: Optional max SOC version to include (filters out later versions)

        Returns:
            VersionedFileManager instance with parsed files

        Examples:
            # Load all PTR files
            >>> VersionedFileManager.from_directory("/path", "PTR_*.ptx")
            
            # Load all ITL files
            >>> VersionedFileManager.from_directory("/path", "ITL_*.itl")
            
            # Load only files up to SOC version 8
            >>> VersionedFileManager.from_directory("/path", max_soc_version=8)
            
            # Load recursively
            >>> VersionedFileManager.from_directory("/path", recursive=True)
        """

        directory = Path(directory)
        files = []
        unmatched = []
        glob_method = directory.rglob if recursive else directory.glob
        for path in glob_method(pattern):
            info = VersionedFileInfo.from_path(
                path,
                prefix_pattern=prefix_pattern,
                extension_pattern=extension_pattern,
            )
            if info:
                # Filter by prefix if specified
                if prefix is None or info.prefix == prefix.upper():
                    # Filter by max_soc_version if specified
                    if max_soc_version is None or (
                        info.soc_version is not None
                        and info.soc_version <= max_soc_version
                    ):
                        files.append(info)
                else:
                    # Track files filtered out by prefix
                    unmatched.append(path)
            else:
                # Track files that didn't match the pattern
                unmatched.append(path)

        return cls(
            files=files,
            scenario=scenario,
            prefix=prefix,
            unmatched_files=unmatched,
            max_soc_version=max_soc_version,
        )

    @classmethod
    def from_paths(
        cls,
        paths: list[os.PathLike | str],
        scenario: str | None = None,
        prefix: str | None = None,
        prefix_pattern: str = r"[A-Z]{3}",
        extension_pattern: str = r"[a-z]+",
        max_soc_version: int | None = None,
    ) -> VersionedFileManager:
        """
        Create manager from a list of paths.

        Args:
            paths: List of Path objects to files
            scenario: Optional scenario identifier; auto-detected if not provided
            prefix: Optional file prefix filter (e.g., 'PTR', 'ITL', 'OPL')
            prefix_pattern: Regex pattern for the file prefix
            extension_pattern: Regex pattern for the extension (default: 1+ lowercase letters)
            max_soc_version: Optional max SOC version to include (filters out later versions)

        Returns:
            VersionedFileManager instance with parsed files
        """
        files = []
        unmatched = []
        for path in paths:
            info = VersionedFileInfo.from_path(
                path,
                prefix_pattern=prefix_pattern,
                extension_pattern=extension_pattern,
            )
            if info:
                # Filter by prefix if specified
                if prefix is None or info.prefix == prefix.upper():
                    # Filter by max_soc_version if specified
                    if max_soc_version is None or (
                        info.soc_version is not None
                        and info.soc_version <= max_soc_version
                    ):
                        files.append(info)
                else:
                    # Track files filtered out by prefix
                    unmatched.append(Path(path))
            else:
                # Track files that didn't match the pattern
                unmatched.append(Path(path))

        return cls(
            files=files,
            scenario=scenario,
            prefix=prefix,
            unmatched_files=unmatched,
            max_soc_version=max_soc_version,
        )

    def _sort_by_version(
        self, files: list[VersionedFileInfo],
    ) -> list[VersionedFileInfo]:
        """Sort files by version, putting SXXPYY files at the end."""
        return sorted(
            files,
            key=lambda f: (
                f.soc_version is None,
                f.soc_version or 0,
                f.pi_version or 0,
            ),
        )

    def filter_by_instrument(self, instrument: str) -> list[VersionedFileInfo]:
        """
        Get all files for a specific instrument, sorted by version.

        Args:
            instrument: Three-letter instrument code (e.g., 'MAJ', 'SOC', 'UVS')

        Returns:
            List of VersionedFileInfo for the specified instrument,
            sorted by SOC version then PI version (SXXPYY files last)
        """
        filtered = [f for f in self.files if f.instrument == instrument.upper()]
        return self._sort_by_version(filtered)

    def filter_by_scenario(self, scenario: str) -> list[VersionedFileInfo]:
        """
        Get all files for a specific scenario, sorted by version.

        Args:
            scenario: Scenario identifier (e.g., 'S008_01')

        Returns:
            List of VersionedFileInfo for the specified scenario,
            sorted by SOC version then PI version (SXXPYY files last)
        """
        filtered = [f for f in self.files if f.scenario == scenario]
        return self._sort_by_version(filtered)

    def filter_by_prefix(self, prefix: str) -> list[VersionedFileInfo]:
        """
        Get all files with a specific prefix (PTR, ITL, OPL, etc.).

        Args:
            prefix: File type prefix (e.g., 'PTR', 'ITL', 'OPL')

        Returns:
            List of VersionedFileInfo with the specified prefix
        """
        filtered = [f for f in self.files if f.prefix == prefix.upper()]
        return self._sort_by_version(filtered)

    def filter_by_provider(self, provider: str) -> list[VersionedFileInfo]:
        """
        Get all files delivered by a specific provider (SOC or instrument).

        Args:
            provider: Provider instrument code (e.g., 'SOC', 'MAJ', 'JAN')

        Returns:
            List of VersionedFileInfo delivered by the specified provider

        Examples:
            # Get all files delivered by SOC (pi_version == 0)
            >>> manager.filter_by_provider('SOC')
            
            # Get all files where MAJIS provided the content (pi_version > 0)
            >>> manager.filter_by_provider('MAJ')
        """
        filtered = [
            f for f in self.files if f.provider_instrument == provider.upper()
        ]
        return self._sort_by_version(filtered)

    def filter_soc_deliveries(self) -> list[VersionedFileInfo]:
        """
        Get all SOC deliveries (files with pi_version == 0).

        Returns:
            List of VersionedFileInfo where SOC was the provider
        """
        return [f for f in self.files if f.is_soc_delivery]

    def filter_pi_deliveries(self) -> list[VersionedFileInfo]:
        """
        Get all PI deliveries (files with pi_version > 0).

        Returns:
            List of VersionedFileInfo where instrument teams provided content
        """
        return [f for f in self.files if f.is_pi_delivery]

    def get_latest_version(
        self,
        instrument: str | None = None,
        scenario: str | None = None,
        prefix: str | None = None,
    ) -> VersionedFileInfo | None:
        """
        Get the file with the highest version number.
        Excludes SXXPYY files (planning system copies).

        Args:
            instrument: Optional instrument filter
            scenario: Optional scenario filter
            prefix: Optional file type prefix filter (e.g., 'PTR', 'ITL', 'OPL')

        Returns:
            VersionedFileInfo with highest SOC and PI version, or None if no files found
        """
        candidates = self.files

        if instrument:
            candidates = [f for f in candidates if f.instrument == instrument.upper()]

        if scenario:
            candidates = [f for f in candidates if f.scenario == scenario]

        if prefix:
            candidates = [f for f in candidates if f.prefix == prefix.upper()]

        # Exclude SXXPYY copies
        candidates = [f for f in candidates if not f.is_sxxpyy_copy]

        if not candidates:
            return None

        return max(candidates, key=lambda f: f.version_tuple)

    def get_all_instruments(self) -> list[str]:
        """Get a sorted list of all unique instruments."""
        return sorted({f.instrument for f in self.files})

    def get_all_scenarios(self) -> list[str]:
        """Get a sorted list of all unique scenarios."""
        return sorted({f.scenario for f in self.files})

    def get_primary_scenario(self) -> str | None:
        """Get the most common scenario in the file collection.

        Returns:
            The scenario with the most files, or None if no files exist.
        """
        if not self.files:
            return None

        scenario_counts = Counter(f.scenario for f in self.files)
        return scenario_counts.most_common(1)[0][0]

    def group_by_instrument(self) -> dict[str, list[VersionedFileInfo]]:
        """
        Group all files by instrument.

        Returns:
            Dictionary mapping instrument codes to lists of VersionedFileInfo
        """
        result = {}
        for instrument in self.get_all_instruments():
            result[instrument] = self.filter_by_instrument(instrument)
        return result

    def group_by_scenario(self) -> dict[str, list[VersionedFileInfo]]:
        """
        Group all files by scenario.

        Returns:
            Dictionary mapping scenario identifiers to lists of VersionedFileInfo
        """
        result = {}
        for scenario in self.get_all_scenarios():
            result[scenario] = self.filter_by_scenario(scenario)
        return result

    def group_by_prefix(self) -> dict[str, list[VersionedFileInfo]]:
        """
        Group all files by prefix (PTR, ITL, OPL, etc.).

        Returns:
            Dictionary mapping file prefixes to lists of VersionedFileInfo
        """
        result = {}
        prefixes = sorted({f.prefix for f in self.files})
        for prefix in prefixes:
            result[prefix] = self.filter_by_prefix(prefix)
        return result

    def get_latest_per_instrument(
        self,
        scenario: str | None = None,
        prefix: str | None = None,
    ) -> dict[str, VersionedFileInfo]:
        """
        Get the latest version for each instrument.

        Args:
            scenario: Optional scenario filter
            prefix: Optional file type prefix filter (e.g., 'PTR', 'ITL', 'OPL')

        Returns:
            Dictionary mapping instrument codes to their latest VersionedFileInfo
        """
        result = {}
        for instrument in self.get_all_instruments():
            latest = self.get_latest_version(
                instrument=instrument,
                scenario=scenario,
                prefix=prefix,
            )
            if latest:
                result[instrument] = latest
        return result

    def get_files_for_soc_version(
        self,
        soc_version: int,
        scenario: str | None = None,
        instruments: list[str] | None = None,
        prefix: str | None = None,
    ) -> dict[str, VersionedFileInfo]:
        """
        Get the latest PI version files for each instrument at a given SOC version.

        This returns files that match a specific SOC version (S number), finding
        the highest P version for each instrument. Useful for collecting all
        instrument responses to a particular SOC delivery.

        Args:
            soc_version: SOC version number to filter by
            scenario: Scenario identifier (auto-detected if not provided)
            instruments: Optional list of instruments to include (all if None)
            prefix: Optional file type prefix filter (e.g., 'PTR', 'ITL', 'OPL')

        Returns:
            Dictionary mapping instrument codes to their latest PI delivery
            for the specified SOC version

        Example:
            # Get all PTR files responding to SOC delivery S08
            >>> manager.get_files_for_soc_version(
            ...     soc_version=8, prefix='PTR'
            ... )
            {'SOC': S08P00, 'MAJ': S08P03, 'JAN': S08P02, 'UVS': S08P01, ...}
        """
        if scenario is None:
            scenario = self.scenario
            if scenario is None:
                return {}

        target_instruments = instruments or self.get_all_instruments()

        result = {}
        for instrument in target_instruments:
            # Filter to files matching the SOC version
            candidates = [
                f
                for f in self.files
                if f.instrument == instrument
                and f.scenario == scenario
                and f.soc_version == soc_version
                and not f.is_sxxpyy_copy
                and (prefix is None or f.prefix == prefix.upper())
            ]

            if candidates:
                # Get the one with highest PI version
                latest = max(candidates, key=lambda f: f.pi_version or 0)
                result[instrument] = latest

        return result

    def get_latest_pi_versions_for_soc(
        self,
        soc_version: int | None = None,
        scenario: str | None = None,
        prefix: str | None = None,
    ) -> dict[str, VersionedFileInfo]:
        """
        Get the latest PI version for each PI instrument for a specific SOC version.

        This method returns only actual PI responses (pi_version > 0) and excludes:
        - SOC instrument files
        - Files where pi_version=0 (these are SOC deliveries, not PI responses)

        If you want all files including SOC deliveries, use get_files_for_soc_version() instead.

        Args:
            soc_version: SOC version to filter by (uses latest if not provided)
            scenario: Scenario identifier (auto-detected if not provided)
            prefix: Optional file type prefix filter (e.g., 'PTR', 'ITL', 'OPL')

        Returns:
            Dictionary mapping instrument codes to their latest PI delivery
            for the specified SOC version (only files with pi_version > 0)

        Example:
            # Get all latest PI responses to SOC delivery S08
            >>> manager.get_latest_pi_versions_for_soc(
            ...     soc_version=8
            ... )
            {'MAJ': S08P03, 'JAN': S08P02, 'UVS': S08P01, ...}
            # Note: Files like 'MAJ_S08P00' (SOC delivery) are excluded
        """
        if scenario is None:
            scenario = self.scenario
            if scenario is None:
                return {}

        # If no SOC version specified, find the latest
        if soc_version is None:
            soc_file = self.get_latest_version(
                instrument="SOC",
                scenario=scenario,
                prefix=prefix,
            )
            if soc_file is None or soc_file.soc_version is None:
                return {}
            soc_version = soc_file.soc_version

        # Get all files for this SOC version
        all_files = self.get_files_for_soc_version(
            soc_version=soc_version,
            scenario=scenario,
            instruments=None,  # Get all instruments
            prefix=prefix,
        )

        # Filter to only PI responses: exclude SOC instrument and pi_version=0 files
        pi_responses = {
            instrument: file_info
            for instrument, file_info in all_files.items()
            if instrument != "SOC" and file_info.pi_version is not None and file_info.pi_version > 0
        }

        return pi_responses

    def predict_next_version(
        self,
        instrument: str,
        scenario: str | None = None,
        is_soc_delivery: bool | None = None,
    ) -> tuple[int, int]:
        """
        Predict the next version number for an instrument.

        Args:
            instrument: Instrument code
            scenario: Scenario identifier (auto-detected if not provided)
            is_soc_delivery: If True, predict next SOC delivery (increment S, reset P to 0).
                           If False, predict next PI delivery (keep S, increment P).
                           If None (default), auto-detect based on instrument:
                           - True for instrument='SOC'
                           - False for other instruments

        Returns:
            Tuple of (soc_version, pi_version)

        Examples:
            # Next PI delivery for MAJIS (after SOC delivered S08P00)
            >>> manager.predict_next_version("MAJ")
            (8, 1)
            
            # Next SOC delivery for MAJIS (after MAJIS responded with S08P02)
            >>> manager.predict_next_version("MAJ", is_soc_delivery=True)
            (9, 0)
            
            # Next SOC delivery (SOC instrument always increments S)
            >>> manager.predict_next_version("SOC")
            (9, 0)
        """
        # Auto-detect if this is a SOC delivery
        if is_soc_delivery is None:
            is_soc_delivery = instrument.upper() == "SOC"

        if scenario is None:
            scenario = self.scenario
            if scenario is None:
                return (1, 0)

        latest = self.get_latest_version(instrument=instrument, scenario=scenario)

        if latest is None or latest.soc_version is None or latest.pi_version is None:
            # No existing version, start at S01P00
            return (1, 0)

        if is_soc_delivery:
            # SOC delivery: increment SOC version, reset PI version to 00
            return (latest.soc_version + 1, 0)
        # PI delivery: keep SOC version, increment PI version
        return (latest.soc_version, latest.pi_version + 1)

    def format_version_string(
        self,
        instrument: str,
        scenario: str,
        soc_version: int,
        pi_version: int,
        prefix: str | None = None,
        extension: str | None = None,
    ) -> str:
        """
        Format a complete filename for the given version.

        Args:
            instrument: Instrument code (e.g., 'MAJ', 'SOC')
            scenario: Scenario identifier (e.g., 'S008_01')
            soc_version: SOC version number
            pi_version: PI version number
            prefix: File type prefix (auto-detected if not provided)
            extension: File extension (auto-detected if not provided)

        Returns:
            Formatted filename string (e.g., 'PTR_MAJ_S008_01_S05P01.ptx')
        """
        inst = instrument.upper()

        # Auto-detect prefix if not provided
        if prefix is None:
            prefix = self.prefix or "PTR"

        # Auto-detect extension from existing files if not provided
        if extension is None:
            existing = self.get_latest_version(instrument=instrument, scenario=scenario)
            if existing:
                extension = existing.extension
            else:
                # Fallback to common extensions based on prefix
                extension_map = {
                    "PTR": "ptx",
                    "ITL": "itl",
                    "OPL": "csv",
                }
                extension = extension_map.get(prefix.upper(), "txt")

        return f"{prefix.upper()}_{inst}_{scenario}_S{soc_version:02d}P{pi_version:02d}.{extension}"

    def format_next_filename(
        self,
        instrument: str,
        soc_version: int,
        pi_version: int,
        scenario: str | None = None,
        prefix: str | None = None,
        extension: str | None = None,
        as_path: bool = True,
    ) -> str | Path:
        """
        Format a filename for a given version.

        Args:
            instrument: Instrument code
            soc_version: SOC version number
            pi_version: PI version number
            scenario: Scenario identifier (auto-detected if not provided)
            prefix: File type prefix (auto-detected if not provided)
            extension: File extension (auto-detected if not provided)
            as_path: If True (default), return full Path; if False, return str

        Returns:
            Full path (Path) if as_path=True, or filename (str) if as_path=False
        """
        if scenario is None:
            scenario = self.scenario
            if scenario is None:
                scenario = "S000_00"

        filename = self.format_version_string(
            instrument, scenario, soc_version, pi_version, prefix, extension,
        )

        if not as_path:
            return filename

        # Get directory from an existing file for this instrument/scenario
        existing = self.get_latest_version(instrument=instrument, scenario=scenario)
        if existing and existing.path:
            return existing.path.parent / filename

        # Fallback: try to get directory from any file
        if self.files:
            return self.files[0].path.parent / filename

        # Last resort: return as Path with just the filename
        return Path(filename)

    def predict_next_filename(
        self,
        instrument: str,
        scenario: str | None = None,
        prefix: str | None = None,
        extension: str | None = None,
        *,
        is_soc_delivery: bool | None = None,
        as_path: bool = True,
    ) -> str | Path:
        """
        Predict the filename/path for the next delivery.

        Args:
            instrument: Instrument code
            scenario: Scenario identifier (auto-detected if not provided)
            prefix: File type prefix (auto-detected if not provided)
            extension: File extension (auto-detected if not provided)
            is_soc_delivery: If True, predict SOC delivery (S+1, P=0).
                           If False, predict PI delivery (S same, P+1).
                           If None, auto-detect (True for 'SOC', False otherwise).
            as_path: If True (default), return full Path; if False, return str

        Returns:
            Full path (Path) if as_path=True, or filename (str) if as_path=False

        Examples:
            # Next PI delivery for MAJIS (after SOC delivered S08P00)
            >>> manager.predict_next_filename("MAJ")
            Path('/data/.../PTR_MAJ_S008_01_S08P01.ptx')
            
            # Next SOC delivery for MAJIS (SOC provides new version)
            >>> manager.predict_next_filename("MAJ", is_soc_delivery=True)
            Path('/data/.../PTR_MAJ_S008_01_S09P00.ptx')
            
            # Next SOC delivery from SOC instrument
            >>> manager.predict_next_filename("SOC")
            Path('/data/.../PTR_SOC_S008_01_S09P00.ptx')
            
            # Override extension
            >>> manager.predict_next_filename("MAJ", extension="csv", as_path=False)
            'PTR_MAJ_S008_01_S08P02.csv'
        """
        soc_v, pi_v = self.predict_next_version(instrument, scenario, is_soc_delivery)
        return self.format_next_filename(
            instrument, soc_v, pi_v, scenario, prefix, extension, as_path,
        )

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, filename: str) -> VersionedFileInfo:
        """
        Access a file by filename using dictionary-like syntax.

        Args:
            filename: The filename to search for (e.g., 'PTR_MAJ_S008_01_S08P02.ptx')

        Returns:
            VersionedFileInfo for the matching file

        Raises:
            KeyError: If no file with the given filename is found

        Example:
            >>> manager['PTR_MAJ_S008_01_S08P02.ptx']
            VersionedFileInfo(...)
        """
        import logging

        matches = [f for f in self.files if f.filename == filename]

        if not matches:
            raise KeyError(f"No file found with filename: {filename}")

        if len(matches) > 1:
            logging.warning(
                f"Multiple files found with filename '{filename}': {len(matches)} matches. "
                f"Returning the first one. Paths: {[str(f.path) for f in matches]}",
            )

        return matches[0]

    def verify_sxxpyy_copies(
        self,
        scenario: str | None = None,
    ) -> dict[str, dict[str, bool | str]]:
        """
        Verify that all SXXPYY files are exact copies of their corresponding latest versions.

        SXXPYY files should be identical to the latest versioned file for each instrument
        in the scenario. This method checks if the file contents match and logs warnings
        for any issues found.

        Args:
            scenario: Scenario identifier (auto-detected if not provided)

        Returns:
            Dictionary mapping instrument codes to verification results:
            {
                'instrument': {
                    'has_sxxpyy': bool,
                    'has_latest': bool,
                    'is_valid_copy': bool,
                    'sxxpyy_file': str (filename),
                    'latest_file': str (filename),
                    'reason': str (explanation if invalid)
                }
            }

        Example:
            >>> results = manager.verify_sxxpyy_copies()
            >>> for inst, result in results.items():
            ...     if not result['is_valid_copy']:
            ...         print(f"{inst}: {result['reason']}")
        """
        import filecmp

        if scenario is None:
            scenario = self.scenario
            if scenario is None:
                return {}

        results = {}

        # Group files by instrument
        for instrument in self.get_all_instruments():
            instrument_files = self.filter_by_instrument(instrument)

            # Find SXXPYY file
            sxxpyy_files = [f for f in instrument_files if f.is_sxxpyy_copy]

            # Find latest versioned file
            latest = self.get_latest_version(
                instrument=instrument, scenario=scenario,
            )

            result = {
                "has_sxxpyy": len(sxxpyy_files) > 0,
                "has_latest": latest is not None,
                "is_valid_copy": False,
                "sxxpyy_file": None,
                "latest_file": None,
                "reason": "",
            }

            if len(sxxpyy_files) > 0:
                sxxpyy_file = sxxpyy_files[0]
                result["sxxpyy_file"] = sxxpyy_file.filename

                if len(sxxpyy_files) > 1:
                    result["reason"] = (
                        f"Multiple SXXPYY files found ({len(sxxpyy_files)})"
                    )
                    log.warning(
                        f"Instrument {instrument}: Multiple SXXPYY files found ({len(sxxpyy_files)})",
                    )
                elif latest is None:
                    result["reason"] = (
                        "SXXPYY exists but no versioned file found to compare"
                    )
                    log.warning(
                        f"Instrument {instrument}: SXXPYY file '{sxxpyy_file.filename}' exists but no versioned file found to compare",
                    )
                else:
                    result["latest_file"] = latest.filename

                    # Compare file contents
                    if filecmp.cmp(sxxpyy_file.path, latest.path, shallow=False):
                        result["is_valid_copy"] = True
                        result["reason"] = "Files are identical"
                    else:
                        result["reason"] = (
                            f"Files differ: SXXPYY ({sxxpyy_file.filename}) "
                            f"!= Latest ({latest.filename})"
                        )
                        log.warning(
                            f"Instrument {instrument}: SXXPYY file '{sxxpyy_file.filename}' differs from latest version '{latest.filename}'",
                        )
            elif latest is not None:
                result["latest_file"] = latest.filename
                result["reason"] = "No SXXPYY file found"
                log.warning(
                    f"Instrument {instrument}: No SXXPYY file found (latest is '{latest.filename}')",
                )
            else:
                result["reason"] = "No files found for this instrument"

            results[instrument] = result

        return results

    def __repr__(self) -> str:
        return (
            f"PtrFileManager({len(self.files)} files, "
            f"{len(self.get_all_instruments())} instruments)"
        )

    def _repr_html_(self) -> str:
        from .html import repr_html_manager
        return repr_html_manager(self)


