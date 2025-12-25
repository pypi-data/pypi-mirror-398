"""Sonnerrise Promo - Track promotion materials management module."""

from sonnerrise_promo.models import Promo, PromoLink
from sonnerrise_promo.repository import (
    PromoExistsError,
    PromoNotFoundError,
    PromoRepository,
)
from sonnerrise_promo.schemas import (
    PromoCreate,
    PromoFilter,
    PromoLinkCreate,
    PromoLinkRead,
    PromoList,
    PromoListItem,
    PromoRead,
    PromoUpdate,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "Promo",
    "PromoLink",
    # Repository
    "PromoRepository",
    "PromoNotFoundError",
    "PromoExistsError",
    # Schemas
    "PromoCreate",
    "PromoFilter",
    "PromoLinkCreate",
    "PromoLinkRead",
    "PromoList",
    "PromoListItem",
    "PromoRead",
    "PromoUpdate",
    # Version
    "__version__",
]
