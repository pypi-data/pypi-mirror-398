# TODO: Check these

import re
from re import Pattern
from typing import Optional


def tlg_plaintext_cleanup(
    text: str, rm_punctuation: bool = False, rm_periods: bool = False
) -> str:
    """Remove and substitute post-processing for Greek TLG text."""
    # Note: flag was removed, is necessary?
    # remove_comp: Pattern[str] = re.compile(
    #     r"-\n|[«»<>〈〉\(\)‘’_—:!\?\'\"\*]|{[^}]*}|\[[[:print:][:space:]]+?\]|[a-zA-Z0-9]",
    # )
    remove_comp: Pattern[str] = re.compile(
        r"-\n"  # hyphen + newline
        r"|[«»<>〈〉()‘’_—:!?\'\"*]"  # punctuation/symbols
        r"|{[^}]*}"  # {...}
        r"|\[[^\]]+?\]"  # [...]  (anything except ])
        r"|[A-Za-z0-9]"  # ASCII alphanumerics
    )
    text = remove_comp.sub("", text)

    if rm_punctuation:
        punct_comp: Pattern[str] = re.compile(r",|·")
        text = punct_comp.sub("", text)

    if rm_periods:
        period_comp: Pattern[str] = re.compile(r"\.|;")
        text = period_comp.sub("", text)

    # replace line breaks w/ space
    replace_comp: Pattern[str] = re.compile(r"\n")
    text = replace_comp.sub(" ", text)

    comp_space: Pattern[str] = re.compile(r"\s+")
    text = comp_space.sub(" ", text)

    return text


def phi5_plaintext_cleanup(
    text, rm_punctuation: bool = False, rm_periods: bool = False
) -> str:
    """Remove and substitute post-processing for Latin PHI5 text.
    TODO: Surely more junk to pull out. Please submit bugs!
    TODO: This is a rather slow now, help in speeding up welcome.
    """
    # This works OK, but misses some
    # Note: Removing all characters between {} and ()
    remove_comp: Pattern[str] = re.compile(
        r"-\n|«|»|\<|\>|\.\.\.|‘|’|_|{.+?}|\(.+?\)|\(|\)|“|#|%|⚔|&|=|/|\\|〚|†|『|⚖|–|˘|⚕|☾|◌|◄|►|⌐|⌊|⌋|≈|∷|≈|∞|”|[0-9]"
    )
    text = remove_comp.sub("", text)

    new_text: Optional[str] = None
    if rm_punctuation:
        new_text = ""
        punctuation: list[str] = [
            ",",
            ";",
            ":",
            '"',
            "'",
            "?",
            "-",
            "!",
            "*",
            "[",
            "]",
            "{",
            "}",
        ]
        if rm_periods:
            punctuation += ["."]
        for char in text:
            # rm acute combining acute accents made by TLGU
            # Could be caught by regex, tried and failed, not sure why
            if bytes(char, "utf-8") == b"\xcc\x81":
                pass
            # second try at rming some punctuation; merge with above regex
            elif char in punctuation:
                pass
            else:
                new_text += char
    if new_text:
        text = new_text

    # replace line breaks w/ space
    replace_comp: Pattern[str] = re.compile(r"\n")
    text = replace_comp.sub(" ", text)

    comp_space: Pattern[str] = re.compile(r"\s+")
    text = comp_space.sub(" ", text)

    return text
