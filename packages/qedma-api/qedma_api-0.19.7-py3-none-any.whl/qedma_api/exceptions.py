"""
Qedma-api Exceptions
"""


class APITokenNotFound(Exception):
    """Token not found locally and not passed to client"""

    def __init__(self) -> None:
        super().__init__("No api token given and no stored one found")
