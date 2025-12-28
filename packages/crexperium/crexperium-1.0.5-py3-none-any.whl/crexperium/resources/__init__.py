"""Resource modules for Crexperium SDK."""

from .base import BaseResource
from .contacts import ContactsResource
from .deals import DealsResource
from .activities import ActivitiesResource
from .events import EventsResource

__all__ = [
    "BaseResource",
    "ContactsResource",
    "DealsResource",
    "ActivitiesResource",
    "EventsResource",
]
