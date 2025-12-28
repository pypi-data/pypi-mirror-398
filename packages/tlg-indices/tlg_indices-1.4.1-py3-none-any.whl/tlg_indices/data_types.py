"""Data types for defining author and work ids."""

from typing import NewType

AuthorID = NewType("AuthorID", str)

WorkID = NewType("WorkID", str)
