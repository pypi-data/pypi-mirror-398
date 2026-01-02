"""
Tests for value-aware security header classification.

This module tests the intelligent severity classification that analyzes
header VALUES to determine if dropping them is a security concern.

The key insight:
- Cache-Control: no-store → MEDIUM (security-protective)
- Cache-Control: public   → LOW (just performance optimization)

This is smarter than blindly adding all cache headers to a "secure" list.
"""

import pytest

from gixy.plugins.add_header_redefinition import (
    CONDITIONAL_SECURITY_HEADERS,
    add_header_redefinition,
    is_security_protective_value,
)


class TestSecurityProtectiveValue:
    """Test the is_security_protective_value function directly."""

    # =========================================================================
    # Cache-Control tests
    # =========================================================================

    def test_cache_control_no_store_is_protective(self):
        """Cache-Control: no-store prevents caching - security protective."""
        assert is_security_protective_value("cache-control", ["no-store"]) is True

    def test_cache_control_no_cache_is_protective(self):
        """Cache-Control: no-cache requires revalidation - security protective."""
        assert is_security_protective_value("cache-control", ["no-cache"]) is True

    def test_cache_control_private_is_protective(self):
        """Cache-Control: private prevents proxy caching - security protective."""
        assert is_security_protective_value("cache-control", ["private"]) is True

    def test_cache_control_must_revalidate_is_protective(self):
        """Cache-Control: must-revalidate - security protective."""
        assert (
            is_security_protective_value("cache-control", ["must-revalidate"]) is True
        )

    def test_cache_control_combined_directive_is_protective(self):
        """Combined directives like 'private, no-cache, no-store' are protective."""
        assert (
            is_security_protective_value(
                "cache-control", ["private, no-cache, no-store"]
            )
            is True
        )

    def test_cache_control_public_is_not_protective(self):
        """Cache-Control: public is just caching optimization - NOT security."""
        assert is_security_protective_value("cache-control", ["public"]) is False

    def test_cache_control_max_age_is_not_protective(self):
        """Cache-Control: max-age=3600 is just caching optimization - NOT security."""
        assert is_security_protective_value("cache-control", ["max-age=3600"]) is False

    def test_cache_control_public_max_age_is_not_protective(self):
        """Cache-Control: public, max-age=86400 is just optimization - NOT security."""
        assert (
            is_security_protective_value("cache-control", ["public, max-age=86400"])
            is False
        )

    def test_cache_control_case_insensitive(self):
        """Header value matching should be case-insensitive."""
        assert is_security_protective_value("cache-control", ["NO-STORE"]) is True
        assert is_security_protective_value("Cache-Control", ["Private"]) is True

    # =========================================================================
    # Pragma tests
    # =========================================================================

    def test_pragma_no_cache_is_protective(self):
        """Pragma: no-cache is security protective."""
        assert is_security_protective_value("pragma", ["no-cache"]) is True

    def test_pragma_other_is_not_protective(self):
        """Other Pragma values are not security protective."""
        assert is_security_protective_value("pragma", ["some-other-value"]) is False

    # =========================================================================
    # Expires tests
    # =========================================================================

    def test_expires_zero_is_protective(self):
        """Expires: 0 means already expired - security protective."""
        assert is_security_protective_value("expires", ["0"]) is True

    def test_expires_negative_is_protective(self):
        """Expires: -1 means already expired - security protective."""
        assert is_security_protective_value("expires", ["-1"]) is True

    def test_expires_epoch_is_protective(self):
        """Expires: Thu, 01 Jan 1970 ... is epoch - security protective."""
        assert (
            is_security_protective_value("expires", ["Thu, 01 Jan 1970 00:00:00 GMT"])
            is True
        )

    def test_expires_future_is_not_protective(self):
        """Expires: <future date> is just caching - NOT security."""
        assert (
            is_security_protective_value("expires", ["Thu, 01 Jan 2030 00:00:00 GMT"])
            is False
        )

    # =========================================================================
    # Content-Disposition tests
    # =========================================================================

    def test_content_disposition_attachment_is_protective(self):
        """Content-Disposition: attachment prevents inline execution - security."""
        assert (
            is_security_protective_value("content-disposition", ["attachment"]) is True
        )

    def test_content_disposition_attachment_with_filename_is_protective(self):
        """Content-Disposition: attachment; filename=x.pdf is security protective."""
        assert (
            is_security_protective_value(
                "content-disposition", ['attachment; filename="file.pdf"']
            )
            is True
        )

    def test_content_disposition_inline_is_not_protective(self):
        """Content-Disposition: inline is NOT security protective."""
        assert is_security_protective_value("content-disposition", ["inline"]) is False

    # =========================================================================
    # X-Download-Options tests
    # =========================================================================

    def test_x_download_options_noopen_is_protective(self):
        """X-Download-Options: noopen prevents auto-execution in IE."""
        assert is_security_protective_value("x-download-options", ["noopen"]) is True

    # =========================================================================
    # Unknown headers
    # =========================================================================

    def test_unknown_header_is_not_protective(self):
        """Unknown headers are not classified as security protective."""
        assert is_security_protective_value("x-custom-header", ["anything"]) is False


class TestPluginSeverityClassification:
    """Integration tests for the plugin's severity classification."""

    @pytest.fixture
    def plugin(self):
        """Create a plugin instance with default config."""
        return add_header_redefinition({})

    def test_always_secure_headers(self, plugin):
        """Test that core security headers are always classified as secure."""
        always_secure = [
            "content-security-policy",
            "strict-transport-security",
            "x-frame-options",
            "x-content-type-options",
            "referrer-policy",
            "permissions-policy",
            "cross-origin-embedder-policy",
            "cross-origin-opener-policy",
            "cross-origin-resource-policy",
        ]
        for header in always_secure:
            assert (
                header in plugin.always_secure_headers
            ), f"{header} should be in always_secure_headers"

    def test_conditional_headers_defined(self):
        """Test that conditional security headers are properly defined."""
        expected_conditional = [
            "cache-control",
            "pragma",
            "expires",
            "content-disposition",
            "x-download-options",
        ]
        for header in expected_conditional:
            assert (
                header in CONDITIONAL_SECURITY_HEADERS
            ), f"{header} should be in CONDITIONAL_SECURITY_HEADERS"


class TestMegaManSecScenario:
    """
    Test the exact scenario MegaManSec described.

    This proves our solution correctly handles his use case:
    - Parent: Cache-Control: no-store
    - Child adds different header, dropping Cache-Control
    - Should be MEDIUM severity (his point was valid!)

    BUT ALSO:
    - Parent: Cache-Control: public, max-age=3600
    - Child adds different header, dropping Cache-Control
    - Should be LOW severity (our improvement!)
    """

    def test_megamansec_scenario_no_store_is_medium(self):
        """
        MegaManSec's exact example should trigger MEDIUM severity.

        http {
            server {
                add_header Cache-Control "no-store";
                location /private_information/ {
                    add_header X-Frame-Options "DENY";
                    # Cache-Control is DROPPED - this is bad!
                }
            }
        }
        """
        # no-store being dropped IS a security issue
        assert is_security_protective_value("cache-control", ["no-store"]) is True

    def test_our_improvement_public_is_low(self):
        """
        Our improvement: public cache control dropped is NOT security issue.

        http {
            server {
                add_header Cache-Control "public, max-age=3600";
                location /dynamic/ {
                    add_header Cache-Control "no-store";
                    # Parent's public cache is "dropped" but that's fine!
                }
            }
        }
        """
        # public being dropped is NOT a security issue
        assert (
            is_security_protective_value("cache-control", ["public, max-age=3600"])
            is False
        )

    def test_comparison_table(self):
        """
        Comparison: MegaManSec's approach vs Our approach

        | Scenario                        | His PR  | Our Solution |
        |---------------------------------|---------|--------------|
        | Drop Cache-Control: no-store    | MEDIUM  | MEDIUM ✅    |
        | Drop Cache-Control: public      | MEDIUM  | LOW ✅       |
        | Drop Content-Disposition: att.  | N/A     | MEDIUM ✅    |
        """
        # His approach: blindly flag all Cache-Control as MEDIUM
        # Our approach: analyze the value

        # Security values → MEDIUM
        assert is_security_protective_value("cache-control", ["no-store"]) is True
        assert is_security_protective_value("cache-control", ["private"]) is True
        assert is_security_protective_value("cache-control", ["no-cache"]) is True

        # Performance values → LOW (not security protective)
        assert is_security_protective_value("cache-control", ["public"]) is False
        assert is_security_protective_value("cache-control", ["max-age=3600"]) is False

        # Bonus: We also handle Content-Disposition intelligently
        assert (
            is_security_protective_value("content-disposition", ["attachment"]) is True
        )
        assert is_security_protective_value("content-disposition", ["inline"]) is False
