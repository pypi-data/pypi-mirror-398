from tlg_indices.file_utils import (
    assemble_phi5_author_filepaths,
    assemble_phi5_works_filepaths,
    assemble_phi5_works_filepaths_for_author,
    assemble_tlg_author_filepaths,
    assemble_tlg_works_filepaths,
    assemble_tlg_works_filepaths_for_author,
)


def main() -> None:
    # TLG
    tlg_author_filepaths: list[str] = assemble_tlg_author_filepaths(
        corpus_dir="~/Downloads/tlg-authors/"
    )
    print("TLG filepaths:", tlg_author_filepaths)

    tlg_works_filepaths: list[str] = assemble_tlg_works_filepaths(
        corpus_dir="~/Downloads/tlg-works/"
    )
    print("TLG works filepaths:", tlg_works_filepaths)

    tlg_author_works: list[str] = assemble_tlg_works_filepaths_for_author(
        corpus_dir="~/Downloads/tlg-works/",
        author_id="0007",
    )
    print("TLG works for author 0007:", tlg_author_works)

    tlg_single_work: list[str] = assemble_tlg_works_filepaths_for_author(
        corpus_dir="~/Downloads/tlg-works/",
        author_id="0007",
        work_id="001",
    )
    print("TLG work 001 for author 0007:", tlg_single_work)

    # PHI5
    phi_author_filepaths: list[str] = assemble_phi5_author_filepaths(
        corpus_dir="~/Downloads/phi5-authors/"
    )
    print("PHI5 filepaths:", phi_author_filepaths)

    phi_works_filepaths: list[str] = assemble_phi5_works_filepaths(
        corpus_dir="~/Downloads/phi5-works/"
    )
    print("PHI5 works filepaths:", phi_works_filepaths)

    phi5_author_works: list[str] = assemble_phi5_works_filepaths_for_author(
        corpus_dir="~/Downloads/phi5-works/",
        author_id="1254",
    )
    print("PHI5 works for author 1254:", phi5_author_works)

    phi5_single_work: list[str] = assemble_phi5_works_filepaths_for_author(
        corpus_dir="~/Downloads/phi5-works/",
        author_id="1254",
        work_id="001",
    )
    print("PHI5 work 001 for author 1254:", phi5_single_work)


if __name__ == "__main__":
    main()
