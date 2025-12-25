########################################################################################################################
# IMPORTS

from typing import Literal, Optional

from rapidfuzz import fuzz, process
from unidecode import unidecode

from ..params.nominatim import (
    _NORMALIZED_PROVINCE_CACHE,
    COUNTRY_PARSING_RULES,
    POSTCODE_TO_STATES,
    PROVINCE_TO_POSTCODE,
    PROVINCES,
    STANDARD_THRESHOLD,
    STATES,
)
from .strings import normalize

########################################################################################################################
# FUNCTIONS


def standardize_admin_division(
    name: str,
    level: Literal["province", "state"] = "province",
    country_code: str = "es",
) -> Optional[str]:
    """
    Normalize and standardize administrative divisions of a given country using RapidFuzz.
    Uses normalized dict keys for comparison and returns dict values with the official names.
    """
    if not name:
        return None

    country_code = country_code.lower()
    mapping = STATES.get(country_code) if level == "state" else PROVINCES.get(country_code)

    if not mapping:  # If country is not standardized, return raw name
        return name

    normalized_name = normalize(name)  # Essential for rapidfuzz to work well
    result = process.extractOne(
        normalized_name,
        mapping.keys(),  # Compare with the normalized names in the dict
        scorer=fuzz.WRatio,
        score_cutoff=STANDARD_THRESHOLD,
    )

    if not result:
        return None

    best_key, score, _ = result

    # Return the standardized name corresponding to the normalized name
    return mapping[best_key]


def parse_state(
    zip_code: str,
    country_code: str,
) -> str | None:
    """Given a zip code and a country code, returns the state in which the zip code is located

    Args:
        zip_code (str)
        country_code (str)

    Returns:
        str | None: state if coincidence found, else None
    """
    country_postcodes = POSTCODE_TO_STATES.get(country_code, {})
    state = country_postcodes.get(zip_code[:2], None)
    return state


def _province_postcode_match(
    address: str,
    zip_code: str,
    country_code: str,
) -> str | None:
    """
    Match and return province with the start of all of its zip codes
    using a pre-computed cache and rapidfuzz for efficient matching.

    Args:
        address (str)
        zip_code (str)
        country_code (str)

    Returns:
        str | None:
    """
    # Get the pre-computed cache for the country
    cache = _NORMALIZED_PROVINCE_CACHE.get(country_code)
    if not cache:
        return None  # Country not configured

    normalized_address = unidecode(address).lower()

    # Use the cached 'choices' list for the search
    result = process.extractOne(
        normalized_address,
        cache["choices"],  # <-- Uses pre-computed list
        scorer=fuzz.partial_ratio,
        score_cutoff=100,
    )

    if not result:
        return None  # No exact substring match found

    # We only need the index from the result
    _, _, index = result

    # Get the original province name from the cached 'keys' list
    original_province = cache["keys"][index]  # <-- Uses pre-computed list

    # Get the postcode prefix from the original map
    province_map = PROVINCE_TO_POSTCODE.get(country_code, {})
    postcode_prefix = province_map[original_province]

    return postcode_prefix + zip_code[1:] if len(zip_code) == 4 else zip_code


def _parse_es_zip_code(
    zip_code: str,
    address: str,
    opt_address: str | None,
) -> str:
    """parse spain zip code"""

    # Get the validation regex from params
    validate_regex = COUNTRY_PARSING_RULES["es"]["zip_validate_pattern"]

    if validate_regex.match(zip_code):
        return zip_code
    else:
        # Use search regex from params
        pattern = COUNTRY_PARSING_RULES["es"]["zip_search_pattern"]

        match = pattern.search(address)
        if match:
            return match.group()
        if opt_address:
            match = pattern.search(opt_address)
            if match:
                return match.group()

        province_match = _province_postcode_match(address, zip_code, country_code="es")
        return province_match or zip_code


def _parse_pt_zip_code(
    zip_code: str,
    address: str,
    opt_address: str | None,
) -> str:
    """parse portugal zip code"""

    # Get the validation regex from params
    validate_regex = COUNTRY_PARSING_RULES["pt"]["zip_validate_pattern"]

    if validate_regex.match(zip_code):
        return zip_code
    else:
        # Use search regex from params
        pattern = COUNTRY_PARSING_RULES["pt"]["zip_search_pattern"]

        match = pattern.search(address)
        if match is None and opt_address:
            match = pattern.search(opt_address)

        return match.group() if match else zip_code


def parse_zip_code(
    address: str,
    zip_code: str,
    country_code: str,
    opt_address: str | None = None,
) -> str | None:
    """Parse and standardize zip code

    Args:
        address (str): written address
        zip_code (str)
        country_code (str):
        opt_address (str | None, optional): optional extra address, usually None. Defaults to None.

    Raises:
        ValueError: when parsing zip code is not supported for the passed country_code

    Returns:
        str | None
    """
    if country_code == "es":
        return _parse_es_zip_code(zip_code, address, opt_address)
    elif country_code == "pt":
        return _parse_pt_zip_code(zip_code, address, opt_address)
    else:
        raise ValueError(f"Country code ({country_code}) is not currently supported")
