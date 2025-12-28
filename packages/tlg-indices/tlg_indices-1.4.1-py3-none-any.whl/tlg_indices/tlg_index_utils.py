"""Read and return data from the author index files."""

from dataclasses import dataclass
import re
from typing import Optional, Union
from tlg_indices.indices.author_id_to_author_name import AUTHOR_ID_TO_AUTHOR_NAME
from tlg_indices.indices.author_ids_to_works import AUTHOR_ID_TO_WORKS
from tlg_indices.data_types import AuthorID, WorkID
from tlg_indices.indices.date_to_author_id import MAP_DATE_TO_AUTHORS
from tlg_indices.indices.epithet_to_author_id import MAP_EPITHET_TO_AUTHOR_IDS
from tlg_indices.indices.female_author_ids import FEMINAE
from tlg_indices.indices.geography_to_author_id import GEO_TO_AUTHOR_ID
from tlg_indices.indices.tlg_indices import ALL_TLG_INDICES


# Allows an O(1) lookup
_EPITHET_INDEX_CASEFOLD: dict[str, list[AuthorID]] = {
    key.casefold(): value for key, value in MAP_EPITHET_TO_AUTHOR_IDS.items()
}
# Reverse index
_AUTHOR_ID_TO_EPITHET: dict[AuthorID, str] = {
    author_id: epithet
    for epithet, author_ids in MAP_EPITHET_TO_AUTHOR_IDS.items()
    for author_id in author_ids
}
_GEO_INDEX_CASEFOLD: dict[str, list[AuthorID]] = {
    key.casefold(): value for key, value in GEO_TO_AUTHOR_ID.items()
}
_AUTHOR_ID_TO_GEO: dict[AuthorID, str] = {
    author_id: geo
    for geo, author_ids in GEO_TO_AUTHOR_ID.items()
    for author_id in author_ids
}
_AUTHOR_NAME_INDEX_CASEFOLD: dict[str, AuthorID] = {
    name.casefold(): author_id for author_id, name in AUTHOR_ID_TO_AUTHOR_NAME.items()
}


def get_indices() -> dict[str, dict[str, str]]:
    """Return all of the TLG's indices."""
    return ALL_TLG_INDICES


def get_all_authors_ids() -> list[AuthorID]:
    """Open author ids index and return sorted list of author ids."""
    return sorted(AUTHOR_ID_TO_AUTHOR_NAME.keys())


def get_female_authors() -> list[AuthorID]:
    """Open female authors index and return sorted list of author ids."""
    return sorted(FEMINAE)


def get_epithet_index() -> dict[str, list[AuthorID]]:
    """Return dict of epithets (key) to a set of all
    author ids of that epithet (value).
    """
    return MAP_EPITHET_TO_AUTHOR_IDS


def get_epithets() -> list[str]:
    """Return a list of all the epithet labels."""
    return sorted(MAP_EPITHET_TO_AUTHOR_IDS.keys())


def get_authors_by_epithet(epithet: str) -> list[AuthorID]:
    """Pass exact name (case-insensitive) of
    epithet name, return ordered list of author ids.
    """
    ids = _EPITHET_INDEX_CASEFOLD.get(epithet.casefold())
    if ids is None:
        return list()
    return sorted(ids)


def get_epithet_of_author(author_id: Union[AuthorID, str]) -> Optional[str]:
    """Pass author id and return the name of its associated epithet."""
    return _AUTHOR_ID_TO_EPITHET.get(AuthorID(author_id))


def get_geo_index() -> dict[str, list[AuthorID]]:
    """Get entire index of geographic name (key) and
    author ids (value).
    """
    return GEO_TO_AUTHOR_ID


def get_geographies() -> list[str]:
    """Return a list of all the geography labels."""
    return sorted(GEO_TO_AUTHOR_ID.keys())


def get_authors_by_geo(geo: str) -> list[AuthorID]:
    """Pass exact name (case-insensitive) of
    geography name, return ordered list of author ids.
    """
    ids = _GEO_INDEX_CASEFOLD.get(geo.casefold())
    if ids is None:
        return list()
    return sorted(ids)


def get_geo_of_author(author_id: Union[AuthorID, str]) -> Optional[str]:
    """Pass author id and return the name of its associated geography."""
    return _AUTHOR_ID_TO_GEO.get(AuthorID(author_id))


def author_id_to_author_name() -> dict[AuthorID, str]:
    """Returns entirety of id-author TLG index."""
    return AUTHOR_ID_TO_AUTHOR_NAME


def get_author_name_from_author_id(author_id: Union[AuthorID, str]) -> Optional[str]:
    """Pass author id and return a string with the author label"""
    return AUTHOR_ID_TO_AUTHOR_NAME.get(AuthorID(author_id))


def get_author_id_from_author_name(name: str) -> Optional[AuthorID]:
    """Pass author name and return a string with the author id"""
    return _AUTHOR_NAME_INDEX_CASEFOLD.get(name.casefold())


def get_author_works_index() -> dict[AuthorID, dict[WorkID, str]]:
    """Returns entirety of id-author TLG index."""
    return AUTHOR_ID_TO_WORKS


def get_works_by_author_id(author_id: Union[AuthorID, str]) -> dict[WorkID, str]:
    """Pass author id and return a dictionary of its works."""
    return AUTHOR_ID_TO_WORKS[AuthorID(author_id)]


def get_work_name(
    author_id: Union[AuthorID, str], work_id: Union[WorkID, str]
) -> Optional[str]:
    """Pass author id and work id and return the work name."""
    works = AUTHOR_ID_TO_WORKS.get(AuthorID(author_id))
    if works is None:
        return None
    return works.get(WorkID(work_id))


# Dates


def get_date_author() -> dict[str, list[AuthorID]]:
    """Returns entirety of date-author index."""
    return MAP_DATE_TO_AUTHORS


def get_dates() -> list[str]:
    """Return a list of all the date epithet labels."""
    return sorted(MAP_DATE_TO_AUTHORS.keys())


def get_date_of_author(author_id: Union[AuthorID, str]) -> Optional[str]:
    """Pass author id and return the name of its associated date."""
    return _AUTHOR_ID_TO_DATE.get(AuthorID(author_id))


_AUTHOR_ID_TO_DATE: dict[AuthorID, str] = {
    author_id: date
    for date, author_ids in MAP_DATE_TO_AUTHORS.items()
    for author_id in author_ids
}
_DATE_SORT_SENTINEL = 10**9
_SPECIAL_DATE_SORT_KEYS: dict[str, tuple[int, int, int, int, str]] = {
    "Incertum": (_DATE_SORT_SENTINEL, _DATE_SORT_SENTINEL, 9, 0, "Incertum"),
    "Varia": (_DATE_SORT_SENTINEL, _DATE_SORT_SENTINEL, 9, 1, "Varia"),
}
_QUALIFIER_RE = re.compile(r"^\s*([ap])\.\s*", re.IGNORECASE)
_ERA_RE = re.compile(r"(A\.D\.|B\.C\.)", re.IGNORECASE)
_CENTURY_RE = re.compile(r"(\d+)")


@dataclass(frozen=True)
class ParsedDate:
    raw: Optional[str]
    start_century: Optional[int]
    start_era: Optional[str]
    end_century: Optional[int]
    end_era: Optional[str]
    start_qualifier: Optional[str]
    end_qualifier: Optional[str]
    uncertain: bool
    special: Optional[str]

    def sort_key(self) -> tuple[int, int, int, int, str]:
        """Return a sort key that handles ranges and qualifiers."""
        return get_date_sort_key(self)


def _parse_century_part(
    part: str, default_era: Optional[str]
) -> tuple[Optional[int], Optional[str], Optional[str]]:
    part = part.strip()
    qualifier = None
    qualifier_match = _QUALIFIER_RE.match(part)
    if qualifier_match:
        qualifier = qualifier_match.group(1).lower()
        part = part[qualifier_match.end() :]
    era_match = _ERA_RE.search(part)
    era = None
    if era_match:
        era_token = era_match.group(1).upper()
        era = "AD" if era_token.startswith("A") else "BC"
        part = _ERA_RE.sub("", part)
    part = part.replace("?", "")
    century_match = _CENTURY_RE.search(part)
    if not century_match:
        return None, era or default_era, qualifier
    century = int(century_match.group(1))
    era = era or default_era
    if era is None:
        return None, None, qualifier
    return century, era, qualifier


def _qualifier_rank(parsed: "ParsedDate") -> int:
    has_a = parsed.start_qualifier == "a" or parsed.end_qualifier == "a"
    has_p = parsed.start_qualifier == "p" or parsed.end_qualifier == "p"
    if has_a and not has_p:
        return -1
    if has_p and not has_a:
        return 1
    return 0


def _normalize_era(era: Optional[str]) -> Optional[str]:
    if era is None:
        return None
    normalized = era.strip().upper()
    if normalized in {"AD", "A.D."}:
        return "AD"
    if normalized in {"BC", "B.C."}:
        return "BC"
    return None


def _century_bounds(century: int, era: Optional[str]) -> Optional[tuple[int, int]]:
    era = _normalize_era(era)
    if era is None or century < 1:
        return None
    start_year = (century - 1) * 100 + 1
    end_year = century * 100
    if era == "BC":
        start = 1 - end_year
        end = 1 - start_year
        return (start, end)
    return (start_year, end_year)


def _century_range_bounds(
    start_century: int,
    start_era: Optional[str],
    end_century: int,
    end_era: Optional[str],
) -> Optional[tuple[int, int]]:
    start_bounds = _century_bounds(start_century, start_era)
    end_bounds = _century_bounds(end_century, end_era)
    if start_bounds is None or end_bounds is None:
        return None
    return (min(start_bounds[0], end_bounds[0]), max(start_bounds[1], end_bounds[1]))


def _parse_tlg_date(raw: str) -> ParsedDate:
    """Parse TLG date strings into a century-based structured form."""
    raw = raw.strip()
    if raw in _SPECIAL_DATE_SORT_KEYS:
        return ParsedDate(
            raw=raw,
            start_century=None,
            start_era=None,
            end_century=None,
            end_era=None,
            start_qualifier=None,
            end_qualifier=None,
            uncertain=False,
            special=raw,
        )
    uncertain = "?" in raw
    normalized = raw.replace("/", "-")
    if "-" in normalized:
        start_raw, end_raw = normalized.split("-", maxsplit=1)
    else:
        start_raw = normalized
        end_raw = normalized
    start_century, start_era, start_qualifier = _parse_century_part(start_raw, None)
    end_century, end_era, end_qualifier = _parse_century_part(end_raw, start_era)
    if start_era is None and end_era is not None:
        start_century, start_era, start_qualifier = _parse_century_part(
            start_raw, end_era
        )
    if end_era is None and start_era is not None:
        end_century, end_era, end_qualifier = _parse_century_part(end_raw, start_era)
    return ParsedDate(
        raw=raw,
        start_century=start_century,
        start_era=start_era,
        end_century=end_century,
        end_era=end_era,
        start_qualifier=start_qualifier,
        end_qualifier=end_qualifier,
        uncertain=uncertain,
        special=None,
    )


def get_date_sort_key(
    date_value: Union[str, "ParsedDate"],
) -> tuple[int, int, int, int, str]:
    """Return a stable sort key for TLG date values."""
    parsed = _parse_tlg_date(date_value) if isinstance(date_value, str) else date_value
    if parsed.special:
        return _SPECIAL_DATE_SORT_KEYS[parsed.special]
    start_era = _normalize_era(parsed.start_era)
    end_era = _normalize_era(parsed.end_era) or start_era
    start_century = parsed.start_century
    end_century = (
        parsed.end_century if parsed.end_century is not None else start_century
    )
    if start_century is None or end_century is None:
        start_numeric = _DATE_SORT_SENTINEL
        end_numeric = _DATE_SORT_SENTINEL
    else:
        bounds = _century_range_bounds(start_century, start_era, end_century, end_era)
        if bounds is None:
            start_numeric = _DATE_SORT_SENTINEL
            end_numeric = _DATE_SORT_SENTINEL
        else:
            start_numeric, end_numeric = bounds
    qualifier_rank = _qualifier_rank(parsed)
    uncertain_rank = 1 if parsed.uncertain else 0
    return (
        start_numeric,
        end_numeric,
        qualifier_rank,
        uncertain_rank,
        parsed.raw or "",
    )


_PARSED_DATE_INDEX: dict[str, ParsedDate] = {
    raw: _parse_tlg_date(raw) for raw in MAP_DATE_TO_AUTHORS.keys()
}


def _ranges_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return max(start_a, start_b) <= min(end_a, end_b)


def get_dates_in_range(date_range: ParsedDate) -> list[str]:
    """Return date labels that overlap a parsed century range."""
    if date_range.special:
        return [date_range.special] if date_range.special in MAP_DATE_TO_AUTHORS else []
    if date_range.start_century is None:
        return []
    start_era = _normalize_era(date_range.start_era)
    end_era = _normalize_era(date_range.end_era) or start_era
    end_century = (
        date_range.end_century
        if date_range.end_century is not None
        else date_range.start_century
    )
    if end_century is None:
        return []
    query_bounds = _century_range_bounds(
        date_range.start_century, start_era, end_century, end_era
    )
    if query_bounds is None:
        return []
    query_start, query_end = query_bounds
    matches: list[str] = []
    for raw, parsed in _PARSED_DATE_INDEX.items():
        if parsed.special or parsed.start_century is None or parsed.end_century is None:
            continue
        parsed_end_era = parsed.end_era or parsed.start_era
        parsed_bounds = _century_range_bounds(
            parsed.start_century,
            parsed.start_era,
            parsed.end_century,
            parsed_end_era,
        )
        if parsed_bounds is None:
            continue
        if _ranges_overlap(query_start, query_end, parsed_bounds[0], parsed_bounds[1]):
            matches.append(raw)
    return sorted(matches, key=get_date_sort_key)
