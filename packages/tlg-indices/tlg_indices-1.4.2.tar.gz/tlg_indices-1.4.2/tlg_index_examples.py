"""Example Python script for tlg_indices."""

from typing import Optional
from tlg_indices.data_types import AuthorID, WorkID
from tlg_indices.tlg_index_utils import (
    ParsedDate,
    author_id_to_author_name,
    get_all_authors_ids,
    get_author_id_from_author_name,
    get_author_name_from_author_id,
    get_author_works_index,
    get_date_author,
    get_date_of_author,
    get_dates_in_range,
    get_dates,
    get_date_sort_key,
    get_work_name,
    get_epithet_of_author,
    get_female_authors,
    get_epithet_index,
    get_epithets,
    get_geo_index,
    get_geo_of_author,
    get_geographies,
    get_authors_by_epithet,
    get_authors_by_geo,
    author_id_to_author_name,
    get_indices,
)


def main() -> None:
    all_authors: list[AuthorID] = get_all_authors_ids()
    print("All authors:", all_authors)

    female_authors: list[AuthorID] = get_female_authors()
    print("Female authors:", female_authors)

    epithets: list[str] = get_epithets()
    print("Epithets:", epithets)

    epithet_index: dict[str, list[AuthorID]] = get_epithet_index()
    print("Epithet index:", epithet_index)

    epithet: str = "Poetae Medici"
    authors: list[AuthorID] = get_authors_by_epithet(epithet=epithet)
    print(f"Authors with epithet '{epithet}':", authors)

    author_id: str = "9020"
    epithet_of_author: Optional[str] = get_epithet_of_author(author_id=author_id)
    print(f"Epithet of author '{author_id}':", epithet_of_author)

    geo_index: dict[str, list[AuthorID]] = get_geo_index()
    print("Geo index:", geo_index)

    geographies: list[str] = get_geographies()
    print("Geographies:", geographies)

    geo: str = "Olynthos [vel Olynthus]"
    geo_authors: list[AuthorID] = get_authors_by_geo(geo=geo)
    print(f"Authors from geography '{geo}':", geo_authors)

    geo_of_author: Optional[str] = get_geo_of_author(author_id=author_id)
    print(f"Geography of author '{author_id}':", geo_of_author)

    indices: dict[str, dict[str, str]] = get_indices()
    print("Indices:", indices)

    author_id_to_name = author_id_to_author_name()
    print("Author ID to name mapping:", author_id_to_name)

    author_name: Optional[str] = get_author_name_from_author_id(author_id=author_id)
    print(f"Author name for ID '{author_id}':", author_name)

    author_name = "Aristoteles Phil. et Corpus Aristotelicum, Aristotle"
    another_author_id: Optional[AuthorID] = get_author_id_from_author_name(
        name=author_name
    )
    print(f"Author ID for name '{author_name}':", another_author_id)

    author_id_works_index: dict[AuthorID, dict[WorkID, str]] = get_author_works_index()
    print("Author works index:", author_id_works_index)

    work_id: str = "001"
    work_name: Optional[str] = get_work_name(author_id=author_id, work_id=work_id)
    print(f"Work name for author '{author_id}' and work '{work_id}':", work_name)

    date_author_index: dict[str, list[AuthorID]] = get_date_author()
    print("Date author index:", date_author_index)

    dates: list[str] = get_dates()
    print("Dates:", dates)

    some_author_id: str = "0007"
    date: Optional[str] = get_date_of_author(author_id=some_author_id)
    print(f"Date of author '{some_author_id}':", date)

    sorted_dates = sorted(dates, key=get_date_sort_key)
    print("Sorted dates:", sorted_dates)

    ad_range = ParsedDate(
        raw=None,
        start_century=1,
        start_era="A.D.",
        end_century=4,
        end_era="A.D.",
        start_qualifier=None,
        end_qualifier=None,
        uncertain=False,
        special=None,
    )
    print("Dates in A.D. 1-4 range:", get_dates_in_range(ad_range))

    bc_range = ParsedDate(
        raw=None,
        start_century=4,
        start_era="B.C.",
        end_century=2,
        end_era="B.C.",
        start_qualifier=None,
        end_qualifier=None,
        uncertain=False,
        special=None,
    )
    print("Dates in 4-2 B.C. range:", get_dates_in_range(bc_range))

    cross_range = ParsedDate(
        raw=None,
        start_century=1,
        start_era="B.C.",
        end_century=1,
        end_era="A.D.",
        start_qualifier=None,
        end_qualifier=None,
        uncertain=False,
        special=None,
    )
    print("Dates across B.C./A.D. boundary:", get_dates_in_range(cross_range))

    ante_range = ParsedDate(
        raw=None,
        start_century=2,
        start_era="A.D.",
        end_century=2,
        end_era="A.D.",
        start_qualifier="a",
        end_qualifier=None,
        uncertain=False,
        special=None,
    )
    print("Dates in a. A.D. 2 range:", get_dates_in_range(ante_range))

    special_range = ParsedDate(
        raw=None,
        start_century=None,
        start_era=None,
        end_century=None,
        end_era=None,
        start_qualifier=None,
        end_qualifier=None,
        uncertain=False,
        special="Incertum",
    )
    print("Special date range (Incertum):", get_dates_in_range(special_range))


if __name__ == "__main__":
    main()
