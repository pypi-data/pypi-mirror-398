# SPDX-FileCopyrightText: 2025-present William Born <william.born.git@gmail.com>
#
# SPDX-License-Identifier: MIT
"""Tests for CoreDNS configuration functionality."""

from unittest.mock import patch

from localargo.config.manifest import (
    ClusterConfig,
    CoreDnsRewriteConfig,
    IngressConfig,
    UpManifest,
)
from localargo.core.checkers import check_coredns
from localargo.core.coredns import (
    LOCALARGO_MARKER_END,
    LOCALARGO_MARKER_START,
    _add_rewrite_rules,
    _remove_existing_rewrite_rules,
    check_coredns_rewrite_configured,
    configure_coredns_rewrite,
)

# =============================================================================
# Test manifest factory
# =============================================================================


def create_test_manifest(
    *,
    coredns_enabled: bool = True,
    coredns_domains: list[str] | None = None,
) -> UpManifest:
    """Create a test manifest with CoreDNS configuration."""
    if coredns_domains is None:
        coredns_domains = ["localtest.me"]

    return UpManifest(
        clusters=[ClusterConfig(name="test-cluster", provider="kind")],
        apps=[],
        repo_creds=[],
        secrets=[],
        ingress=IngressConfig(
            namespace="ingress-nginx",
            coredns_rewrite=CoreDnsRewriteConfig(
                enabled=coredns_enabled,
                domains=coredns_domains,
            ),
        ),
    )


# =============================================================================
# Sample Corefile for testing
# =============================================================================

SAMPLE_COREFILE = """.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}"""

SAMPLE_COREFILE_WITH_REWRITE = """.:53 {
    errors
    health {
       lameduck 5s
    }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
       max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
        # BEGIN localargo coredns rewrite
        rewrite name regex (.*)\\.localtest\\.me ingress-nginx-controller.ingress-nginx.svc.cluster.local answer auto
        # END localargo coredns rewrite
}"""


# =============================================================================
# CoreDNS rewrite rule tests
# =============================================================================


class TestAddRewriteRules:
    """Tests for adding rewrite rules to Corefile."""

    def test_add_single_domain_rewrite(self) -> None:
        """Test adding a single domain rewrite rule."""
        result = _add_rewrite_rules(
            SAMPLE_COREFILE,
            ["localtest.me"],
            "ingress-nginx-controller.ingress-nginx.svc.cluster.local",
        )

        assert LOCALARGO_MARKER_START in result
        assert LOCALARGO_MARKER_END in result
        assert "rewrite name regex" in result
        # Domain is escaped in the regex pattern
        assert r"localtest\.me" in result
        assert "ingress-nginx-controller.ingress-nginx.svc.cluster.local" in result

    def test_add_multiple_domain_rewrites(self) -> None:
        """Test adding multiple domain rewrite rules."""
        result = _add_rewrite_rules(
            SAMPLE_COREFILE,
            ["localtest.me", "nip.io"],
            "ingress-nginx-controller.ingress-nginx.svc.cluster.local",
        )

        assert result.count("rewrite name regex") == 2  # noqa: PLR2004
        # Domains are escaped in the regex patterns
        assert r"localtest\.me" in result
        assert r"nip\.io" in result

    def test_add_rewrite_preserves_existing_config(self) -> None:
        """Test that adding rewrite rules preserves existing configuration."""
        result = _add_rewrite_rules(
            SAMPLE_COREFILE,
            ["localtest.me"],
            "ingress-nginx-controller.ingress-nginx.svc.cluster.local",
        )

        # Check existing config is preserved
        assert "errors" in result
        assert "health" in result
        assert "kubernetes cluster.local" in result
        assert "prometheus :9153" in result
        assert "cache 30" in result

    def test_add_rewrite_replaces_existing_localargo_rules(self) -> None:
        """Test that adding rewrite rules replaces existing localargo rules."""
        # Start with a Corefile that already has localargo rules
        result = _add_rewrite_rules(
            SAMPLE_COREFILE_WITH_REWRITE,
            ["newdomain.me"],
            "ingress-nginx-controller.ingress-nginx.svc.cluster.local",
        )

        # Should only have one set of markers
        assert result.count(LOCALARGO_MARKER_START) == 1
        assert result.count(LOCALARGO_MARKER_END) == 1

        # Should have the new domain (escaped in regex)
        assert r"newdomain\.me" in result


class TestRemoveExistingRewriteRules:
    """Tests for removing existing rewrite rules."""

    def test_remove_existing_rules(self) -> None:
        """Test removing existing localargo rewrite rules."""
        result = _remove_existing_rewrite_rules(SAMPLE_COREFILE_WITH_REWRITE)

        assert LOCALARGO_MARKER_START not in result
        assert LOCALARGO_MARKER_END not in result
        assert "rewrite name regex" not in result

    def test_remove_preserves_other_config(self) -> None:
        """Test that removing rules preserves other configuration."""
        result = _remove_existing_rewrite_rules(SAMPLE_COREFILE_WITH_REWRITE)

        # Check existing config is preserved
        assert "errors" in result
        assert "health" in result
        assert "kubernetes cluster.local" in result

    def test_remove_from_corefile_without_rules(self) -> None:
        """Test removing from a Corefile without localargo rules."""
        result = _remove_existing_rewrite_rules(SAMPLE_COREFILE)

        # Should be unchanged (or nearly so, may have whitespace differences)
        assert "errors" in result
        assert LOCALARGO_MARKER_START not in result


# =============================================================================
# CoreDNS checker tests
# =============================================================================


class TestCheckCorednsRewriteConfigured:
    """Tests for checking if CoreDNS rewrite is configured."""

    def test_check_disabled_config(self) -> None:
        """Test check with disabled configuration."""
        config = CoreDnsRewriteConfig(enabled=False, domains=["localtest.me"])
        result = check_coredns_rewrite_configured(config)
        assert result is True  # Disabled means "configured" (nothing to do)

    def test_check_empty_domains(self) -> None:
        """Test check with no domains configured."""
        config = CoreDnsRewriteConfig(enabled=True, domains=[])
        result = check_coredns_rewrite_configured(config)
        assert result is True  # No domains means "configured" (nothing to do)

    def test_check_configured_corefile(self) -> None:
        """Test check when CoreDNS is properly configured."""
        config = CoreDnsRewriteConfig(enabled=True, domains=["localtest.me"])

        with patch("localargo.core.coredns._get_current_corefile") as mock_get:
            mock_get.return_value = SAMPLE_COREFILE_WITH_REWRITE
            result = check_coredns_rewrite_configured(config)

        assert result is True

    def test_check_unconfigured_corefile(self) -> None:
        """Test check when CoreDNS is not configured."""
        config = CoreDnsRewriteConfig(enabled=True, domains=["localtest.me"])

        with patch("localargo.core.coredns._get_current_corefile") as mock_get:
            mock_get.return_value = SAMPLE_COREFILE
            result = check_coredns_rewrite_configured(config)

        assert result is False

    def test_check_corefile_not_available(self) -> None:
        """Test check when CoreDNS ConfigMap cannot be retrieved."""
        config = CoreDnsRewriteConfig(enabled=True, domains=["localtest.me"])

        with patch("localargo.core.coredns._get_current_corefile") as mock_get:
            mock_get.return_value = None
            result = check_coredns_rewrite_configured(config)

        assert result is False


class TestCheckCorednsStep:
    """Tests for the check_coredns step function."""

    def test_check_coredns_disabled(self) -> None:
        """Test check when CoreDNS rewrite is disabled."""
        manifest = create_test_manifest(coredns_enabled=False)
        status = check_coredns(manifest)

        assert status.state == "skipped"
        assert "disabled" in status.reason

    def test_check_coredns_no_domains(self) -> None:
        """Test check when no domains are configured."""
        manifest = create_test_manifest(coredns_domains=[])
        status = check_coredns(manifest)

        assert status.state == "skipped"
        assert "No domains" in status.reason

    def test_check_coredns_configured(self) -> None:
        """Test check when CoreDNS is properly configured."""
        manifest = create_test_manifest()

        with patch("localargo.core.checkers.check_coredns_rewrite_configured") as mock_check:
            mock_check.return_value = True
            status = check_coredns(manifest)

        assert status.state == "completed"
        assert "configured" in status.reason.lower()

    def test_check_coredns_needs_configuration(self) -> None:
        """Test check when CoreDNS needs configuration."""
        manifest = create_test_manifest()

        with patch("localargo.core.checkers.check_coredns_rewrite_configured") as mock_check:
            mock_check.return_value = False
            status = check_coredns(manifest)

        assert status.state == "pending"
        assert "needs configuration" in status.reason

    def test_check_coredns_error_handling(self) -> None:
        """Test check error handling."""
        manifest = create_test_manifest()

        with patch("localargo.core.checkers.check_coredns_rewrite_configured") as mock_check:
            mock_check.side_effect = RuntimeError("kubectl failed")
            status = check_coredns(manifest)

        assert status.state == "pending"
        assert "Failed to check" in status.reason


# =============================================================================
# CoreDNS configure tests
# =============================================================================


class TestConfigureCorednsRewrite:
    """Tests for configure_coredns_rewrite function."""

    def test_configure_disabled(self) -> None:
        """Test that configuration is skipped when disabled."""
        config = CoreDnsRewriteConfig(enabled=False, domains=["localtest.me"])

        with patch("localargo.core.coredns._get_current_corefile") as mock_get:
            configure_coredns_rewrite(config, "ingress-nginx")
            mock_get.assert_not_called()

    def test_configure_no_domains(self) -> None:
        """Test that configuration is skipped when no domains."""
        config = CoreDnsRewriteConfig(enabled=True, domains=[])

        with patch("localargo.core.coredns._get_current_corefile") as mock_get:
            configure_coredns_rewrite(config, "ingress-nginx")
            mock_get.assert_not_called()

    def test_configure_already_configured(self) -> None:
        """Test that configuration is skipped when already configured."""
        config = CoreDnsRewriteConfig(enabled=True, domains=["localtest.me"])

        with (
            patch("localargo.core.coredns._get_current_corefile") as mock_get,
            patch("localargo.core.coredns._update_coredns_configmap") as mock_update,
        ):
            mock_get.return_value = SAMPLE_COREFILE_WITH_REWRITE
            configure_coredns_rewrite(config, "ingress-nginx")
            mock_update.assert_not_called()

    def test_configure_applies_rules(self) -> None:
        """Test that configuration applies rewrite rules."""
        config = CoreDnsRewriteConfig(enabled=True, domains=["localtest.me"])

        with (
            patch("localargo.core.coredns._get_current_corefile") as mock_get,
            patch("localargo.core.coredns._update_coredns_configmap") as mock_update,
            patch("localargo.core.coredns._restart_coredns") as mock_restart,
        ):
            mock_get.return_value = SAMPLE_COREFILE
            configure_coredns_rewrite(config, "ingress-nginx")

            mock_update.assert_called_once()
            mock_restart.assert_called_once()

            # Verify the new corefile content
            new_corefile = mock_update.call_args[0][0]
            assert LOCALARGO_MARKER_START in new_corefile
            # Domain is escaped in the regex
            assert r"localtest\.me" in new_corefile

    def test_configure_handles_corefile_not_found(self) -> None:
        """Test that configuration handles missing CoreDNS ConfigMap."""
        config = CoreDnsRewriteConfig(enabled=True, domains=["localtest.me"])

        with (
            patch("localargo.core.coredns._get_current_corefile") as mock_get,
            patch("localargo.core.coredns._update_coredns_configmap") as mock_update,
        ):
            mock_get.return_value = None
            configure_coredns_rewrite(config, "ingress-nginx")
            mock_update.assert_not_called()
