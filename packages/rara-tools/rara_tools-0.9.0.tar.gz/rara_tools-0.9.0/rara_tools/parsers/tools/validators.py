import regex as re
from typing import List

def has_valid_chars(entity: str, allow_cyrillic: bool = True) -> bool:
    """ Checks if entity contains any valid characters in latin
    or in cyrillic, if the latter is enabled

    Parameters
    ------------
    entity: str
        String to validate.
    allow_cyrillic: bool
        Allow strings in cyrillic?

    Returns
    ------------
    bool
        Boolean value indicating, if the string
        contains any valid characters.

    """
    # Check for latin characters
    is_valid = bool(re.search(r"[a-züõöäA-ZÜÕÖÄ]", entity))

    if allow_cyrillic and not is_valid:
        # If cyrillic characters are allowed,
        # check for them as well
        is_valid = bool(re.search(r"[а-яА-Я]", entity))

    return is_valid


def filter_names(names: List[str], allow_cyrillic: bool = True) -> List[str]:
    """ Filters out names not in allowed encodings (latin / cyrillic).

    Parameters
    ------------
    names: List[str]
        Names to filters.
    allow_cyrillic: bool
        Allow strings in cyrillic?

    Returns
    ------------
    List[str]
        List of filtered names.

    """
    filtered_names = [
        name for name in names
        if has_valid_chars(entity=name, allow_cyrillic=allow_cyrillic)
    ]
    return filtered_names
    