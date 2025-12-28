"""Wrapper for `tlgu` command line utility.

TLGU software written by Dimitri Marinakis and available at
<http://tlgu.carmen.gr/> under GPLv2 license.
"""

import os
from pathlib import Path
import subprocess
from types import UnionType
from typing import Literal, Optional

# # TLGU args
# ARGS: dict[str, str] = {
#     "book_breaks": "-b",
#     "page_breaks": "-p",
#     "lat_text": "-r",
#     "level_1": "-v",
#     "level_2": "-w",
#     "level_3": "-x",
#     "level_4": "-y",
#     "level_5": "-z",
#     "line_tab": "-B",
#     "higher_levels": "-X",
#     "lower_levels": "-Y",
#     "no_spaces": "-N",  # rm_newlines
#     "citation_debug": "-C",
#     "code_debug": "-S",
#     "verbose": "-V",
#     "split_works": "-W",
# }

corpusTypes = Literal["tlg", "phi5", "phi7"]
groupingTypes = Literal["author", "work"]


def tlgu_convert_file(
    orig_txt_path: str,
    target_txt_path: str,
    corpus: corpusTypes,
    grouping: groupingTypes,
) -> None:
    """Call `tlgu` to convert a single file."""
    orig_path = Path(orig_txt_path).expanduser()
    target_path = Path(target_txt_path).expanduser()
    if not orig_path.exists():
        raise FileNotFoundError(f"File '{orig_path}' does not exist.")
    target_name = target_path.name
    # Skip index files in TLG
    if target_name.startswith("DOCCAN"):
        print("Skipping 'DOCCAN*' file:", orig_path)
        return None
    # Skip these files in PHI5
    if (
        target_name.startswith("AUTHTAB")
        or target_name.startswith("CIV")
        or target_name.startswith("COP")
        or target_name.startswith("IND")
    ):
        print("Skipping non-text PHI5 file:", orig_path)
        return None
    if target_name.lower().startswith("tlg"):
        target_name = target_name[3:]
    if target_name.lower().startswith("lat"):  # for phi5
        target_name = target_name[3:]
    if target_name.endswith(".TXT"):
        target_name = f"{target_name[:-4]}.txt"
    if grouping == "work":
        target_name = target_name.rstrip(".txt")
    target_path = target_path.with_name(target_name)
    tlgu_call: str
    grouping_flag: str
    if grouping == "author":
        grouping_flag = "-N"
    elif grouping == "work":
        grouping_flag = "-W"
    else:
        raise ValueError(f"Invalid grouping '{grouping}'.")
    if corpus == "tlg":
        tlgu_call = f"tlgu {grouping_flag} {orig_path} {target_path}"
    elif corpus == "phi5":
        # "-r" flag for Latin text
        tlgu_call = f"tlgu -r {grouping_flag} {orig_path} {target_path}"
    # elif corpus == "phi7":
    #     tlgu_call = f"tlgu {grouping_flag} {orig_path} {target_path}"
    else:
        raise ValueError(f"Invalid corpus '{corpus}'.")
    print("Going to call tlgu with:", tlgu_call)
    try:
        subprocess.run(tlgu_call, shell=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"tlgu failed with exit code {exc.returncode}. The likely cause is that `tlgu` is not installed. To install, follow instructions at <https://github.com/cltk/grc_software_tlgu>."
        ) from exc
    if grouping == "author":
        if not target_path.exists():
            raise FileNotFoundError(f"Failed to create file: {target_path}")
    else:
        work_glob = f"{target_path.stem}-*.txt"
        if not any(target_path.parent.glob(work_glob)):
            raise FileNotFoundError(
                f"Failed to create work files matching: {target_path.parent / work_glob}"
            )
    return None


def tlgu_convert_corpus(
    orig_txt_dir: str,
    target_txt_dir: str,
    corpus: corpusTypes,
    grouping: groupingTypes,
) -> None:
    """Convert an entire TLG, PHI5 or PHI7 corpus."""
    orig_txt_dir = os.path.expanduser(orig_txt_dir)
    target_txt_dir = os.path.expanduser(target_txt_dir)
    if not os.path.exists(orig_txt_dir):
        raise FileNotFoundError(f"Directory '{orig_txt_dir}' does not exist.")
    if not os.path.exists(target_txt_dir):
        os.makedirs(target_txt_dir)
    for orig_txt_file in sorted(os.listdir(orig_txt_dir)):
        if orig_txt_file.endswith("TXT"):
            orig_txt_path: str = os.path.join(orig_txt_dir, orig_txt_file)
            target_txt_path: str = os.path.join(target_txt_dir, orig_txt_file)
            tlgu_convert_file(
                orig_txt_path=orig_txt_path,
                target_txt_path=target_txt_path,
                corpus=corpus,
                grouping=grouping,
            )
    return None
