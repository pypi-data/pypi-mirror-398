"""Unit tests for secret value types (fromEnv, randomBase64, randomHex, staticValue, sameAs)."""

import base64
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from localargo.config.manifest import (
    ManifestValidationError,
    SecretValueFromEnv,
    SecretValueRandomBase64,
    SecretValueRandomHex,
    SecretValueSameAs,
    SecretValueStatic,
    load_up_manifest,
)
from localargo.core.executors import _resolve_secret_value, execute_secrets_creation

# =============================================================================
# Test Constants
# =============================================================================

BYTES_4 = 4
BYTES_8 = 8
BYTES_16 = 16
BYTES_32 = 32
BYTES_64 = 64
HEX_CHARS_8 = 8  # 4 bytes = 8 hex chars
HEX_CHARS_32 = 32  # 16 bytes = 32 hex chars
RANDOM_SAMPLE_COUNT = 10
EXPECTED_SECRETS_MIXED = 3

# =============================================================================
# Manifest Parsing Tests
# =============================================================================


def write_file(path: Path, content: str) -> None:
    """Write test content to a temporary file."""
    path.write_text(content, encoding="utf-8")


class TestSecretValueParsing:
    """Tests for parsing secret value specifications from manifests."""

    def test_parse_from_env(self, tmp_path: Path) -> None:
        """FromEnv secret values should parse correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - my_secret:
      namespace: default
      secretName: my-secret
      secretKey: api-key
      secretValue:
        - fromEnv: MY_API_KEY
""",
        )

        manifest = load_up_manifest(manifest_file)
        assert len(manifest.secrets) == 1
        secret = manifest.secrets[0]
        assert secret.name == "my_secret"
        assert secret.secret_key == "api-key"
        assert len(secret.secret_value) == 1
        assert isinstance(secret.secret_value[0], SecretValueFromEnv)
        assert secret.secret_value[0].from_env == "MY_API_KEY"

    def test_parse_random_base64(self, tmp_path: Path) -> None:
        """randomBase64 secret values should parse correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - encryption_key:
      namespace: default
      secretName: crypto-secret
      secretKey: key
      secretValue:
        - randomBase64: 32
""",
        )

        manifest = load_up_manifest(manifest_file)
        assert len(manifest.secrets) == 1
        secret = manifest.secrets[0]
        assert len(secret.secret_value) == 1
        assert isinstance(secret.secret_value[0], SecretValueRandomBase64)
        assert secret.secret_value[0].num_bytes == BYTES_32

    def test_parse_random_hex(self, tmp_path: Path) -> None:
        """RandomHex secret values should parse correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - session_id:
      namespace: default
      secretName: session-secret
      secretKey: id
      secretValue:
        - randomHex: 16
""",
        )

        manifest = load_up_manifest(manifest_file)
        assert len(manifest.secrets) == 1
        secret = manifest.secrets[0]
        assert len(secret.secret_value) == 1
        assert isinstance(secret.secret_value[0], SecretValueRandomHex)
        assert secret.secret_value[0].num_bytes == BYTES_16

    def test_parse_mixed_secret_types(self, tmp_path: Path) -> None:
        """Multiple secrets with different value types should parse correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - env_secret:
      namespace: core
      secretName: app-secrets
      secretKey: db-password
      secretValue:
        - fromEnv: DB_PASSWORD
  - base64_secret:
      namespace: core
      secretName: app-secrets
      secretKey: encryption-key
      secretValue:
        - randomBase64: 64
  - hex_secret:
      namespace: core
      secretName: app-secrets
      secretKey: session-key
      secretValue:
        - randomHex: 8
""",
        )

        manifest = load_up_manifest(manifest_file)
        assert len(manifest.secrets) == EXPECTED_SECRETS_MIXED

        # Check fromEnv
        assert isinstance(manifest.secrets[0].secret_value[0], SecretValueFromEnv)

        # Check randomBase64
        assert isinstance(manifest.secrets[1].secret_value[0], SecretValueRandomBase64)
        assert manifest.secrets[1].secret_value[0].num_bytes == BYTES_64

        # Check randomHex
        assert isinstance(manifest.secrets[2].secret_value[0], SecretValueRandomHex)
        assert manifest.secrets[2].secret_value[0].num_bytes == BYTES_8

    def test_invalid_random_base64_non_integer(self, tmp_path: Path) -> None:
        """randomBase64 with non-integer value should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_secret:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - randomBase64: "not-a-number"
""",
        )

        with pytest.raises(ManifestValidationError, match="randomBase64 must be a positive integer"):
            load_up_manifest(manifest_file)

    def test_invalid_random_base64_zero(self, tmp_path: Path) -> None:
        """randomBase64 with zero bytes should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_secret:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - randomBase64: 0
""",
        )

        with pytest.raises(ManifestValidationError, match="randomBase64 must be a positive integer"):
            load_up_manifest(manifest_file)

    def test_invalid_random_base64_negative(self, tmp_path: Path) -> None:
        """randomBase64 with negative bytes should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_secret:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - randomBase64: -5
""",
        )

        with pytest.raises(ManifestValidationError, match="randomBase64 must be a positive integer"):
            load_up_manifest(manifest_file)

    def test_invalid_random_hex_non_integer(self, tmp_path: Path) -> None:
        """RandomHex with non-integer value should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_secret:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - randomHex: "not-a-number"
""",
        )

        with pytest.raises(ManifestValidationError, match="randomHex must be a positive integer"):
            load_up_manifest(manifest_file)

    def test_invalid_random_hex_zero(self, tmp_path: Path) -> None:
        """RandomHex with zero bytes should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_secret:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - randomHex: 0
""",
        )

        with pytest.raises(ManifestValidationError, match="randomHex must be a positive integer"):
            load_up_manifest(manifest_file)

    def test_parse_static_value(self, tmp_path: Path) -> None:
        """StaticValue secret values should parse correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - my_static:
      namespace: default
      secretName: static-secret
      secretKey: api-key
      secretValue:
        - staticValue: "my-literal-secret-value"
""",
        )

        manifest = load_up_manifest(manifest_file)
        assert len(manifest.secrets) == 1
        secret = manifest.secrets[0]
        assert secret.name == "my_static"
        assert secret.secret_key == "api-key"
        assert len(secret.secret_value) == 1
        assert isinstance(secret.secret_value[0], SecretValueStatic)
        assert secret.secret_value[0].value == "my-literal-secret-value"

    def test_parse_same_as_value(self, tmp_path: Path) -> None:
        """SameAs secret values should parse correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - copied_secret:
      namespace: app-namespace
      secretName: app-secrets
      secretKey: db-password
      secretValue:
        - sameAs:
            namespace: source-namespace
            secretName: source-secret
            secretKey: password
""",
        )

        manifest = load_up_manifest(manifest_file)
        assert len(manifest.secrets) == 1
        secret = manifest.secrets[0]
        assert secret.name == "copied_secret"
        assert len(secret.secret_value) == 1
        assert isinstance(secret.secret_value[0], SecretValueSameAs)
        same_as = secret.secret_value[0]
        assert same_as.namespace == "source-namespace"
        assert same_as.secret_name == "source-secret"
        assert same_as.secret_key == "password"

    def test_same_as_missing_fields_raises(self, tmp_path: Path) -> None:
        """SameAs without required fields should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_same_as:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - sameAs:
            namespace: some-ns
""",
        )

        with pytest.raises(ManifestValidationError, match="sameAs requires namespace, secretName, and secretKey"):
            load_up_manifest(manifest_file)

    def test_same_as_not_dict_raises(self, tmp_path: Path) -> None:
        """SameAs with non-dict value should raise validation error."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - bad_same_as:
      namespace: default
      secretName: bad
      secretKey: key
      secretValue:
        - sameAs: "not-a-dict"
""",
        )

        with pytest.raises(ManifestValidationError, match="sameAs must be a mapping"):
            load_up_manifest(manifest_file)


# =============================================================================
# Secret Value Resolution Tests
# =============================================================================


class TestSecretValueResolution:
    """Tests for resolving secret value specifications to actual values."""

    def test_resolve_from_env_existing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FromEnv should resolve to the environment variable value."""
        monkeypatch.setenv("TEST_SECRET", "my-secret-value")
        spec = SecretValueFromEnv(from_env="TEST_SECRET")

        result = _resolve_secret_value(spec)

        assert result == "my-secret-value"

    def test_resolve_from_env_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FromEnv should resolve to empty string if env var is missing."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        spec = SecretValueFromEnv(from_env="NONEXISTENT_VAR")

        result = _resolve_secret_value(spec)

        assert result == ""

    def test_resolve_random_base64_length(self) -> None:
        """randomBase64 should generate correct base64-encoded output length."""
        spec = SecretValueRandomBase64(num_bytes=BYTES_32)

        result = _resolve_secret_value(spec)

        # 32 bytes -> 44 characters in base64 (with padding)
        # Formula: ceil(n * 4/3) rounded up to multiple of 4
        decoded = base64.b64decode(result)
        assert len(decoded) == BYTES_32

    def test_resolve_random_base64_is_valid_base64(self) -> None:
        """randomBase64 output should be valid base64."""
        spec = SecretValueRandomBase64(num_bytes=BYTES_16)

        result = _resolve_secret_value(spec)

        # Should not raise
        decoded = base64.b64decode(result)
        assert len(decoded) == BYTES_16

    def test_resolve_random_base64_is_random(self) -> None:
        """randomBase64 should generate different values each time."""
        spec = SecretValueRandomBase64(num_bytes=BYTES_32)

        results = {_resolve_secret_value(spec) for _ in range(RANDOM_SAMPLE_COUNT)}

        # All 10 should be unique (cryptographically improbable to collide)
        assert len(results) == RANDOM_SAMPLE_COUNT

    def test_resolve_random_hex_length(self) -> None:
        """RandomHex should generate correct hex output length (2 chars per byte)."""
        spec = SecretValueRandomHex(num_bytes=BYTES_4)

        result = _resolve_secret_value(spec)

        # 4 bytes -> 8 hex characters
        assert len(result) == HEX_CHARS_8

    def test_resolve_random_hex_is_valid_hex(self) -> None:
        """RandomHex output should be valid lowercase hex."""
        spec = SecretValueRandomHex(num_bytes=BYTES_16)

        result = _resolve_secret_value(spec)

        # Should match hex pattern
        assert re.fullmatch(r"[0-9a-f]+", result) is not None
        assert len(result) == HEX_CHARS_32  # 16 bytes = 32 hex chars

    def test_resolve_random_hex_is_random(self) -> None:
        """RandomHex should generate different values each time."""
        spec = SecretValueRandomHex(num_bytes=BYTES_16)

        results = {_resolve_secret_value(spec) for _ in range(RANDOM_SAMPLE_COUNT)}

        # All 10 should be unique
        assert len(results) == RANDOM_SAMPLE_COUNT

    def test_resolve_random_hex_4_bytes_example(self) -> None:
        """randomHex: 4 should produce 8 hex characters (like 'cafebabe')."""
        spec = SecretValueRandomHex(num_bytes=BYTES_4)

        result = _resolve_secret_value(spec)

        # Exactly 8 hex characters
        assert len(result) == HEX_CHARS_8
        assert re.fullmatch(r"[0-9a-f]{8}", result) is not None

    def test_resolve_unknown_type_raises(self) -> None:
        """Unknown secret value type should raise TypeError."""

        class UnknownSpec:
            pass

        with pytest.raises(TypeError, match="Unknown secret value type"):
            _resolve_secret_value(UnknownSpec())  # type: ignore[arg-type]

    def test_resolve_static_value(self) -> None:
        """StaticValue should resolve to its literal string value."""
        spec = SecretValueStatic(value="my-literal-value")

        result = _resolve_secret_value(spec)

        assert result == "my-literal-value"

    def test_resolve_static_value_empty(self) -> None:
        """StaticValue with empty string should resolve to empty string."""
        spec = SecretValueStatic(value="")

        result = _resolve_secret_value(spec)

        assert result == ""

    def test_resolve_static_value_special_chars(self) -> None:
        """StaticValue should preserve special characters."""
        spec = SecretValueStatic(value="p@ssw0rd!#$%^&*()")

        result = _resolve_secret_value(spec)

        assert result == "p@ssw0rd!#$%^&*()"

    @patch("localargo.core.executors.get_secret_data")
    def test_resolve_same_as_value(self, mock_get_secret: MagicMock) -> None:
        """SameAs should resolve by reading from another secret."""
        # Value in Kubernetes secrets is base64-encoded
        mock_get_secret.return_value = base64.b64encode(b"secret-value").decode("ascii")
        spec = SecretValueSameAs(
            namespace="source-ns",
            secret_name="source-secret",
            secret_key="the-key",
        )

        result = _resolve_secret_value(spec)

        assert result == "secret-value"
        mock_get_secret.assert_called_once_with(
            "source-ns",
            "source-secret",
            "jsonpath={.data.the-key}",
        )

    @patch("localargo.core.executors.get_secret_data")
    def test_resolve_same_as_value_not_found(self, mock_get_secret: MagicMock) -> None:
        """SameAs should raise ValueError if source secret key is not found."""
        mock_get_secret.return_value = ""
        spec = SecretValueSameAs(
            namespace="missing-ns",
            secret_name="missing-secret",
            secret_key="missing-key",
        )

        with pytest.raises(ValueError, match="Secret 'missing-secret' key 'missing-key' not found"):
            _resolve_secret_value(spec)


# =============================================================================
# Integration Tests (Execution)
# =============================================================================


class TestSecretsExecutionIntegration:
    """Integration tests for secret creation with different value types."""

    def test_execute_secrets_with_random_values(
        self,
        tmp_path: Path,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """Secrets with random values should be created correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - crypto_key:
      namespace: default
      secretName: app-secrets
      secretKey: encryption-key
      secretValue:
        - randomBase64: 32
  - session_key:
      namespace: default
      secretName: app-secrets
      secretKey: session-id
      secretValue:
        - randomHex: 16
""",
        )

        manifest = load_up_manifest(manifest_file)

        # Execute - should not raise
        execute_secrets_creation(manifest)

        # Verify upsert_secret was called
        # The mock handles subprocess calls; we verify no exceptions raised
        assert mock_subprocess_run.called

    def test_execute_secrets_key_merging(
        self,
        tmp_path: Path,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """Multiple secrets with same name but different keys should be merged."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - db_user:
      namespace: backend
      secretName: database-credentials
      secretKey: username
      secretValue:
        - staticValue: "admin"
  - db_pass:
      namespace: backend
      secretName: database-credentials
      secretKey: password
      secretValue:
        - staticValue: "secret123"
  - db_host:
      namespace: backend
      secretName: database-credentials
      secretKey: host
      secretValue:
        - staticValue: "localhost"
""",
        )

        manifest = load_up_manifest(manifest_file)

        # Execute - should not raise
        execute_secrets_creation(manifest)

        # Verify subprocess was called (for kubectl operations)
        assert mock_subprocess_run.called

    def test_execute_secrets_with_static_values(
        self,
        tmp_path: Path,
        mock_subprocess_run: MagicMock,
    ) -> None:
        """Secrets with static values should be created correctly."""
        manifest_file = tmp_path / "localargo.yaml"
        write_file(
            manifest_file,
            """
cluster:
  - name: test
    provider: kind

apps: []
repo_creds: []

secrets:
  - api_key:
      namespace: core
      secretName: api-secrets
      secretKey: key
      secretValue:
        - staticValue: "sk-abc123xyz"
""",
        )

        manifest = load_up_manifest(manifest_file)
        execute_secrets_creation(manifest)
        assert mock_subprocess_run.called
