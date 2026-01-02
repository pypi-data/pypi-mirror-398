"""Common types and enums for Blizzard API."""

from enum import Enum


class Region(str, Enum):
    """Blizzard API regions."""

    US = "us"
    EU = "eu"
    KR = "kr"
    TW = "tw"
    CN = "cn"


class Locale(str, Enum):
    """Blizzard API locales."""

    # English
    EN_US = "en_US"
    EN_GB = "en_GB"

    # Spanish
    ES_MX = "es_MX"
    ES_ES = "es_ES"

    # Portuguese
    PT_BR = "pt_BR"
    PT_PT = "pt_PT"

    # French
    FR_FR = "fr_FR"

    # German
    DE_DE = "de_DE"

    # Italian
    IT_IT = "it_IT"

    # Russian
    RU_RU = "ru_RU"

    # Korean
    KO_KR = "ko_KR"

    # Chinese
    ZH_TW = "zh_TW"
    ZH_CN = "zh_CN"


# Mapping of regions to their default locales
REGION_LOCALES: dict[Region, list[Locale]] = {
    Region.US: [Locale.EN_US, Locale.ES_MX, Locale.PT_BR],
    Region.EU: [Locale.EN_GB, Locale.ES_ES, Locale.FR_FR, Locale.DE_DE, Locale.IT_IT, Locale.PT_PT, Locale.RU_RU],
    Region.KR: [Locale.KO_KR],
    Region.TW: [Locale.ZH_TW],
    Region.CN: [Locale.ZH_CN],
}


def get_default_locale(region: Region | str) -> Locale:
    """Get the default locale for a region.

    Args:
        region: The region to get the default locale for

    Returns:
        The default locale for the region

    Raises:
        ValueError: If the region is invalid
    """
    if isinstance(region, str):
        try:
            region = Region(region)
        except ValueError:
            raise ValueError(f"Invalid region: {region}")

    locales = REGION_LOCALES.get(region)
    if not locales:
        raise ValueError(f"No locales defined for region: {region}")

    return locales[0]
