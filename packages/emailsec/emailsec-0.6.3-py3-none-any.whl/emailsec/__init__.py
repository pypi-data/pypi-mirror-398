"""
.. include:: ../../README.md
   :start-line: 1
"""

from .auth import AuthenticationResult as AuthenticationResult
from .auth import DeliveryAction as DeliveryAction
from .auth import SMTPContext as SMTPContext
from .auth import authenticate_message as authenticate_message
from .config import AuthenticationConfiguration as AuthenticationConfiguration
from ._utils import BodyAndHeaders as BodyAndHeaders
from ._utils import Body as Body
from ._utils import Header as Header
from ._utils import Headers as Headers
from ._utils import (
    body_and_headers_for_canonicalization as body_and_headers_for_canonicalization,
)
from ._alignment import AlignmentMode as AlignmentMode
