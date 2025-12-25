"""Protocol for PTR element generators.

This module re-exports the ElementGenerator protocol from attrs_xml
for backward compatibility, with a PTR-specific type annotation.
"""

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord
from loguru import logger as log

from attrs_xml import log, time_element
from attrs_xml.core.decorators import element_define
from attrs_xml.core.fields import element
from ptr_editor import InertialAttitude, LonLatDirection, ObsBlock, TrackAttitude
from ptr_editor.generators.base import PtrElementGenerator

from functools import lru_cache


# generic obs block generator
@element_define
class ObsBlockGen(PtrElementGenerator):
    """Generator for ObsBlock elements."""

    start: pd.Timestamp | None = time_element(default=None, tag="startTime")
    end: pd.Timestamp | None = time_element(default=None, tag="endTime")

    def _element_generate_(self) -> ObsBlock:
        return ObsBlock(start=self.start, end=self.end)


### attitudes
@element_define
class TrackGen(PtrElementGenerator):
    target = element(default="JUPITER", kw_only=True)

    def _element_generate_(self) -> TrackAttitude:
        return TrackAttitude(target=self.target)




@element_define
class StarInertialGenerator(PtrElementGenerator):
    """
    Generator that looks up a star by name and creates an InertialAttitude.
    
    Uses astropy to resolve star names from catalogs (SIMBAD, etc.) and 
    compute RA/Dec coordinates for inertial tracking.
    
    Example:
        >>> gen = StarInertialGenerator(star_name="Betelgeuse")
        >>> attitude = gen._element_generate_()
    """

    star_name = element(kw_only=True)
    """Name of the star to look up (e.g., 'Betelgeuse', 'Sirius', 'Vega')"""

    @lru_cache(maxsize=128)
    def _element_generate_(self) -> InertialAttitude:
        """Generate an InertialAttitude by looking up the star coordinates."""

        # Look up the star using astropy
        # SkyCoord.from_name queries SIMBAD by default
        try:
            coord = SkyCoord.from_name(self.star_name)

            # Extract RA and Dec in degrees
            ra_deg = coord.ra.deg
            dec_deg = coord.dec.deg

            log.info(f"✨ Resolved '{self.star_name}':")
            log.info(f"   RA:  {coord.ra.to_string(unit=u.hour, sep=':', precision=2)}")
            log.info(f"   Dec: {coord.dec.to_string(unit=u.deg, sep=':', precision=2)}")
            log.info(f"   RA (deg):  {ra_deg:.6f}°")
            log.info(f"   Dec (deg): {dec_deg:.6f}°")

            # Create LonLatDirection with RA/Dec
            # In J2000, longitude=RA, latitude=Dec
            target_direction = LonLatDirection(lon=ra_deg, lat=dec_deg)

            # Create and return InertialAttitude
            return InertialAttitude(target=target_direction)

        except Exception as e:
            raise ValueError(f"Failed to resolve star '{self.star_name}': {e}")

