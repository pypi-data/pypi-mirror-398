"""Resource clients for Vaulty API."""

from .activities import ActivityResource
from .customers import CustomerResource
from .health import HealthResource
from .projects import ProjectResource
from .secrets import SecretResource
from .tokens import TokenResource

__all__ = [
    "ActivityResource",
    "CustomerResource",
    "HealthResource",
    "ProjectResource",
    "SecretResource",
    "TokenResource",
]
