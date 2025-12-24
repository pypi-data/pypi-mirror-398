"""Type definitions for internacia SDK data structures."""

from typing import TypedDict, List, Optional, Dict


class CapitalCity(TypedDict, total=False):
    """Capital city information."""
    name: str
    lng: float
    lat: float


class Region(TypedDict, total=False):
    """World Bank region information."""
    id: str
    value: str


class IncomeLevel(TypedDict, total=False):
    """World Bank income level information."""
    id: str
    value: str


class Language(TypedDict, total=False):
    """Language information."""
    code: str
    name: str
    official: bool


class Currency(TypedDict, total=False):
    """Currency information."""
    code: str
    name: str
    symbol: str


class NativeName(TypedDict, total=False):
    """Native name information."""
    official: str
    common: str


class Country(TypedDict, total=False):
    """Country data structure."""
    code: str
    name: str
    iso3code: str
    numeric_code: str
    official_name: Optional[str]
    capital_city: Optional[CapitalCity]
    region: Optional[Region]
    incomeLevel: Optional[IncomeLevel]
    languages: List[Language]
    currencies: List[Currency]
    un_member: bool
    independent: bool
    continents: List[str]
    borders: List[str]
    native_names: Dict[str, NativeName]
    # Additional fields may exist in the database


class Translation(TypedDict, total=False):
    """Translation information."""
    lang: str
    name: str


class Acronym(TypedDict, total=False):
    """Acronym information."""
    lang: str
    value: str


class Topic(TypedDict, total=False):
    """Topic information."""
    key: str
    name: str


class Member(TypedDict, total=False):
    """Member country information."""
    id: str
    name: str
    type: Optional[str]
    status: Optional[str]


class Intblock(TypedDict, total=False):
    """International block data structure."""
    id: str
    name: str
    blocktype: List[str]
    status: str
    translations: List[Translation]
    acronyms: List[Acronym]
    includes: List[Member]
    founded: Optional[str]
    geographic_scope: Optional[str]
    tags: List[str]
    topics: List[Topic]
    # Additional fields may exist in the database


class SearchResult(TypedDict, total=False):
    """Search result with type indicator."""
    type: str  # 'country' or 'intblock'
    # All fields from Country or Intblock depending on type
