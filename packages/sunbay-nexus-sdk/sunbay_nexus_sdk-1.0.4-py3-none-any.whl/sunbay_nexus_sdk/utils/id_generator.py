"""
Request ID generator.

Provides a simple utility to generate unique client request identifiers,
similar to the Java IdGenerator.
"""

import uuid


def generate_request_id() -> str:
    """
    Generate a unique request id.

    The format is a UUID4 string without dashes, which is concise and
    sufficiently unique for client-side request tracking.
    """
    return uuid.uuid4().hex


