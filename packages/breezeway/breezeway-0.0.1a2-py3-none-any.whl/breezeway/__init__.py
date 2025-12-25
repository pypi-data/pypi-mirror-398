from .breezeway_client import BreezewayClient, AsyncBreezewayClient
from .models.company import Department
from .models.unit import Unit, UnitNotes
from .models.user import User

__all__ = [
    # Clients
    'BreezewayClient', 'AsyncBreezewayClient',

    # Company
    'Department',

    # People
    'User',

    # Property
    'Unit',
    "UnitNotes",
]

# Package metadata
__author__ = 'Anthony DeGarimore'
__email__ = 'Anthony@DeGarimore.com'
__licence__ = 'MIT'