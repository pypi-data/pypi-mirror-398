"""Example Python script for PHI5 utilities."""

from typing import Optional

from tlg_indices.data_types import AuthorID, WorkID
from tlg_indices.phi5_index_utils import (
    author_id_to_author_name,
    get_all_authors_ids,
    get_author_id_from_author_name,
    get_author_ids_from_work_id,
    get_author_name_from_author_id,
    get_author_names,
    get_author_works_index,
    get_works_by_author_id,
    get_works_by_author_name,
)


def main() -> None:
    all_authors: list[AuthorID] = get_all_authors_ids()
    print("All PHI5 author ids:", all_authors)

    author_names: list[str] = get_author_names()
    print("All PHI5 author names:", author_names)

    author_id_to_name = author_id_to_author_name()
    print("PHI5 author id-to-name mapping:", author_id_to_name)

    author_id: str = "0474"
    author_name: Optional[str] = get_author_name_from_author_id(author_id=author_id)
    print(f"Author name for id '{author_id}':", author_name)

    author_label = "Publius Ovidius Naso"
    ovid_id: Optional[AuthorID] = get_author_id_from_author_name(name=author_label)
    print(f"Author id for name '{author_label}':", ovid_id)

    author_works_index: dict[AuthorID, list[WorkID]] = get_author_works_index()
    print("Author works index:", author_works_index)

    works_by_id: list[WorkID] = get_works_by_author_id(author_id=author_id)
    print(f"Work ids for author '{author_id}':", works_by_id)

    works_by_name: list[WorkID] = get_works_by_author_name(name=author_label)
    print(f"Work ids for author name '{author_label}':", works_by_name)

    work_id: str = "001"
    authors_for_work: list[AuthorID] = get_author_ids_from_work_id(work_id=work_id)
    print(f"Author ids for work '{work_id}':", authors_for_work)


if __name__ == "__main__":
    main()
