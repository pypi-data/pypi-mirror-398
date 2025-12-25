"""
Look up country information
"""

import functools

from countryguess import guess_country as _guess_country


def _list_or_string(func):
    @functools.wraps(func)
    def wrapper(arg):
        if isinstance(arg, str):
            return func(arg)
        else:
            return tuple(func(country) for country in arg)

    return wrapper


@_list_or_string
def name(country):
    """
    Convert fuzzy country name to consistent name

    :param country: Country name or code, e.g. "Russian Federation" (official
        name), "USA" (common abbreviation), "Korea" (short name), "fr"
        (2-character country code), etc.
    :type country: str or sequence

    :return: Country name or `country` if it can't be associated with any
        country
    """
    return _guess_country(country, attribute='name_short', default=country)


@_list_or_string
def iso2(country):
    """
    Convert fuzzy country name to ISO 3166-1 alpha-2 codes

    :param country: Country name or code, e.g. "Russian Federation" (official
        name), "USA" (common abbreviation), "Korea" (short name), "fr"
        (2-character country code), etc.
    :type country: str or sequence

    :return: Country code or `country` if it can't be associated with any
        country
    """
    return _guess_country(country, attribute='iso2', default=country)


@_list_or_string
def tld(country):
    """
    Convert fuzzy country name to top level domain

    :param country: Country name or code, e.g. "Russian Federation" (official
        name), "USA" (common abbreviation), "Korea" (short name), "fr"
        (2-character country code), etc.
    :type country: str or sequence

    :return: Country TLD or `country` if it can't be associated with any country
    """
    return _guess_country(country, attribute='cctld', default=country)
