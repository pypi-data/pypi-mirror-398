"""Higher-level (i.e., user-friendly) functions for quickly reading
PHI5 data after it has been processed by ``TLGU()``.
"""

from typing import Optional, Union

from tlg_indices.data_types import AuthorID, WorkID
from tlg_indices.indices.phi5_author_id_to_name import MAP_PHI5_AUTHOR_ID_TO_NAME
from tlg_indices.indices.phi5_author_id_to_works import MAP_PHI5_AUTHOR_ID_TO_WORKS


_AUTHOR_NAME_INDEX_CASEFOLD: dict[str, AuthorID] = {
    name.casefold(): author_id for author_id, name in MAP_PHI5_AUTHOR_ID_TO_NAME.items()
}
_WORK_ID_TO_AUTHOR_IDS: dict[WorkID, list[AuthorID]] = {}
for author_id, work_ids in MAP_PHI5_AUTHOR_ID_TO_WORKS.items():
    for work_id in work_ids:
        _WORK_ID_TO_AUTHOR_IDS.setdefault(work_id, []).append(author_id)
for work_id, author_ids in _WORK_ID_TO_AUTHOR_IDS.items():
    author_ids.sort()


def get_all_authors_ids() -> list[AuthorID]:
    """Open PHI5 author ids index and return sorted list of author ids."""
    return sorted(MAP_PHI5_AUTHOR_ID_TO_NAME.keys())


def get_author_names() -> list[str]:
    """Return a list of all PHI5 author labels."""
    return sorted(MAP_PHI5_AUTHOR_ID_TO_NAME.values())


def author_id_to_author_name() -> dict[AuthorID, str]:
    """Return entirety of PHI5 id-author index."""
    return MAP_PHI5_AUTHOR_ID_TO_NAME


def get_author_name_from_author_id(author_id: Union[AuthorID, str]) -> Optional[str]:
    """Pass PHI5 author id and return the author label."""
    return MAP_PHI5_AUTHOR_ID_TO_NAME.get(AuthorID(author_id))


def get_author_id_from_author_name(name: str) -> Optional[AuthorID]:
    """Pass PHI5 author name and return the author id."""
    return _AUTHOR_NAME_INDEX_CASEFOLD.get(name.casefold())


def get_author_works_index() -> dict[AuthorID, list[WorkID]]:
    """Return entirety of PHI5 author-to-work index."""
    return MAP_PHI5_AUTHOR_ID_TO_WORKS


def get_works_by_author_id(author_id: Union[AuthorID, str]) -> list[WorkID]:
    """Pass PHI5 author id and return a list of work ids."""
    return MAP_PHI5_AUTHOR_ID_TO_WORKS[AuthorID(author_id)]


def get_works_by_author_name(name: str) -> list[WorkID]:
    """Pass PHI5 author name and return a list of work ids."""
    author_id = get_author_id_from_author_name(name)
    if author_id is None:
        return list()
    return MAP_PHI5_AUTHOR_ID_TO_WORKS.get(author_id, list())


def get_author_ids_from_work_id(work_id: Union[WorkID, str]) -> list[AuthorID]:
    """Pass PHI5 work id and return ordered list of author ids."""
    ids = _WORK_ID_TO_AUTHOR_IDS.get(WorkID(work_id))
    if ids is None:
        return list()
    return list(ids)


# from cltk.utils.file_operations import make_cltk_path


# def assemble_phi5_author_filepaths() -> list[str]:
#     """Reads PHI5 index and builds a list of absolute filepaths."""
#     plaintext_dir: str = make_cltk_path("lat/text/phi5/plaintext/")
#     filepaths: list[str] = [
#         os.path.join(plaintext_dir, x + ".TXT") for x in MAP_PHI5_AUTHOR_ID_TO_NAME
#     ]
#     return filepaths


# def assemble_phi5_works_filepaths() -> list[str]:
#     """Reads PHI5 index and builds a list of absolute filepaths."""
#     plaintext_dir: str = make_cltk_path("lat/text/phi5/individual_works/")
#     all_filepaths: list[str] = list()
#     for author_code in MAP_PHI5_AUTHOR_ID_TO_WORKS_AND_NAME:
#         author_data: dict[str, Union[list[str], str]] = (
#             MAP_PHI5_AUTHOR_ID_TO_WORKS_AND_NAME[author_code]
#         )
#         works: Union[list[str], str] = author_data["works"]
#         for work in works:
#             filepath: str = os.path.join(
#                 plaintext_dir, author_code + ".TXT" + "-" + work + ".txt"
#             )
#             all_filepaths.append(filepath)
#     return all_filepaths
