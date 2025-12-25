from __future__ import annotations

from typing import TYPE_CHECKING

from haikunator import Haikunator
import secrets
import string



if TYPE_CHECKING:
    from ptr_editor import ObsBlock

import json
from hashlib import sha256

space_adjectives = [
    "Cosmic",
    "Galactic",
    "Lunar",
    "Solar",
    "Stellar",
    "Orion",
    "Apollo",
    "Ares",
    "Cygnus",
    "Nebula",
    "Pulsar",
    "Quantum",
    "Void",
    "Warp",
    "Deep",
    "Hyperion",
    "Titan",
    "Astro",
    "Nova",
    "Celestial",
    "Infinite",
    "Aurora",
    "Photon",
    "Meteor",
    "Comet",
    "Eclipse",
    "Zenith",
    "Radiant",
    "Eternal",
    "Crimson",
    "Azure",
    "Silver",
    "Golden",
    "Phantom",
    "Starlight",
    "Magnetar",
    "Helios",
    "Andromeda",
    "Cassiopeia",
    "Phoenix",
    "Draco",
    "Lyra",
    "Vega",
    "Sirius",
    "Rigel",
    "Betelgeuse",
    "Altair",
    "Deneb",
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Omega",
    "Prime",
    "Ultra",
    "Mega",
    "Hyper",
    "Super",
    "Trans",
    "Inter",
    "Exo",
    "Proto",
    "Neo",
    "Astral",
    "Celestia",
    "Cosmo",
]

space_nouns = [
    "Odyssey",
    "Pioneer",
    "Voyager",
    "Interceptor",
    "Sentry",
    "Horizon",
    "Probe",
    "Initiative",
    "Pathfinder",
    "Guardian",
    "Resolve",
    "Vanguard",
    "Sentinel",
    "Explorer",
    "Spire",
    "Quest",
    "Relay",
    "Endeavor",
    "Discovery",
    "Challenger",
    "Enterprise",
    "Stargazer",
    "Wayfinder",
    "Navigator",
    "Surveyor",
    "Observer",
    "Seeker",
    "Herald",
    "Beacon",
    "Nexus",
    "Genesis",
    "Exodus",
    "Ascent",
    "Venture",
    "Expedition",
    "Journey",
    "Passage",
    "Transit",
    "Eclipse",
    "Spectra",
    "Vector",
    "Catalyst",
    "Harbinger",
    "Emissary",
    "Envoy",
    "Courier",
    "Messenger",
    "Atlas",
    "Aegis",
    "Bastion",
    "Citadel",
    "Fortress",
    "Bulwark",
    "Tempest",
    "Maelstrom",
    "Cyclone",
    "Typhoon",
    "Nebula",
    "Aurora",
    "Legacy",
    "Destiny",
    "Prophecy",
    "Chronicle",
    "Saga",
    "Legend",
    "Condor",
    "Eagle",
    "Falcon",
    "Hawk",
    "Raven",
    "Phoenix",
    "Paladin",
    "Ranger",
    "Warden",
    "Keeper",
    "Vigil",
    "Watch",
]


def hash_ptr_element(obj):
    obj_dict = obj.as_dict(recurse=True)

    if "metadata" in obj_dict:
        obj_dict.pop("metadata")

    # Convert non-serializable objects to strings
    def make_serializable(value):
        if isinstance(value, dict):
            return {k: make_serializable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [make_serializable(item) for item in value]
        if hasattr(value, "isoformat"):  # For Timestamp/datetime objects
            return value.isoformat()
        try:
            json.dumps(value)  # Test if serializable
            return value
        except TypeError:
            return str(value)  # Fallback to string

    serializable_dict = make_serializable(obj_dict)
    obj_json = json.dumps(serializable_dict, sort_keys=True).encode("utf-8")
    return sha256(obj_json).hexdigest()


def make_unique_codename_id(obj: ObsBlock, exclude_metadata: bool = True) -> str:
    """Generate a unique codename ID for space missions.

    Combines a space-themed codename with a random 4-digit number
    to ensure uniqueness.

    This will be replaced with a bette, context aware implementation.

    Returns:
        str: A unique codename ID.
    """

    if exclude_metadata:
        obj = obj.copy(renew_id=False)
        from ptr_editor.elements.metadata import Metadata
        obj.metadata = Metadata() # Remove metadata for hashing

    hash_obj = hash_ptr_element(obj)

    haiku = Haikunator(adjectives=space_adjectives, nouns=space_nouns, seed=hash_obj)

    codename = haiku.haikunate(token_length=0, delimiter="_")
    # random 6 tokens to ensure uniqueness
    # use both integers and chars

    # Generate 6 random alphanumeric characters
    random_suffix = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
    )
    codename += f"_{random_suffix}"

    return codename.upper()
