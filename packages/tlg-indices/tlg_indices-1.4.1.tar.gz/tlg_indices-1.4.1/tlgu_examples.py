"""Examples how to convert files using `tlgu`."""

from tlg_indices.tlgu import tlgu_convert_corpus, tlgu_convert_file


def main() -> None:
    # Convert a single TLG file into author file
    tlgu_convert_file(
        orig_txt_path="~/tlg/TLG_E/TLG0007.TXT",
        target_txt_path="~/Downloads/0007.txt",
        corpus="tlg",
        grouping="author",
    )

    # Convert a single TLG file into works files
    tlgu_convert_file(
        orig_txt_path="~/tlg/TLG_E/TLG0007.TXT",
        target_txt_path="~/Downloads/0007",
        corpus="tlg",
        grouping="work",
    )

    # Convert entire TLG corpus into author files
    tlgu_convert_corpus(
        orig_txt_dir="~/tlg/TLG_E",
        target_txt_dir="~/Downloads/tlg-authors",
        corpus="tlg",
        grouping="author",
    )

    # Convert entire TLG corpus into work files
    tlgu_convert_corpus(
        orig_txt_dir="~/tlg/TLG_E",
        target_txt_dir="~/Downloads/tlg-works",
        corpus="tlg",
        grouping="work",
    )

    # Convert a single PHI5 file into author file
    tlgu_convert_file(
        orig_txt_path="~/tlg/PHI5/LAT1254.TXT",
        target_txt_path="~/Downloads/1254.txt",
        corpus="phi5",
        grouping="author",
    )

    # Convert a single PHI5 file into works files
    tlgu_convert_file(
        orig_txt_path="~/tlg/PHI5/LAT1254.TXT",
        target_txt_path="~/Downloads/1254",
        corpus="phi5",
        grouping="work",
    )

    # Convert entire PHI5 corpus into author files
    tlgu_convert_corpus(
        orig_txt_dir="~/tlg/PHI5",
        target_txt_dir="~/Downloads/phi5-authors",
        corpus="phi5",
        grouping="author",
    )

    # Convert entire PHI5 corpus into work files
    tlgu_convert_corpus(
        orig_txt_dir="~/tlg/PHI5",
        target_txt_dir="~/Downloads/phi5-works",
        corpus="phi5",
        grouping="work",
    )


if __name__ == "__main__":
    main()
