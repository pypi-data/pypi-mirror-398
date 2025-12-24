"""Django Service Views - Class-based views for service layer pattern"""

__version__ = "0.1.0"

from .views import (
    ServiceCreateView,
    ServiceDeleteView,
    ServiceModelFormMixin,
    ServiceUpdateView,
)

__all__ = [
    "ServiceModelFormMixin",
    "ServiceUpdateView",
    "ServiceCreateView",
    "ServiceDeleteView",
]
