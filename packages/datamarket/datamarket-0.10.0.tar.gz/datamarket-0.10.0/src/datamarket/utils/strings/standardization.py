########################################################################################################################
# IMPORTS

import re
from typing import Literal

from ...params.nominatim import COUNTRY_PARSING_RULES

########################################################################################################################
# FUNCTIONS


def parse_phone_number(number: str, country_code: Literal["es", "pt"]) -> str | None:
    """Clean and standardize phone number from a certain country_code

    Args:
        number (str): phone number
        country_code (Literal["es", "pt"]): country code of the phone number to parse

    Raises:
        ValueError: when parsing is not supported for a certain country

    Returns:
        str | None: standardized phone number
    """
    clean_number = re.sub(r"\D", "", number)
    if country_code in {"es", "pt"}:
        # Get the validation regex from params
        pattern = COUNTRY_PARSING_RULES[country_code]["phone_validate_pattern"]

        # Validate and extract in one step
        if len(clean_number) >= 9:  # Check if the cleaned number has at least 9 digits
            match = pattern.match(clean_number)

            # Return the captured group (the 9-digit number)
            return match.group(0)[-9:] if match else None
        else:
            return None  # Or handle the case where the number is too short
    else:
        raise ValueError(f"Country code ({country_code}) is not currently supported")
