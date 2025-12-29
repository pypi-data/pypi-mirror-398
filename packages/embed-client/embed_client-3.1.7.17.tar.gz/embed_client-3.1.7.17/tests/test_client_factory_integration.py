"""
ClientFactory integration tests.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from embed_client.client_factory import ClientFactory, SecurityMode


class TestIntegration:
    """Integration tests for client factory."""

    def test_security_mode_detection_comprehensive(self):
        """Test comprehensive security mode detection scenarios."""
        test_cases = [
            # (base_url, auth_method, ssl_enabled, cert_file, key_file, expected_mode)
            ("http://localhost", None, None, None, None, SecurityMode.HTTP),
            ("http://localhost", "api_key", None, None, None, SecurityMode.HTTP_TOKEN),
            ("https://localhost", None, None, None, None, SecurityMode.HTTPS),
            (
                "https://localhost",
                "api_key",
                None,
                None,
                None,
                SecurityMode.HTTPS_TOKEN,
            ),
            ("https://localhost", None, None, "cert.pem", "key.pem", SecurityMode.MTLS),
            (
                "https://localhost",
                None,
                None,
                "cert.pem",
                "key.pem",
                SecurityMode.MTLS_ROLES,
                {"roles": ["admin"]},
            ),
            ("http://localhost", None, True, None, None, SecurityMode.HTTPS),
            ("https://localhost", None, False, None, None, SecurityMode.HTTP),
        ]

        for case in test_cases:
            if len(case) == 6:
                (
                    base_url,
                    auth_method,
                    ssl_enabled,
                    cert_file,
                    key_file,
                    expected_mode,
                ) = case
                kwargs = {}
            else:
                (
                    base_url,
                    auth_method,
                    ssl_enabled,
                    cert_file,
                    key_file,
                    expected_mode,
                    kwargs,
                ) = case

            mode = ClientFactory.detect_security_mode(
                base_url, auth_method, ssl_enabled, cert_file, key_file, **kwargs
            )
            assert mode == expected_mode, f"Failed for case: {case}"

    def test_config_creation_comprehensive(self):
        """Test comprehensive configuration creation."""
        # Test HTTP config
        config = ClientFactory._create_config_for_mode(
            SecurityMode.HTTP, "http://localhost", 8001, None, False
        )
        assert config["server"]["host"] == "http://localhost"
        assert config["server"]["port"] == 8001
        assert "auth" not in config
        assert "ssl" not in config

        # Test HTTPS + Token config
        config = ClientFactory._create_config_for_mode(
            SecurityMode.HTTPS_TOKEN,
            "https://localhost",
            8001,
            "api_key",
            True,
            api_key="test_key",
            ca_cert_file="ca.pem",
        )
        assert config["server"]["host"] == "https://localhost"
        assert config["server"]["port"] == 8001
        assert config["auth"]["method"] == "api_key"
        assert config["auth"]["api_keys"]["user"] == "test_key"
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["ca_cert_file"] == "ca.pem"

        # Test mTLS config
        config = ClientFactory._create_config_for_mode(
            SecurityMode.MTLS,
            "https://localhost",
            8001,
            None,
            True,
            cert_file="cert.pem",
            key_file="key.pem",
            ca_cert_file="ca.pem",
        )
        assert config["server"]["host"] == "https://localhost"
        assert config["server"]["port"] == 8001
        assert "auth" not in config
        assert config["ssl"]["enabled"] is True
        assert config["ssl"]["cert_file"] == "cert.pem"
        assert config["ssl"]["key_file"] == "key.pem"
        assert config["ssl"]["ca_cert_file"] == "ca.pem"
