"""
Usage documentation module.

Centralizes all usage texts for easy maintenance.
"""

from finter.data.content_model.usage.contentfactory import (
    CONTENTFACTORY_GENERAL_USAGE_TEXT,
    get_standard_item_usage,
)
from finter.data.content_model.usage.quarters import QUARTERS_USAGE_TEXT

__all__ = [
    "CONTENTFACTORY_GENERAL_USAGE_TEXT",
    "get_standard_item_usage",
    "QUARTERS_USAGE_TEXT",
]
