"""
Tests for authentication system.

Thin aggregator that imports tests from split modules.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest

# NOTE:
# These tests were written for a standalone authentication implementation.
# The current architecture delegates **all real authentication** to
# mcp-proxy-adapter / mcp_security_framework. ``ClientAuthManager`` in
# ``embed_client.auth`` is now a thin configuration/headers helper.
# Direct authentication semantics are tested in the adapter/middleware
# project; here we only verify request shaping and high-level flows via
# EmbeddingServiceAsyncClient and adapter tests.
pytestmark = pytest.mark.skip(
    reason=(
        "Legacy direct-auth tests; authentication is handled by "
        "mcp-proxy-adapter/mcp_security_framework in production"
    )
)

# Import all test classes from split modules to maintain backward compatibility
from test_auth_manager import TestClientAuthManager  # noqa: F401, E402
from test_auth_helpers import (  # noqa: F401, E402
    TestAuthResult,
    TestAuthManagerFactory,
    TestAuthenticationError,
)
