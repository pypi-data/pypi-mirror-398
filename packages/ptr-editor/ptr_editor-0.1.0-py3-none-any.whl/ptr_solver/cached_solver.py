import re
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from hashlib import sha256
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import platformdirs
from attrs import define, field
from loguru import logger as log
from planetary_coverage import SpicePool

from ptr_editor.elements.timeline import Timeline

from .ptr_solver import (
    PtrSolution,
    solve_attitude,
)

USER_CACHE_DIR = Path(platformdirs.user_cache_dir("ptr-solver"))



def clean_xml(xml_string, tags_to_remove):
    # Remove comments using regex
    xml_string = re.sub(r"<!--.*?-->", "", xml_string, flags=re.DOTALL)

    # Parse the XML string
    root = ET.fromstring(xml_string)

    # Function to recursively remove unwanted tags
    def remove_tags_recursive(element):
        for child in list(element):
            if child.tag in tags_to_remove:
                element.remove(child)
            else:
                remove_tags_recursive(child)

    # Remove the specified tags
    remove_tags_recursive(root)

    # Convert the cleaned XML to a string
    compressed_xml = ET.tostring(root, encoding="unicode")

    # Minify XML by removing unnecessary whitespace
    return re.sub(r">\s+<", "><", compressed_xml).strip()


def hash_list_of_strings(string_list, sort=False):
    # Optionally sort the list if the order doesn't matter
    if sort:
        string_list = sorted(string_list)

    # Join the strings with a consistent separator
    combined_string = "|".join(string_list)

    # Encode the combined string to bytes
    encoded_string = combined_string.encode("utf-8")

    # Compute the SHA-256 hash
    hash_object = sha256(encoded_string)

    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()


def spice_pool_hash():
    kernels = [k for k in SpicePool.kernels if not k.endswith(".tm")]
    log.debug("Computing currently loaded kernels hash using")

    # for k in kernels:
    #     log.debug(k)

    return hash_list_of_strings(kernels)[:8]


def get_ptwrapper_version() -> str:
    """Get the ptwrapper version string."""
    try:
        return version("ptwrapper")
    except PackageNotFoundError:
        log.warning("Could not determine ptwrapper version, using 'unknown'")
        return "unknown"


def get_osve_version() -> str:
    """Get the OSVE version string."""
    try:
        return version("osve")
    except PackageNotFoundError:
        log.warning("Could not determine osve version, using 'unknown'")
        return "unknown"


def multi_type_to_str(value: str | list[str] | Timeline | None) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, Timeline):
       return value.as_prm().xml


    if hasattr(value, "xml"):
        return value.xml
    if hasattr(value, "_element_generate_"):
        elem = value._element_generate_()
        return multi_type_to_str(elem)

    if isinstance(value, Sequence) and not isinstance(value, str):
        tml = Timeline(value)
        tml.insert_slews()
        return tml.xml

    return ""


@define
class CachedPtrSolver:
    ptr_text: str = field(default="", converter=multi_type_to_str)
    cache_folder: Path = field(default=USER_CACHE_DIR / "pointings")
    metakernel: str = field(default="5_1_150lb_23_1_a3")
    use_cache: bool = field(default=True)

    @classmethod
    def from_file(cls, file, **kwargs):
        return cls(Path(file).open("r").read(), **kwargs)

    def ptr_hash(self):
        txt = clean_xml(self.ptr_text, {"metadata"})
        return sha256(txt.encode()).hexdigest()[:8]

    def make_unique_cache_key(self):
        ptwrapper_version = get_ptwrapper_version()
        osve_version = get_osve_version()
        log.debug(
            f"Cache key includes ptwrapper version: {ptwrapper_version}, "
            f"osve version: {osve_version}",
        )
        return (
            f"{self.ptr_hash()}_{spice_pool_hash()}_"
            f"ptw{ptwrapper_version}_osve{osve_version}"
        )

    def unique_ck_path(self):
        return (self.cache_folder / self.make_unique_cache_key()).with_suffix(".ck")

    def unique_cache_path(self):
        return self.cache_folder / self.make_unique_cache_key()

    def solve(self) -> PtrSolution:
        log.debug(f"Solving ptr. using cache dir {self.cache_folder}")

        folder = self.unique_cache_path()

        folder.mkdir(exist_ok=True, parents=True)

        ck_name = folder / "result.ck"

        if ck_name.exists() and self.use_cache:
            log.debug(
                f"Ck already there (at {ck_name.absolute()}). "
                "Not recomputing as cache is enabled.",
            )
            return PtrSolution(ck_file=ck_name.absolute())
        return solve_attitude(
            self.ptr_text,
            out_folder=folder,
            ck_name="result.ck",
            metakernel=self.metakernel,
        )
