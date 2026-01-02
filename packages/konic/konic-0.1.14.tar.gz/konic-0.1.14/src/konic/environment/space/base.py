from abc import ABC

from pydantic import BaseModel


class BaseKonicSpace(ABC, BaseModel):
    """Abstract base class for Konic spaces that defines the common interface and shared utilities for concrete space implementations"""

    pass
